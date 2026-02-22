# 26_xbox_project_kinds

Demonstration des 4 types de projet Xbox:
- `staticlib` (`XboxStaticMath`)
- `sharedlib` (`XboxSharedMath`)
- `consoleapp` (`XboxConsoleApp`)
- `windowedapp` (`XboxWindowedApp`)

## Build (mode principal GDK/GameCore)

```bat
cd /d E:\Projets\MacShared\Projets\Jenga\Jenga\Exemples\26_xbox_project_kinds
python ..\..\jenga.py build --platform XboxSeries-x64
```

## Build (optionnel UWP Dev Mode)

```bat
python ..\..\jenga.py build --platform XboxSeries-x64 --xbox-mode=uwp
```
