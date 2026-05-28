# Réseau et Pare-feu / Networking & Firewall

**Langues / Languages :** [Français](#français) · [English](#english)

---

## Français

Jenga configure **automatiquement les permissions réseau** de vos applications
au moment de l'installation/packaging, sur **toutes les plateformes**, à partir
d'une seule déclaration DSL. Plus besoin d'ouvrir manuellement le pare-feu pour
qu'un jeu multijoueur LAN ou un serveur local accepte les connexions entrantes.

> **Pourquoi ?** Sans règle explicite, Windows Defender bloque silencieusement
> les connexions UDP/TCP entrantes, macOS demande confirmation, et Android /
> HarmonyOS / iOS refusent l'accès socket sans permission déclarée. Cas typique :
> un Pong PC ↔ Android sur LAN qui échoue côté PC.

---

## 1. DSL — vue d'ensemble

| Fonction DSL | Rôle | Plateformes concernées |
|--------------|------|------------------------|
| `networkenabled(True)` | Active le réseau (règle/permission par défaut) | Toutes |
| `firewallrule(...)` | Règle de pare-feu personnalisée (ports, protocole) | Windows, Linux |
| `networkusagedescription("...")` | Phrase affichée à l'utilisateur | iOS, macOS |
| `bonjourservices([...])` | Services Bonjour/mDNS publiés | iOS, macOS |
| `iosallowarbitraryloads(True)` | Autorise HTTP non-TLS (LAN/IoT) | iOS |
| `androidpermissions([...])` | Permissions Android explicites | Android |
| `harmonypermissions([...])` | Permissions `ohos.permission.*` explicites | HarmonyOS |

---

## 2. Usage minimal

```python
with project("MyGame"):
    consoleapp()
    files(["src/**.cpp"])
    networkenabled(True)     # suffit pour autoriser le LAN entrant
```

Selon la plateforme cible/packagée, Jenga produit :

| Plateforme | Action générée |
|------------|----------------|
| **Windows (MSI WiX 3/4, EXE Inno)** | Règle `netsh advfirewall` entrante, tous profils, ajoutée à l'install / retirée au uninstall |
| **macOS (PKG)** | Script postinstall `socketfilterfw --add` + `--unblockapp` |
| **Linux (DEB)** | Hooks `postinst`/`postrm` détectant `ufw` / `firewall-cmd` / `iptables` |
| **Android (APK/AAB)** | `INTERNET` + `ACCESS_NETWORK_STATE` + `ACCESS_WIFI_STATE` dans le manifest |
| **iOS (IPA)** | `NSLocalNetworkUsageDescription` dans Info.plist |
| **HarmonyOS (HAP)** | `INTERNET` + `GET_NETWORK_INFO` + `GET_WIFI_INFO` dans `module.json5` |

---

## 3. Règles personnalisées (Windows / Linux)

```python
with project("MyServer"):
    consoleapp()
    networkenabled(True)

    # Ouvre un port TCP précis
    firewallrule(name="MyServer TCP", protocol="tcp", ports=["7777"])

    # Découverte UDP sur plage de ports, profils Windows ciblés
    firewallrule(name="MyServer discovery",
                 protocol="udp",
                 ports=["5353", "8000-8100"],
                 profiles=["private", "public"])
```

### Paramètres de `firewallrule()`

| Paramètre | Valeurs | Défaut |
|-----------|---------|--------|
| `name` | nom visible (vide → `"{AppName} (Network)"`) | `""` |
| `direction` | `"in"`, `"out"`, `"both"` | `"in"` |
| `action` | `"allow"`, `"block"` | `"allow"` |
| `protocol` | `"any"`, `"tcp"`, `"udp"` | `"any"` |
| `ports` | liste, ex `["7777", "8000-8100"]` (vide = tous) | `[]` |
| `profiles` | Windows : sous-ensemble de `domain`/`private`/`public`/`any` | `["any"]` |
| `programOverride` | autre exe que celui du projet | `""` |

> Déclarer au moins un `firewallrule()` active implicitement `networkenabled`.
> Les règles personnalisées **remplacent** la règle « tout autoriser » par défaut.

---

## 4. iOS / macOS — réseau local et Bonjour

```python
with project("Discovery"):
    windowedapp()
    networkenabled(True)
    networkusagedescription("Discovery utilise le réseau local pour trouver "
                            "les pairs à proximité.")
    bonjourservices(["_discovery._tcp"])
    iosallowarbitraryloads(True)     # si vous parlez en HTTP clair sur le LAN
```

Génère dans **Info.plist** :

```xml
<key>NSLocalNetworkUsageDescription</key>
<string>Discovery utilise le réseau local pour trouver les pairs à proximité.</string>
<key>NSBonjourServices</key>
<array><string>_discovery._tcp</string></array>
<key>NSAppTransportSecurity</key>
<dict><key>NSAllowsArbitraryLoads</key><true/></dict>
```

---

## 5. Architecture interne

Toute la logique de génération des commandes est centralisée dans
[Core/FirewallSpec.py](../../Core/FirewallSpec.py) :

| Helper | Produit |
|--------|---------|
| `BuildNetshAddCommands()` / `BuildNetshDeleteCommands()` | commandes `netsh` (Windows) |
| `BuildSocketfilterfwAddScript()` / `...RemoveScript()` | lignes shell `socketfilterfw` (macOS) |
| `BuildLinuxFirewallAddScript()` / `...RemoveScript()` | scripts `postinst`/`postrm` (Linux) |
| `ResolveAndroidNetworkPermissions()` | permissions `android.permission.*` |
| `ResolveHarmonyNetworkPermissions()` | permissions `ohos.permission.*` |
| `BuildIosInfoPlistNetworkKeys()` | clés `NS*` pour Info.plist (iOS/macOS) |

Les builders d'installeur (`Commands/Package.py`, `Builders/Android.py`,
`Builders/Ios.py`, `Builders/Macos.py`, `Builders/HarmonyOs.py`) appellent ces
helpers — la logique de mapping (direction/protocole/ports) n'est jamais
dupliquée.

---

## 6. Vérification après installation

### Windows
```powershell
netsh advfirewall firewall show rule name="MyGame (Network)"
```

### macOS
```bash
/usr/libexec/ApplicationFirewall/socketfilterfw --listapps | grep MyGame
```

### Linux
```bash
sudo ufw status | grep 7777        # ou : sudo firewall-cmd --list-ports
```

### Android / HarmonyOS
Vérifier les permissions déclarées dans l'`AndroidManifest.xml` (APK) ou
`module.json5` (HAP) générés sous `Build/Bin/...`.

---

## 7. Désactiver le réseau

Par défaut, **aucune** règle n'est créée si vous ne déclarez ni
`networkenabled(True)` ni `firewallrule(...)`. Pour une app qui n'a pas besoin
du réseau, ne déclarez simplement rien — Jenga ne touchera pas au pare-feu.

---

## English

Jenga **automatically configures network permissions** for your apps at install
time, on **every platform**, from a single DSL declaration. No more manually
opening the firewall so a LAN multiplayer game or a local server can accept
incoming connections.

> **Why?** Without an explicit rule, Windows Defender silently blocks incoming
> UDP/TCP connections, macOS prompts for confirmation, and Android / HarmonyOS /
> iOS deny socket access without a declared permission.

### 1. DSL overview

| DSL function | Role | Platforms |
|--------------|------|-----------|
| `networkenabled(True)` | Enable networking (default rule/permission) | All |
| `firewallrule(...)` | Custom firewall rule (ports, protocol) | Windows, Linux |
| `networkusagedescription("...")` | Message shown to the user | iOS, macOS |
| `bonjourservices([...])` | Published Bonjour/mDNS services | iOS, macOS |
| `iosallowarbitraryloads(True)` | Allow non-TLS HTTP (LAN/IoT) | iOS |
| `androidpermissions([...])` | Explicit Android permissions | Android |
| `harmonypermissions([...])` | Explicit `ohos.permission.*` | HarmonyOS |

### 2. Minimal usage

```python
with project("MyGame"):
    consoleapp()
    files(["src/**.cpp"])
    networkenabled(True)     # enough to allow incoming LAN traffic
```

Per platform, Jenga generates:

| Platform | Generated action |
|----------|------------------|
| **Windows (MSI WiX 3/4, EXE Inno)** | Inbound `netsh advfirewall` rule, all profiles, added on install / removed on uninstall |
| **macOS (PKG)** | `socketfilterfw --add` + `--unblockapp` postinstall script |
| **Linux (DEB)** | `postinst`/`postrm` hooks detecting `ufw` / `firewall-cmd` / `iptables` |
| **Android (APK/AAB)** | `INTERNET` + `ACCESS_NETWORK_STATE` + `ACCESS_WIFI_STATE` in the manifest |
| **iOS (IPA)** | `NSLocalNetworkUsageDescription` in Info.plist |
| **HarmonyOS (HAP)** | `INTERNET` + `GET_NETWORK_INFO` + `GET_WIFI_INFO` in `module.json5` |

### 3. Custom rules (Windows / Linux)

```python
with project("MyServer"):
    consoleapp()
    networkenabled(True)
    firewallrule(name="MyServer TCP", protocol="tcp", ports=["7777"])
    firewallrule(name="MyServer discovery", protocol="udp",
                 ports=["5353", "8000-8100"], profiles=["private", "public"])
```

`firewallrule()` parameters: `name`, `direction` (`in`/`out`/`both`), `action`
(`allow`/`block`), `protocol` (`any`/`tcp`/`udp`), `ports` (list, supports
ranges), `profiles` (Windows: `domain`/`private`/`public`/`any`),
`programOverride`. Declaring at least one rule implicitly enables networking;
custom rules **replace** the default allow-all rule.

### 4. iOS / macOS — local network and Bonjour

```python
with project("Discovery"):
    windowedapp()
    networkenabled(True)
    networkusagedescription("Discovery uses the local network to find peers.")
    bonjourservices(["_discovery._tcp"])
    iosallowarbitraryloads(True)
```

### 5. Internal architecture

All command generation lives in
[Core/FirewallSpec.py](../../Core/FirewallSpec.py): `BuildNetshAddCommands` /
`BuildNetshDeleteCommands` (Windows), `BuildSocketfilterfwAddScript` /
`...RemoveScript` (macOS), `BuildLinuxFirewallAddScript` / `...RemoveScript`
(Linux), `ResolveAndroidNetworkPermissions`, `ResolveHarmonyNetworkPermissions`,
`BuildIosInfoPlistNetworkKeys`. The installer builders call these helpers — the
direction/protocol/ports mapping is never duplicated.

### 6. Verify after install

```powershell
netsh advfirewall firewall show rule name="MyGame (Network)"      # Windows
```
```bash
/usr/libexec/ApplicationFirewall/socketfilterfw --listapps | grep MyGame   # macOS
sudo ufw status | grep 7777                                       # Linux
```

### 7. Disabling networking

By default **no** rule is created unless you declare `networkenabled(True)` or
`firewallrule(...)`. For an app that does not need the network, declare nothing —
Jenga leaves the firewall untouched.
