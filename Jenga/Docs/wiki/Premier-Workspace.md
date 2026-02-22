# Premier Workspace

Cette page te donne un exemple "clé en main" pour démarrer vite.

## Création

```bash
mkdir demo-jenga
cd demo-jenga
jenga workspace DemoWorkspace
jenga project DemoApp --kind console --lang C++
```

## Structure attendue

```text
demo-jenga/
  DemoWorkspace.jenga
  src/
  include/
```

## Exemple de fichier `.jenga`

```python
from Jenga import *

with workspace("DemoWorkspace"):
    configurations(["Debug", "Release"])
    targetoses([TargetOS.WINDOWS, TargetOS.LINUX, TargetOS.MACOS])
    targetarchs([TargetArch.X86_64])
    startproject("DemoApp")

    with project("DemoApp"):
        consoleapp()
        language("C++")
        cppdialect("C++20")
        files(["src/**.cpp", "include/**.hpp"])
        includedirs(["include"])
```

## Build et exécution

```bash
jenga build --config Debug
jenga run DemoApp
```

## Ajouter un fichier rapidement

```bash
jenga file DemoApp --src src/main.cpp
jenga file DemoApp --inc include
jenga file DemoApp --def APP_VERSION=1
```
