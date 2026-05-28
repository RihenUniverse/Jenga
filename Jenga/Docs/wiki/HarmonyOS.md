# HarmonyOS / OpenHarmony

**Langues / Languages :** [Français](#français) · [English](#english)

---

## Français

Jenga compile, package et signe des applications **HarmonyOS** (HAP) à partir de
sources C/C++ natives, avec génération automatique de la structure de projet
ArkTS attendue par `hvigor`.

> **Statut :** ✅ Intégré — builder complet, packaging HAP, permissions réseau.
> Testable depuis Windows, Linux et macOS (le SDK OpenHarmony est cross-platform).

---

## 1. Prérequis

| Outil | Détail | Variable d'environnement |
|-------|--------|--------------------------|
| SDK OpenHarmony / HarmonyOS | Contient le NDK natif (LLVM) + `hvigorw` | `OHOS_SDK`, `HARMONY_OS_SDK` ou `HARMONY_SDK` |
| DevEco Studio (optionnel) | Fournit le template officiel + `hvigor` | détecté automatiquement |
| Node.js | Requis par `hvigorw` pour assembler le `.hap` | dans le PATH |

```bash
# Windows
set HARMONY_OS_SDK=C:\Users\%USERNAME%\AppData\Local\OpenHarmony\Sdk

# Linux / macOS
export OHOS_SDK=$HOME/OpenHarmony/Sdk
```

Le builder résout automatiquement le NDK dans
`<sdk>/default/openharmony/native/` et détecte `clang`, `llvm-ar`, `llvm-strip`.

---

## 2. Plateforme et architectures

| TargetOS | Architectures | Triples cibles |
|----------|---------------|----------------|
| `TargetOS.HARMONYOS` | `ARM` (armv7a), `ARM64` (aarch64), `X86_64` | `aarch64-linux-ohos`, `arm-linux-ohos`, `x86_64-linux-ohos` |

---

## 3. Exemple minimal

```python
# harmony_app.jenga
from Jenga import *
from Jenga.GlobalToolchains import RegisterJengaGlobalToolchains

with workspace("HarmonyDemo"):
    RegisterJengaGlobalToolchains()
    configurations(["Debug", "Release"])
    targetoses([TargetOS.HARMONYOS])
    targetarchs([TargetArch.ARM64])

    harmonysdk(os.getenv("HARMONY_OS_SDK", ""))   # workspace-level

    with project("MyApp"):
        windowedapp()                  # -> génère un .hap (sinon .so/.a/ELF)
        language("C++")
        cppdialect("C++17")
        files(["src/**.cpp"])

        # Métadonnées HAP
        harmonybundlename("com.monentreprise.myapp")
        harmonyminsdk(12)              # API level minimum
        harmonyversioncode(1000000)
        harmonyversionname("1.0.0")

        # Réseau (LAN / Internet) — injecte les permissions OHOS
        networkenabled(True)
```

```bash
jenga build harmony_app.jenga --platform HarmonyOS-arm64 --config Release
jenga package --platform harmonyos --type hap --project MyApp --output ./dist
```

---

## 4. Fonctions DSL HarmonyOS

| Fonction DSL | Description |
|--------------|-------------|
| `harmonysdk("<path>")` | Chemin du SDK (workspace-level) |
| `harmonyminsdk(12)` | API level minimum (compatibleSdkVersion) |
| `harmonytargetapi(12)` | API level cible |
| `harmonybundlename("com.x.y")` | Bundle name (identité de l'app) |
| `harmonyversioncode(1000000)` | Code de version (entier) |
| `harmonyversionname("1.0.0")` | Nom de version (semver) |
| `harmonypermissions([...])` | Permissions `ohos.permission.*` ✅ **nouveau** |
| `harmonyets(["ets/"])` | Répertoires de sources ArkTS/ETS ✅ **nouveau** |
| `harmonyresources([...])` | Dossiers de ressources (string.json, color.json, media…) |
| `harmonyassets([...])` | Fichiers bruts → `resources/rawfile/` |
| `harmonyappicon("icon.png")` | Icône applicative |
| `harmonysign(True)` | Active la signature du HAP |
| `harmonycertfile`, `harmonyprofile`, `harmonykeystore`, `harmonykeyalias`, `harmonykeypwd` | Paramètres de signature |

---

## 5. Permissions réseau (LAN / Internet)

Sur HarmonyOS, **sans `ohos.permission.INTERNET` une app ne peut pas ouvrir de
socket** — les connexions LAN/Internet échouent silencieusement au runtime.

Jenga injecte automatiquement les permissions réseau dans
`entry/src/main/module.json5 > requestPermissions` dès que vous activez le
réseau :

```python
with project("MyApp"):
    windowedapp()
    networkenabled(True)     # injecte INTERNET + GET_NETWORK_INFO + GET_WIFI_INFO
```

Génère dans `module.json5` :

```json5
{
  "module": {
    "name": "entry",
    "type": "entry",
    "requestPermissions": [
      { "name": "ohos.permission.INTERNET" },
      { "name": "ohos.permission.GET_NETWORK_INFO" },
      { "name": "ohos.permission.GET_WIFI_INFO" }
    ],
    ...
  }
}
```

### Permissions supplémentaires

```python
with project("MyApp"):
    windowedapp()
    networkenabled(True)
    harmonypermissions([
        "ohos.permission.CAMERA",
        "ohos.permission.MICROPHONE",
    ])
    # -> fusionne réseau auto + ces permissions, sans doublon
```

> 🌐 Le DSL réseau (`networkenabled`, `firewallrule`, …) est **multi-plateforme** :
> la même déclaration produit les règles `netsh` (Windows), `socketfilterfw`
> (macOS), `ufw/iptables` (Linux DEB), les `uses-permission` (Android) et les
> `requestPermissions` (HarmonyOS). Voir
> [Packaging, Déploiement, Publication](Packaging-Deploiement-Publication.md).

---

## 6. Ce que génère Jenga

```
Build/Bin/Release-HarmonyOS/MyApp/
├── libMyApp.so                       ← bibliothèque native compilée
└── harmony-build/                    ← projet hvigor généré (ne touche pas vos sources)
    ├── build-profile.json5
    ├── oh-package.json5
    ├── hvigorfile.ts
    └── entry/
        ├── build-profile.json5
        ├── hvigorfile.ts
        └── src/main/
            ├── module.json5          ← avec requestPermissions
            ├── ets/entryability/EntryAbility.ets
            ├── libs/arm64-v8a/libMyApp.so
            └── resources/...
```

Le `.hap` final est assemblé via `hvigorw assembleHap` et copié dans `./dist`.

---

## 7. Signature du HAP

```python
with project("MyApp"):
    windowedapp()
    harmonysign(True)
    harmonycertfile("cert/app.cer")
    harmonyprofile("cert/app.p7b")
    harmonykeystore("cert/app.p12")
    harmonykeyalias("debugKey")
    harmonykeypwd("xxxxxx")
```

---

## 8. Limitations connues

| Limitation | Détail |
|------------|--------|
| Backend natif fenêtré | L'exemple `27_nk_window` a un squelette HarmonyOS ; le backend natif réel reste à compléter selon votre moteur de rendu. |
| `hvigorw` requis | L'assemblage du `.hap` nécessite Node.js + `hvigor` (fournis par DevEco Studio ou le SDK). |
| Régénération `module.json5` | Le fichier n'est généré que s'il n'existe pas (préserve vos éditions). Supprimez `harmony-build/` pour forcer la régénération avec de nouvelles permissions. |

---

## 9. Dépannage

- **`HarmonyOS SDK not found`** → définir `HARMONY_OS_SDK` / `OHOS_SDK`.
- **`hvigorw not found`** → installer DevEco Studio ou ajouter le SDK au PATH.
- **App n'accède pas au réseau** → vérifier `networkenabled(True)` et regarder
  `module.json5 > requestPermissions` dans `harmony-build/entry/src/main/`.
- **Permissions non mises à jour après changement** → supprimer le dossier
  `harmony-build/` puis relancer le build.

---

## English

Jenga builds, packages and signs **HarmonyOS** apps (HAP) from native C/C++
sources, automatically generating the ArkTS project structure expected by
`hvigor`.

> **Status:** ✅ Integrated — full builder, HAP packaging, network permissions.
> Buildable from Windows, Linux and macOS (the OpenHarmony SDK is cross-platform).

### 1. Requirements

| Tool | Detail | Environment variable |
|------|--------|----------------------|
| OpenHarmony/HarmonyOS SDK | Native NDK (LLVM) + `hvigorw` | `OHOS_SDK`, `HARMONY_OS_SDK` or `HARMONY_SDK` |
| DevEco Studio (optional) | Official template + `hvigor` | auto-detected |
| Node.js | Required by `hvigorw` to assemble the `.hap` | on PATH |

```bash
# Windows
set HARMONY_OS_SDK=C:\Users\%USERNAME%\AppData\Local\OpenHarmony\Sdk
# Linux / macOS
export OHOS_SDK=$HOME/OpenHarmony/Sdk
```

### 2. Platform and architectures

`TargetOS.HARMONYOS` with `ARM` (armv7a), `ARM64` (aarch64), `X86_64` →
triples `aarch64-linux-ohos`, `arm-linux-ohos`, `x86_64-linux-ohos`.

### 3. Minimal example

```python
from Jenga import *
from Jenga.GlobalToolchains import RegisterJengaGlobalToolchains

with workspace("HarmonyDemo"):
    RegisterJengaGlobalToolchains()
    configurations(["Debug", "Release"])
    targetoses([TargetOS.HARMONYOS])
    targetarchs([TargetArch.ARM64])
    harmonysdk(os.getenv("HARMONY_OS_SDK", ""))

    with project("MyApp"):
        windowedapp()                  # -> produces a .hap (else .so/.a/ELF)
        language("C++"); cppdialect("C++17")
        files(["src/**.cpp"])
        harmonybundlename("com.company.myapp")
        harmonyminsdk(12)
        harmonyversioncode(1000000)
        harmonyversionname("1.0.0")
        networkenabled(True)           # injects ohos network permissions
```

```bash
jenga build harmony_app.jenga --platform HarmonyOS-arm64 --config Release
jenga package --platform harmonyos --type hap --project MyApp --output ./dist
```

### 4. DSL functions

`harmonysdk` · `harmonyminsdk` · `harmonytargetapi` · `harmonybundlename` ·
`harmonyversioncode` · `harmonyversionname` · `harmonypermissions` (✅ new) ·
`harmonyets` (✅ new) · `harmonyresources` · `harmonyassets` · `harmonyappicon` ·
`harmonysign` · `harmonycertfile` · `harmonyprofile` · `harmonykeystore` ·
`harmonykeyalias` · `harmonykeypwd`.

### 5. Network permissions (LAN / Internet)

Without `ohos.permission.INTERNET` a HarmonyOS app cannot open a socket — LAN/
Internet calls fail silently. Jenga auto-injects the permissions into
`entry/src/main/module.json5 > requestPermissions` as soon as you enable
networking:

```python
with project("MyApp"):
    windowedapp()
    networkenabled(True)     # INTERNET + GET_NETWORK_INFO + GET_WIFI_INFO

# extra permissions:
harmonypermissions(["ohos.permission.CAMERA", "ohos.permission.MICROPHONE"])
```

The cross-platform network DSL is shared — see
[Networking & Firewall](Reseau-et-Pare-feu.md).

### 6. What Jenga generates

```
Build/Bin/Release-HarmonyOS/MyApp/
├── libMyApp.so
└── harmony-build/                    # generated hvigor project (sources untouched)
    └── entry/src/main/
        ├── module.json5              # with requestPermissions
        ├── ets/entryability/EntryAbility.ets
        └── libs/arm64-v8a/libMyApp.so
```

### 7. Signing the HAP

```python
with project("MyApp"):
    windowedapp()
    harmonysign(True)
    harmonycertfile("cert/app.cer"); harmonyprofile("cert/app.p7b")
    harmonykeystore("cert/app.p12"); harmonykeyalias("debugKey")
    harmonykeypwd("xxxxxx")
```

### 8. Known limitations

- Windowed native backend: example `27_nk_window` has a HarmonyOS skeleton; the
  real native backend depends on your rendering engine.
- `hvigorw` (Node.js + hvigor) is required to assemble the `.hap`.
- `module.json5` is only generated if absent (preserves your edits) — delete
  `harmony-build/` to force regeneration with new permissions.

### 9. Troubleshooting

- `HarmonyOS SDK not found` → set `HARMONY_OS_SDK` / `OHOS_SDK`.
- `hvigorw not found` → install DevEco Studio or add the SDK to PATH.
- App has no network access → check `networkenabled(True)` and inspect
  `module.json5 > requestPermissions` under `harmony-build/entry/src/main/`.
- Permissions not updated → delete `harmony-build/` and rebuild.
