# Release Description (GitHub)

## Jenga Build System v2.0.1

Jenga est un système de build moderne pour projets natifs C/C++, piloté par une DSL Python et une CLI unifiée.

Cette release consolide l’architecture `Jenga/Core` + `Jenga/Commands`, améliore le workflow multi-plateforme, et fournit une base propre pour build, tests, docs et packaging.

### Points clés

- DSL Python unifiée: `workspace`, `project`, `toolchain`, `filter`, `unitest`, `test`, `include`
- Commandes principales: `build`, `run`, `test`, `clean`, `rebuild`, `watch`, `info`, `gen`
- Support multi-plateforme (selon toolchains/disponibilité host): Windows, Linux, macOS, Android, iOS, Web
- Gestion des toolchains globales: `jenga install toolchain ...` + `jenga config ...`
- Extraction de documentation: `jenga docs extract`
- Exemples prêts à l’emploi dans `Exemples/`

### Correctifs notables

- Correction de l’entrypoint CLI Python (`jenga`) vers `Jenga.jenga:main`
- Amélioration de compatibilité pour anciens lanceurs qui référencent `Jenga.Jenga`
- Ajustement des scripts de lancement `jenga.bat` / `jenga.sh`

### Ressources

- README: `README.md`
- README complet: `README_v2.md`
- Wiki local: `wiki/README.md`
- Guide utilisateur: `Jenga_User_Guide.md`
- Guide développeur: `Jenga_Developer_Guide.md`

---

## Comment builder les artefacts de release (Python)

### 1) Préparer l’environnement

```bash
python -m pip install --upgrade pip
python -m pip install --upgrade build twine setuptools wheel
```

### 2) Nettoyer les anciens artefacts (optionnel)

```bash
python -m pip uninstall jenga -y
rm -rf build dist *.egg-info
```

Sous Windows PowerShell:

```powershell
python -m pip uninstall jenga -y
Remove-Item -Recurse -Force build, dist, *.egg-info
```

### 3) Générer les artefacts standards PyPI

```bash
python -m build
```

Sorties attendues dans `dist/`:

- `jenga-<version>-py3-none-any.whl`
- `jenga-<version>.tar.gz`

### 4) Générer aussi un sdist ZIP (optionnel)

```bash
python setup.py sdist --formats=zip
```

Sortie supplémentaire:

- `dist/jenga-<version>.zip`

### 5) Vérifier les métadonnées des artefacts

```bash
python -m twine check dist/*
```

### 6) Tester une installation locale depuis wheel

```bash
python -m pip install --force-reinstall dist/jenga-<version>-py3-none-any.whl
jenga --version
```

---

## Générer des archives source pour GitHub Release (zip/tar.gz)

Ces archives sont utiles comme assets "Source code" additionnels.

```bash
git archive --format=zip    --output dist/jenga-v2.0.1-source.zip HEAD
git archive --format=tar.gz --output dist/jenga-v2.0.1-source.tar.gz HEAD
```

---

## Exemple de checklist avant publication

1. `python -m build` OK
2. `python -m twine check dist/*` OK
3. `jenga --version` OK après install wheel
4. README/Wiki/Guides à jour
5. Assets uploadés sur GitHub Release (`.whl`, `.tar.gz`, éventuellement `.zip`)
