# Packaging, Déploiement, Publication / Packaging, Deployment, Publishing

**Langues / Languages :** [Français](#français) · [English](#english)

---

## Français

Commandes opérationnelles : `jenga package`, `jenga deploy`, `jenga publish`,
`jenga sign`, `jenga keygen`.

### 1. Packaging — formats par plateforme

| Plateforme | `--type` | Outil sous-jacent |
|-----------|----------|-------------------|
| Android | `apk`, `aab` | AndroidBuilder (aapt2, d8, apksigner) |
| iOS / tvOS / watchOS | `ipa` | xcrun / xcodebuild |
| Windows | `zip`, `msi`, `exe` | zipfile / WiX 4+ ou 3 / Inno Setup |
| Linux | `deb` (✅), `rpm`/`appimage`/`snap` (placeholders) | dpkg-deb |
| macOS | `pkg`, `dmg` | pkgbuild / create-dmg |
| Web | `zip` | EmscriptenBuilder |
| HarmonyOS | `hap` | hvigorw |

```bash
jenga package --platform android  --type apk --project MonApp --config Release
jenga package --platform ios       --type ipa --project MonApp --config Release
jenga package --platform windows   --type msi --project MonApp -o ./dist   # WiX 4+/3
jenga package --platform windows   --type exe --project MonApp -o ./dist   # Inno Setup
jenga package --platform linux     --type deb --project MonApp -o ./dist
jenga package --platform macos     --type pkg --project MonApp -o ./dist
jenga package --platform harmonyos --type hap --project MonApp -o ./dist
```

### 2. Métadonnées installer (DSL)

```python
with project("MonApp"):
    consoleapp()
    files(["src/**.cpp"])
    apppublisher("Mon Studio")
    appversion("1.2.3")
    licensefile("LICENSE.md")        # .txt/.md auto-converti en RTF (WiX)
    createdesktopshortcut(True)
    dependfiles(["../../Resources"]) # ressources + DLLs embarquées
    appicon("res/icon.png")          # PNG/JPG auto-converti (ICO/ICNS)
```

### 3. Permissions réseau / pare-feu

Le packaging configure automatiquement le pare-feu et les permissions réseau sur
**toutes** les plateformes via `networkenabled()` / `firewallrule()` :
MSI (WiX 3 **et** 4), EXE (Inno), DEB (postinst/postrm), PKG (socketfilterfw),
APK/AAB (manifest), HAP (module.json5), IPA (Info.plist).
Voir [Réseau et Pare-feu](Reseau-et-Pare-feu.md).

### 4. Signature

```bash
jenga keygen --interactive                    # keystore Android
jenga keygen --harmony                         # certificat .p12 HarmonyOS
jenga sign --apk ./Build/Bin/Debug/MonApp/MonApp.apk \
           --keystore ./keystore.jks --alias mykey \
           --storepass xxxx --keypass xxxx
```

### 5. Déploiement

```bash
jenga deploy --platform android --target emulator-5554 --run
jenga deploy --platform ios --project MonApp
jenga deploy --platform harmonyos --hap ./dist/MonApp.hap --target 127.0.0.1:5555
jenga deploy --platform android --list-devices    # lister les appareils
```

### 6. Publication

```bash
jenga publish --registry nuget --package ./dist/MonPackage.nupkg --api-key <TOKEN>
```

### 7. Limitations actuelles

- `publish` : seul le flux **NuGet** est réellement implémenté ; le reste est partiel.
- `deploy` : Linux pas encore implémenté.
- `profile` : certaines plateformes en mode placeholder.
- `package` Linux : `rpm`, `appimage`, `snap` sont des placeholders (`deb` OK).

---

## English

Operational commands: `jenga package`, `jenga deploy`, `jenga publish`,
`jenga sign`, `jenga keygen`.

### 1. Packaging — formats per platform

| Platform | `--type` | Underlying tool |
|----------|----------|-----------------|
| Android | `apk`, `aab` | AndroidBuilder (aapt2, d8, apksigner) |
| iOS / tvOS / watchOS | `ipa` | xcrun / xcodebuild |
| Windows | `zip`, `msi`, `exe` | zipfile / WiX 4+ or 3 / Inno Setup |
| Linux | `deb` (✅), `rpm`/`appimage`/`snap` (placeholders) | dpkg-deb |
| macOS | `pkg`, `dmg` | pkgbuild / create-dmg |
| Web | `zip` | EmscriptenBuilder |
| HarmonyOS | `hap` | hvigorw |

```bash
jenga package --platform android  --type apk --project MyApp --config Release
jenga package --platform ios       --type ipa --project MyApp --config Release
jenga package --platform windows   --type msi --project MyApp -o ./dist   # WiX 4+/3
jenga package --platform windows   --type exe --project MyApp -o ./dist   # Inno Setup
jenga package --platform linux     --type deb --project MyApp -o ./dist
jenga package --platform macos     --type pkg --project MyApp -o ./dist
jenga package --platform harmonyos --type hap --project MyApp -o ./dist
```

### 2. Installer metadata (DSL)

```python
with project("MyApp"):
    consoleapp()
    files(["src/**.cpp"])
    apppublisher("My Studio")
    appversion("1.2.3")
    licensefile("LICENSE.md")        # .txt/.md auto-converted to RTF (WiX)
    createdesktopshortcut(True)
    dependfiles(["../../Resources"]) # bundled resources + DLLs
    appicon("res/icon.png")          # PNG/JPG auto-converted (ICO/ICNS)
```

### 3. Network permissions / firewall

Packaging automatically configures the firewall and network permissions on
**every** platform via `networkenabled()` / `firewallrule()`:
MSI (WiX 3 **and** 4), EXE (Inno), DEB (postinst/postrm), PKG (socketfilterfw),
APK/AAB (manifest), HAP (module.json5), IPA (Info.plist).
See [Networking & Firewall](Reseau-et-Pare-feu.md).

### 4. Signing

```bash
jenga keygen --interactive                    # Android keystore
jenga keygen --harmony                         # HarmonyOS .p12 certificate
jenga sign --apk ./Build/Bin/Debug/MyApp/MyApp.apk \
           --keystore ./keystore.jks --alias mykey \
           --storepass xxxx --keypass xxxx
```

### 5. Deployment

```bash
jenga deploy --platform android --target emulator-5554 --run
jenga deploy --platform ios --project MyApp
jenga deploy --platform harmonyos --hap ./dist/MyApp.hap --target 127.0.0.1:5555
jenga deploy --platform android --list-devices    # list devices
```

### 6. Publishing

```bash
jenga publish --registry nuget --package ./dist/MyPackage.nupkg --api-key <TOKEN>
```

### 7. Current limitations

- `publish`: only the **NuGet** flow is fully implemented; the rest is partial.
- `deploy`: Linux not yet implemented.
- `profile`: some platforms are placeholders.
- `package` Linux: `rpm`, `appimage`, `snap` are placeholders (`deb` works).
