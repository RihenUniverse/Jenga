# 22_nk_multiplatform_sandbox

Exemple framework multi-plateforme et multi-architecture avec:
- une API utilisateur `nk::nk_main(int argc, char** argv)`
- un point d'entree par plateforme (`main_*`)
- des backends nommes par plateforme:
  - `Win32Window` / `Win32Event`
  - `XcbWindow` / `XcbEvent`
  - `XlibWindow` / `XlibEvent`
  - `AndroidWindow` / `AndroidEvent`
  - `EmscriptenWindow` / `EmscriptenEvent`
  - `IosWindow` / `IosEvent`
  - `MacosWindow` / `MacosEvent`
  - `HarmonyWindow` / `HarmonyEvent`

## Projets

- `NKFramework` (staticlib): coeur + backends + points d'entree platformes
- `NKSandbox` (windowedapp): implementation utilisateur de `nk_main`
- `NKSandboxTests` (consoleapp): test de validation simple

## Build rapide (Windows)

```powershell
cd Exemples\22_nk_multiplatform_sandbox
Jenga build --no-cache
```

## Lancer le test sandbox

```powershell
Jenga run --target NKSandboxTests
```

## Notes

Cet exemple est structure pour le multi-OS/multi-arch.
Les classes natives sont des stubs pedagogiques ici (architecture),
a completer ensuite avec les appels natifs reels (Win32/XCB/Xlib/Android/iOS/etc.).
