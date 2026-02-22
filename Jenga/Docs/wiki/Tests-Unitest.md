# Tests Unitest

Jenga intègre un flux de tests via:

- `with unitest() as u: ...`
- `with test(): ...` dans un projet
- commande CLI `jenga test`

## Exemple complet

```python
from Jenga import *

with workspace("UnitWorkspace"):
    configurations(["Debug", "Release"])
    targetoses([TargetOS.WINDOWS, TargetOS.LINUX, TargetOS.MACOS])
    targetarchs([TargetArch.X86_64])

    with unitest() as u:
        u.Precompiled()   # ou u.Compile(...)

    with project("Calculator"):
        staticlib()
        language("C++")
        files(["src/**.cpp"])
        includedirs(["include"])

        with test():
            testfiles(["tests/**.cpp"])
            testmainfile("src/main.cpp")
            testoptions(["--verbose"])
```

## Commandes utiles

```bash
jenga test
jenga test --project Calculator_Tests
jenga test --config Debug --no-build
```

## Cas fréquents

### Erreur: `test context must be placed directly inside a project block`

La section `with test():` doit être directement imbriquée dans `with project(...):`.

### Erreur: Unitest non configuré

Ajoute un bloc `with unitest() as u:` dans le workspace avant les projets qui utilisent `test()`.
