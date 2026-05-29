#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Builder_HarmonyOS_patch.py
==========================
Patch MINIMAL à appliquer sur le Builder.py ORIGINAL.

Ne modifie QUE les lignes nécessaires pour le support .ts/.ets.
Toutes les docstrings, commentaires, logs et code existants sont PRÉSERVÉS.

Application :
    python3 Builder_HarmonyOS_patch.py path/to/Builder.py

Le script crée Builder.py.bak avant de modifier.
"""

import sys
import shutil
from pathlib import Path


# =============================================================================
# CHANGEMENT 1 — Ajouter les constantes après les imports (début du fichier)
# =============================================================================
#
# Insérer APRÈS la ligne :
#   from .Platform import Platform
#
# Le bloc à insérer :

INSERT_AFTER_IMPORTS = '''

# ---------------------------------------------------------------------------
# Extensions platform-spécifiques — gérées par des builders dédiés,
# PAS par le compilateur natif C/C++.
#
# Ces extensions peuvent être déclarées dans files() du .jenga exactement
# comme .mm pour Cocoa — le builder natif les ignore, les builders platform
# les collectent via GetPlatformSpecificFiles().
# ---------------------------------------------------------------------------

# Extensions compilables par le compilateur natif C/C++/ObjC/ASM
NATIVE_COMPILABLE_EXTENSIONS = {
    '.c',
    '.cpp', '.cc', '.cxx', '.c++',
    '.cppm', '.ixx', '.mpp', '.c++m',   # C++20 modules
    '.m',                                 # Objective-C
    '.mm',                                # Objective-C++
    '.s', '.asm', '.S',                   # Assembleur
    '.rs',                                # Rust
    '.zig',                               # Zig
}

# Extensions gérées par des builders platform-spécifiques.
# Déclarables dans files() mais jamais passées à Compile().
#
#   .ts / .ets  → HarmonyOsBuilder : copiés dans entry/src/main/ets/
#   .swift      → XcodeBuilder     : compilé par swiftc (futur)
#   .kt / .java → AndroidBuilder   : compilé par javac + d8
#   .hlsl/.glsl → ShaderBuilder    : compilé par shader compiler (futur)
#   .metal      → XcodeBuilder     : compilé par Metal (futur)
PLATFORM_SPECIFIC_EXTENSIONS = {
    '.ts':    'harmonyos',
    '.ets':   'harmonyos',
    '.swift': 'xcode',
    '.kt':    'android',
    '.java':  'android',
    '.hlsl':  'shader',
    '.glsl':  'shader',
    '.metal': 'xcode',
}
'''

# =============================================================================
# CHANGEMENT 2 — Ajouter HarmonyOS dans _ResolveToolchain
# =============================================================================
#
# Dans _ResolveToolchain, le bloc elif pour les plateformes se termine par :
#   elif self.targetOs == TargetOS.WEB:
#       prefer = ['emscripten', 'zig-web-wasm32']
#
# Ajouter APRÈS ce bloc :

INSERT_AFTER_WEB_TOOLCHAIN = '''        elif self.targetOs == TargetOS.HARMONYOS:
            prefer = ['ohos-ndk']'''

# =============================================================================
# CHANGEMENT 3 — 3 nouvelles méthodes statiques + GetPlatformSpecificFiles
# =============================================================================
#
# Ajouter AVANT la méthode GetSharedLibExtensions (ou après PreparePCH).
# Ces méthodes constituent l'API pour les builders platform.

NEW_METHODS = '''
    # -----------------------------------------------------------------------
    # API pour les fichiers platform-spécifiques (.ts/.ets/.swift/.java...)
    # -----------------------------------------------------------------------

    @staticmethod
    def IsPlatformSpecificFile(sourceFile: str) -> bool:
        """
        Retourne True si le fichier est géré par un builder platform-spécifique
        et NE DOIT PAS être compilé par le compilateur natif C/C++.

        Fichiers reconnus :
          .ts / .ets  → HarmonyOS ArkTS (copié dans HAP par HarmonyOsBuilder)
          .swift      → Swift (XcodeBuilder)
          .kt / .java → Kotlin/Java (AndroidBuilder)
          .hlsl/.glsl → Shaders (ShaderBuilder)
          .metal      → Metal (XcodeBuilder)
        """
        return Path(sourceFile).suffix.lower() in PLATFORM_SPECIFIC_EXTENSIONS

    @staticmethod
    def IsNativeCompilable(sourceFile: str) -> bool:
        """
        Retourne True si le fichier est compilable par le compilateur natif.
        Exclut les fichiers platform-spécifiques (.ts, .ets, .swift, etc.).
        """
        ext = Path(sourceFile).suffix.lower()
        return ext in NATIVE_COMPILABLE_EXTENSIONS and ext not in PLATFORM_SPECIFIC_EXTENSIONS

    def GetPlatformSpecificFiles(self, project: Project,
                                  extensions: Optional[List[str]] = None) -> List[str]:
        """
        Retourne les fichiers platform-spécifiques déclarés dans files() du projet.

        C'est la méthode que les builders platform utilisent pour récupérer
        leurs fichiers depuis files() — même logique que .mm pour Cocoa.

        Usage dans HarmonyOsBuilder :
          arkts = self.GetPlatformSpecificFiles(project, ['.ts', '.ets'])
          # → ["harmony/ets/NkHarmonyBridge.ts", "harmony/ets/EntryAbility.ets"]

        Usage dans AndroidBuilder :
          java_files = self.GetPlatformSpecificFiles(project, ['.java', '.kt'])

        Args:
          project    : projet à analyser
          extensions : liste d'extensions à filtrer (None = toutes les platform-spécifiques)
        """
        if extensions is None:
            target_exts = set(PLATFORM_SPECIFIC_EXTENSIONS.keys())
        else:
            target_exts = {e.lower() for e in extensions}

        result = []
        all_files = self._CollectAllDeclaredFiles(project)
        for f in all_files:
            p = Path(f)
            if p.suffix.lower() in target_exts and p.exists():
                result.append(str(p))
        return result

    def _CollectAllDeclaredFiles(self, project: Project) -> List[str]:
        """
        Résout TOUS les fichiers déclarés dans files() du projet, quelle que soit
        leur extension. Utilisé pour extraire les fichiers platform-spécifiques.

        Contrairement à _CollectSourceFiles(), ne filtre PAS par extension —
        retourne tout ce que files() et les filtres actifs déclarent.
        """
        result = []
        workspace_base = Path(self.workspace.location).resolve() \\
            if self.workspace and self.workspace.location else Path.cwd()

        if project.location:
            base_dir_str = project.location
            if self._expander:
                self._expander.SetProject(project)
                base_dir_str = self._expander.Expand(base_dir_str, recursive=True)
            base_dir_path = Path(base_dir_str)
            if not base_dir_path.is_absolute():
                base_dir_path = workspace_base / base_dir_path
            base_dir = base_dir_path.resolve()
        else:
            base_dir = workspace_base

        # Patterns depuis files() + filtres actifs
        all_patterns = list(project.files)
        for filter_name, ffiles in getattr(project, '_filteredFiles', {}).items():
            if self._FilterMatches(filter_name, project):
                all_patterns.extend(ffiles)

        for pattern in all_patterns:
            expanded = pattern
            if self._expander:
                self._expander.SetProject(project)
                expanded = self._expander.Expand(pattern, recursive=True)
            p = Path(expanded)
            if p.is_absolute():
                if any(ch in expanded for ch in ('*', '?', '[')):
                    result.extend(m for m in glob.glob(expanded, recursive=True)
                                  if Path(m).is_file())
                elif p.exists():
                    result.append(str(p))
            else:
                matched = FileSystem.ListFiles(base_dir, pattern=expanded,
                                               recursive=True, fullPath=True)
                result.extend(matched)

        return result

'''

# =============================================================================
# CHANGEMENT 4 — Exclure .ts/.ets dans _CollectSourceFiles
# =============================================================================
#
# Dans _CollectSourceFiles, DANS la boucle "for f in matched:", avant le check
# d'extension, ajouter l'exclusion des fichiers platform-spécifiques.
#
# Trouver le bloc :
#   for f in matched:
#       if any(f.lower().endswith(ext) for ext in src_exts):
#           files.append(f)
#
# Le remplacer par :
OLD_COLLECT_LOOP = '''            for f in matched:
                if any(f.lower().endswith(ext) for ext in src_exts):
                    files.append(f)'''

NEW_COLLECT_LOOP = '''            for f in matched:
                # Exclure silencieusement les fichiers platform-spécifiques
                # (.ts, .ets, .swift, .java, .kt...) — ils sont gérés par
                # GetPlatformSpecificFiles() dans les builders platform.
                # Même logique que .mm pour Cocoa : déclaré dans files(),
                # ignoré par le compilateur natif si le builder ne le supporte pas.
                if Path(f).suffix.lower() in PLATFORM_SPECIFIC_EXTENSIONS:
                    continue
                if any(f.lower().endswith(ext) for ext in src_exts):
                    files.append(f)'''

# =============================================================================
# Application du patch
# =============================================================================

def apply_patch(builder_path: str) -> bool:
    path = Path(builder_path)
    if not path.exists():
        print(f"❌ Fichier introuvable : {builder_path}")
        return False

    # Backup
    backup = path.with_suffix('.py.bak')
    shutil.copy2(path, backup)
    print(f"✓ Backup créé : {backup}")

    content = path.read_text(encoding='utf-8')
    original_len = len(content.splitlines())

    # ── Changement 1 : constantes après imports ───────────────────────────────
    ANCHOR_IMPORTS = 'from .Platform import Platform'
    if ANCHOR_IMPORTS not in content:
        print(f"❌ Anchor 1 introuvable : '{ANCHOR_IMPORTS}'")
        return False
    if 'PLATFORM_SPECIFIC_EXTENSIONS' in content:
        print("⚠️  Changement 1 déjà appliqué (PLATFORM_SPECIFIC_EXTENSIONS présent)")
    else:
        # Insérer après la ligne anchor (après le \n)
        idx = content.find(ANCHOR_IMPORTS) + len(ANCHOR_IMPORTS)
        # Trouver la fin de la ligne
        eol = content.find('\n', idx)
        content = content[:eol+1] + INSERT_AFTER_IMPORTS + content[eol+1:]
        print("✓ Changement 1 appliqué : constantes PLATFORM_SPECIFIC_EXTENSIONS")

    # ── Changement 2 : HarmonyOS dans _ResolveToolchain ─────────────────────
    ANCHOR_WEB = "prefer = ['emscripten', 'zig-web-wasm32']"
    if ANCHOR_WEB not in content:
        print(f"⚠️  Anchor 2 introuvable (format peut différer) : '{ANCHOR_WEB}'")
        print("   Ajouter manuellement dans _ResolveToolchain après le bloc WEB :")
        print("   elif self.targetOs == TargetOS.HARMONYOS:")
        print("       prefer = ['ohos-ndk']")
    elif 'TargetOS.HARMONYOS' in content and 'ohos-ndk' in content:
        print("⚠️  Changement 2 déjà appliqué (HARMONYOS toolchain présent)")
    else:
        idx = content.find(ANCHOR_WEB) + len(ANCHOR_WEB)
        eol = content.find('\n', idx)
        content = content[:eol+1] + INSERT_AFTER_WEB_TOOLCHAIN + '\n' + content[eol+1:]
        print("✓ Changement 2 appliqué : HarmonyOS dans _ResolveToolchain")

    # ── Changement 3 : nouvelles méthodes ────────────────────────────────────
    ANCHOR_METHODS = 'def GetSharedLibExtensions(self)'
    if ANCHOR_METHODS not in content:
        print(f"⚠️  Anchor 3 introuvable : '{ANCHOR_METHODS}'")
        print("   Ajouter manuellement les méthodes IsPlatformSpecificFile,")
        print("   IsNativeCompilable, GetPlatformSpecificFiles, _CollectAllDeclaredFiles")
    elif '_CollectAllDeclaredFiles' in content:
        print("⚠️  Changement 3 déjà appliqué (_CollectAllDeclaredFiles présent)")
    else:
        idx = content.find('    ' + ANCHOR_METHODS)
        content = content[:idx] + NEW_METHODS + content[idx:]
        print("✓ Changement 3 appliqué : 4 nouvelles méthodes platform-spécifiques")

    # ── Changement 4 : exclure .ts/.ets dans _CollectSourceFiles ─────────────
    if OLD_COLLECT_LOOP not in content:
        print(f"⚠️  Anchor 4 introuvable (indentation peut différer)")
        print("   Dans _CollectSourceFiles, dans la boucle 'for f in matched:',")
        print("   ajouter AVANT le check d'extension :")
        print("     if Path(f).suffix.lower() in PLATFORM_SPECIFIC_EXTENSIONS:")
        print("         continue")
    elif 'PLATFORM_SPECIFIC_EXTENSIONS' in content.split(OLD_COLLECT_LOOP)[1][:200]:
        print("⚠️  Changement 4 déjà appliqué")
    else:
        content = content.replace(OLD_COLLECT_LOOP, NEW_COLLECT_LOOP, 1)
        print("✓ Changement 4 appliqué : exclusion .ts/.ets dans _CollectSourceFiles")

    # ── Écriture ──────────────────────────────────────────────────────────────
    path.write_text(content, encoding='utf-8')
    new_len = len(content.splitlines())
    print(f"\n✅ Patch appliqué avec succès")
    print(f"   Avant : {original_len} lignes")
    print(f"   Après : {new_len} lignes (+{new_len - original_len} lignes ajoutées)")

    # Vérification syntaxe Python
    import ast
    try:
        ast.parse(content)
        print("   Syntaxe Python : OK")
    except SyntaxError as e:
        print(f"   ⚠️  Erreur de syntaxe : {e}")
        print(f"   Restaurer depuis le backup : cp {backup} {path}")
        return False

    return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 Builder_HarmonyOS_patch.py path/to/Builder.py")
        print()
        print("Ce script applique le patch HarmonyOS minimal sur Builder.py.")
        print("Il préserve TOUT le contenu original (docstrings, commentaires,")
        print("logs, code commenté) et ajoute seulement les 4 changements nécessaires.")
        sys.exit(1)

    success = apply_patch(sys.argv[1])
    sys.exit(0 if success else 1)