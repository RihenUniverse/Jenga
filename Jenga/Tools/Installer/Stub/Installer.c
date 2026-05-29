/*
 * Jenga Installer — stub self-extracting multi-plateforme.
 *
 * Ce binaire est compile par Jenga puis se voit accoler un PAYLOAD
 * (manifeste + archive) suivi d'un TRAILER de 48 octets. A l'execution, le
 * stub se lit lui-meme, extrait les fichiers vers le dossier d'installation,
 * configure le pare-feu et ecrit un desinstalleur.
 *
 * Format : voir Jenga/Tools/Installer/DESIGN.md.
 * Edite par Rihen — fait partie de Jenga.
 *
 * Nomenclature : fonctions/types en PascalCase, variables locales en camelCase,
 * constantes/macros en UPPER_SNAKE_CASE.
 *
 * C99 portable. Specificites OS isolees par #ifdef (_WIN32 / __APPLE__ / autre).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <ctype.h>

#ifdef _WIN32
  #include <windows.h>
  #include <direct.h>
  #define PATH_SEP '\\'
  #define MKDIR(p) _mkdir(p)
#else
  #include <unistd.h>
  #include <sys/stat.h>
  #include <sys/types.h>
  #include <errno.h>
  #define PATH_SEP '/'
  #define MKDIR(p) mkdir((p), 0755)
  #ifdef __APPLE__
    #include <mach-o/dyld.h>
  #endif
#endif

#define TRAILER_MAGIC "JNGINST1"
#define TRAILER_SIZE  48
#define PATH_MAX_LEN  4096

/* ----------------------------------------------------------------------- */
/* Lecture little-endian portable                                          */
/* ----------------------------------------------------------------------- */
static uint64_t RdU64(const unsigned char *p) {
    uint64_t value = 0;
    for (int i = 7; i >= 0; --i) value = (value << 8) | p[i];
    return value;
}
static uint32_t RdU32(const unsigned char *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

/* ----------------------------------------------------------------------- */
/* Chemin du binaire courant                                               */
/* ----------------------------------------------------------------------- */
static int GetSelfPath(char *buf, size_t n) {
#ifdef _WIN32
    DWORD r = GetModuleFileNameA(NULL, buf, (DWORD)n);
    return (r > 0 && r < n) ? 0 : -1;
#elif defined(__APPLE__)
    uint32_t sz = (uint32_t)n;
    return _NSGetExecutablePath(buf, &sz) == 0 ? 0 : -1;
#else
    ssize_t r = readlink("/proc/self/exe", buf, n - 1);
    if (r <= 0) return -1;
    buf[r] = '\0';
    return 0;
#endif
}

/* ----------------------------------------------------------------------- */
/* Creation recursive de dossiers (mkdir -p)                               */
/* ----------------------------------------------------------------------- */
static void MkdirP(const char *path) {
    char tmp[PATH_MAX_LEN];
    size_t len = strlen(path);
    if (len == 0 || len >= sizeof(tmp)) return;
    strcpy(tmp, path);
    for (size_t i = 1; i < len; ++i) {
        if (tmp[i] == '/' || tmp[i] == '\\') {
            char c = tmp[i];
            tmp[i] = '\0';
            MKDIR(tmp);
            tmp[i] = c;
        }
    }
    MKDIR(tmp);
}

/* Normalise les separateurs vers ceux de l'OS. */
static void ToNativeSep(char *s) {
    for (; *s; ++s)
        if (*s == '/' || *s == '\\') *s = PATH_SEP;
}

/* ----------------------------------------------------------------------- */
/* Manifeste : recherche d'une cle "cle=valeur" (1er match).               */
/* ----------------------------------------------------------------------- */
static int ManifestGet(const char *manifest, const char *key, char *out, size_t n) {
    size_t keyLen = strlen(key);
    const char *cursor = manifest;
    while (*cursor) {
        const char *line = cursor;
        const char *eol = strchr(cursor, '\n');
        size_t lineLen = eol ? (size_t)(eol - line) : strlen(line);
        if (lineLen > keyLen && strncmp(line, key, keyLen) == 0 && line[keyLen] == '=') {
            size_t valueLen = lineLen - keyLen - 1;
            if (valueLen >= n) valueLen = n - 1;
            memcpy(out, line + keyLen + 1, valueLen);
            out[valueLen] = '\0';
            if (valueLen > 0 && out[valueLen - 1] == '\r') out[valueLen - 1] = '\0';
            return 0;
        }
        if (!eol) break;
        cursor = eol + 1;
    }
    return -1;
}

/* Expansion basique des variables d'environnement dans un chemin. */
static void ExpandPath(const char *in, char *out, size_t n) {
#ifdef _WIN32
    ExpandEnvironmentStringsA(in, out, (DWORD)n);
#else
    out[0] = '\0';
    size_t outIdx = 0;
    for (size_t i = 0; in[i] && outIdx + 1 < n; ) {
        if (in[i] == '~' && i == 0) {
            const char *home = getenv("HOME");
            if (home) {
                size_t homeLen = strlen(home);
                if (outIdx + homeLen < n) { strcpy(out + outIdx, home); outIdx += homeLen; }
            }
            i++;
        } else if (in[i] == '$') {
            char varName[256];
            size_t varIdx = 0;
            i++;
            while (in[i] && (isalnum((unsigned char)in[i]) || in[i] == '_') && varIdx < 255)
                varName[varIdx++] = in[i++];
            varName[varIdx] = '\0';
            const char *value = getenv(varName);
            if (value) {
                size_t valueLen = strlen(value);
                if (outIdx + valueLen < n) { strcpy(out + outIdx, value); outIdx += valueLen; }
            }
        } else {
            out[outIdx++] = in[i++];
        }
    }
    out[outIdx] = '\0';
#endif
}

/* ----------------------------------------------------------------------- */
/* Extraction de l'archive : lit `entries` fichiers depuis fp (positionne  */
/* au debut de l'archive). Ecrit la liste des fichiers poses dans `listFp`. */
/* ----------------------------------------------------------------------- */
static int ExtractArchive(FILE *fp, uint64_t entries, const char *destDir,
                          FILE *listFp, int verbose) {
    char path[PATH_MAX_LEN], full[PATH_MAX_LEN];
    char *dataBuf = NULL;
    size_t dataBufCap = 0;

    for (uint64_t e = 0; e < entries; ++e) {
        unsigned char u32b[4], u64b[8];
        if (fread(u32b, 1, 4, fp) != 4) { free(dataBuf); return -1; }
        uint32_t pathLen = RdU32(u32b);
        if (pathLen == 0 || pathLen >= sizeof(path)) { free(dataBuf); return -1; }
        if (fread(path, 1, pathLen, fp) != pathLen) { free(dataBuf); return -1; }
        path[pathLen] = '\0';
        if (fread(u32b, 1, 4, fp) != 4) { free(dataBuf); return -1; }
        uint32_t mode = RdU32(u32b);
        if (fread(u64b, 1, 8, fp) != 8) { free(dataBuf); return -1; }
        uint64_t size = RdU64(u64b);

        snprintf(full, sizeof(full), "%s%c%s", destDir, PATH_SEP, path);
        ToNativeSep(full);

        /* creer le dossier parent */
        char parent[PATH_MAX_LEN];
        strcpy(parent, full);
        for (int i = (int)strlen(parent) - 1; i >= 0; --i) {
            if (parent[i] == PATH_SEP) { parent[i] = '\0'; break; }
        }
        MkdirP(parent);

        FILE *out = fopen(full, "wb");
        if (!out) { fprintf(stderr, "  [ERREUR] ecriture %s\n", full); free(dataBuf); return -1; }
        if (size > dataBufCap) {
            char *grown = (char *)realloc(dataBuf, (size_t)size);
            if (!grown) { fclose(out); free(dataBuf); return -1; }
            dataBuf = grown; dataBufCap = (size_t)size;
        }
        if (size > 0) {
            if (fread(dataBuf, 1, (size_t)size, fp) != size) { fclose(out); free(dataBuf); return -1; }
            fwrite(dataBuf, 1, (size_t)size, out);
        }
        fclose(out);

#ifndef _WIN32
        if (mode != 0) chmod(full, (mode_t)mode);
#else
        (void)mode;
#endif
        if (listFp) fprintf(listFp, "%s\n", path);
        if (verbose) printf("  + %s\n", path);
    }
    free(dataBuf);
    return 0;
}

/* ----------------------------------------------------------------------- */
/* Ecrit un desinstalleur simple (script) dans le dossier d'install.       */
/* ----------------------------------------------------------------------- */
static void WriteUninstaller(const char *destDir, const char *fwDel) {
    char path[PATH_MAX_LEN];
#ifdef _WIN32
    snprintf(path, sizeof(path), "%s%cuninstall.bat", destDir, PATH_SEP);
    FILE *u = fopen(path, "wb");
    if (!u) return;
    fprintf(u, "@echo off\r\n");
    fprintf(u, "REM Desinstalleur genere par Jenga Installer\r\n");
    if (fwDel && fwDel[0]) fprintf(u, "%s >nul 2>&1\r\n", fwDel);
    fprintf(u, "for /f \"usebackq delims=\" %%%%F in (\"%s%cuninstall.files\") do del /f /q \"%s%c%%%%F\" >nul 2>&1\r\n",
            destDir, PATH_SEP, destDir, PATH_SEP);
    fprintf(u, "echo Desinstalle.\r\n");
    fclose(u);
#else
    snprintf(path, sizeof(path), "%s%cuninstall.sh", destDir, PATH_SEP);
    FILE *u = fopen(path, "wb");
    if (!u) return;
    fprintf(u, "#!/bin/sh\n# Desinstalleur genere par Jenga Installer\n");
    if (fwDel && fwDel[0]) fprintf(u, "%s >/dev/null 2>&1 || true\n", fwDel);
    fprintf(u, "DIR=\"$(cd \"$(dirname \"$0\")\" && pwd)\"\n");
    fprintf(u, "while IFS= read -r f; do rm -f \"$DIR/$f\"; done < \"$DIR/uninstall.files\"\n");
    fprintf(u, "echo Desinstalle.\n");
    fclose(u);
    chmod(path, 0755);
#endif
}

/* ----------------------------------------------------------------------- */
/* Point d'entree                                                           */
/* ----------------------------------------------------------------------- */
int main(int argc, char **argv) {
    const char *optDir = NULL;
    int silent = 0;
    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--dir") == 0 && i + 1 < argc) optDir = argv[++i];
        else if (strcmp(argv[i], "--silent") == 0) silent = 1;
        else if (strcmp(argv[i], "--help") == 0) {
            printf("Jenga Installer\n  --dir <chemin>  dossier d'installation\n"
                   "  --silent        sans interaction\n  --help          aide\n");
            return 0;
        }
    }

    /* 1. self path + ouverture */
    char selfPath[PATH_MAX_LEN];
    if (GetSelfPath(selfPath, sizeof(selfPath)) != 0) { fprintf(stderr, "self path KO\n"); return 1; }
    FILE *fp = fopen(selfPath, "rb");
    if (!fp) { fprintf(stderr, "ouverture self KO\n"); return 1; }

    /* 2. trailer (48 derniers octets) */
    if (fseek(fp, -TRAILER_SIZE, SEEK_END) != 0) { fclose(fp); return 1; }
    unsigned char trailer[TRAILER_SIZE];
    if (fread(trailer, 1, TRAILER_SIZE, fp) != TRAILER_SIZE) { fclose(fp); return 1; }
    if (memcmp(trailer, TRAILER_MAGIC, 8) != 0) {
        fprintf(stderr, "Aucun payload trouve (binaire stub nu ?).\n");
        fclose(fp); return 1;
    }
    uint64_t manifestOff = RdU64(trailer + 8);
    uint64_t manifestSz  = RdU64(trailer + 16);
    uint64_t archiveOff  = RdU64(trailer + 24);
    uint64_t archiveEnt  = RdU64(trailer + 32);

    /* 3. manifeste */
    char *manifest = (char *)malloc((size_t)manifestSz + 1);
    if (!manifest) { fclose(fp); return 1; }
    fseek(fp, (long)manifestOff, SEEK_SET);
    if (fread(manifest, 1, (size_t)manifestSz, fp) != manifestSz) { free(manifest); fclose(fp); return 1; }
    manifest[manifestSz] = '\0';

    char name[256] = "App", version[64] = "", publisher[256] = "Rihen";
    ManifestGet(manifest, "name", name, sizeof(name));
    ManifestGet(manifest, "version", version, sizeof(version));
    ManifestGet(manifest, "publisher", publisher, sizeof(publisher));

    /* 4. dossier d'install */
    char destDir[PATH_MAX_LEN];
    if (optDir) {
        strncpy(destDir, optDir, sizeof(destDir) - 1);
        destDir[sizeof(destDir) - 1] = '\0';
    } else {
        char key[64], raw[PATH_MAX_LEN] = "";
#ifdef _WIN32
        strcpy(key, "default_dir_windows");
#elif defined(__APPLE__)
        strcpy(key, "default_dir_macos");
#else
        strcpy(key, "default_dir_linux");
#endif
        if (ManifestGet(manifest, key, raw, sizeof(raw)) != 0)
            snprintf(raw, sizeof(raw), "%s", name);
        ExpandPath(raw, destDir, sizeof(destDir));
    }
    ToNativeSep(destDir);

    printf("=== Installation de %s %s (editeur : %s) ===\n", name, version, publisher);
    printf("Dossier cible : %s\n", destDir);
    if (!silent) {
        printf("Continuer ? [O/n] ");
        fflush(stdout);
        int c = getchar();
        if (c == 'n' || c == 'N') { printf("Annule.\n"); free(manifest); fclose(fp); return 0; }
    }

    MkdirP(destDir);

    /* liste des fichiers installes (pour le desinstalleur) */
    char listPath[PATH_MAX_LEN];
    snprintf(listPath, sizeof(listPath), "%s%cuninstall.files", destDir, PATH_SEP);
    FILE *listFp = fopen(listPath, "wb");

    /* 5. extraction */
    fseek(fp, (long)archiveOff, SEEK_SET);
    int rc = ExtractArchive(fp, archiveEnt, destDir, listFp, !silent);
    if (listFp) fclose(listFp);
    fclose(fp);
    if (rc != 0) { fprintf(stderr, "Extraction echouee.\n"); free(manifest); return 1; }

    /* 6. pare-feu : execute la commande 'add' du manifeste si presente */
    char fwAdd[2048] = "", fwDel[2048] = "";
    ManifestGet(manifest, "firewall_add", fwAdd, sizeof(fwAdd));
    ManifestGet(manifest, "firewall_del", fwDel, sizeof(fwDel));
    if (fwAdd[0]) {
        if (!silent) printf("Configuration du pare-feu...\n");
        system(fwAdd);
    }

    /* 7. desinstalleur */
    WriteUninstaller(destDir, fwDel);

    free(manifest);
    printf("Installation terminee dans : %s\n", destDir);
    return 0;
}
