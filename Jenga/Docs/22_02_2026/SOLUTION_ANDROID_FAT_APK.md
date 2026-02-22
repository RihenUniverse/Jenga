# Solution : Fat APK Android (Universal APK)

**Date** : 2026-02-22
**Problème** : Jenga génère une APK par ABI au lieu d'une fat APK universelle
**Impact** : Les APK ne s'installent pas sur MEmu car elles ne contiennent pas l'ABI x86

---

## 🔍 Analyse du Problème

### Comportement Actuel

Jenga génère **une APK par architecture** :
```bash
jenga build --platform android-arm64  → APK avec lib/arm64-v8a/ uniquement
jenga build --platform android-x86    → APK avec lib/x86/ uniquement
```

**Pourquoi?**
Le builder Android (`Jenga/Core/Builders/Android.py`) compile pour **une seule ABI** à la fois (définie par `--platform android-{arch}`), puis génère l'APK avec seulement cette ABI.

### Code Responsable

[Android.py:702-751](e:\Projets\MacShared\Projets\Jenga\Jenga\Core\Builders\Android.py#L702-L751) :
```python
def Build(self, targetProject: Optional[str] = None) -> int:
    # Compile le code natif pour self.targetArch (UNE SEULE architecture)
    code = super().Build(targetProject)

    # Collecte les .so de cette architecture uniquement
    native_libs: List[str] = []
    app_out = self.GetTargetPath(proj)
    if app_out.exists():
        native_libs.append(str(app_out))

    # Génère une APK avec seulement cette ABI
    if not self.BuildAPK(proj, native_libs):
        return 1
```

[Android.py:764-766](e:\Projets\MacShared\Projets\Jenga\Jenga\Core\Builders\Android.py#L764-L766) :
```python
def BuildAPK(self, project: Project, nativeLibs: List[str]) -> bool:
    Reporter.Info(f"Building APK for {project.name} ({self.ndk_abi})")  # UNE SEULE ABI
    build_dir = Path(self.GetTargetDir(project)) / f"android-build-{self.ndk_abi}"
    # ...
```

---

## ✅ Solution 1 : Compiler pour x86 Uniquement (Workaround Rapide)

**Pour MEmu/BlueStacks** : Compiler spécifiquement pour x86 (32-bit)

```bash
cd "e:\Projets\MacShared\Projets\Jenga\Jenga\Exemples\18_window_android_native"
jenga build --platform android-x86
```

**APK générée** :
`Build/Bin/Debug/android-x86/AndroidWindow/android-build-x86/AndroidWindow-Debug.apk`

**Installation sur MEmu** :
```bash
adb connect 127.0.0.1:21503
adb install -r "Build/Bin/Debug/android-x86/AndroidWindow/android-build-x86/AndroidWindow-Debug.apk"
```

**Avantage** : Fonctionne immédiatement
**Inconvénient** : Une APK par ABI, il faut compiler 4 fois pour avoir toutes les ABIs

---

## ✅ Solution 2 : Modifier le Builder Android (Fat APK Universelle)

**Objectif** : Générer **une seule APK** contenant toutes les ABIs spécifiées dans `androidabis()`

### Modifications Nécessaires

#### 1. Modifier `Build()` pour compiler toutes les ABIs

[Android.py:702](e:\Projets\MacShared\Projets\Jenga\Jenga\Core\Builders\Android.py#L702) :
```python
def Build(self, targetProject: Optional[str] = None) -> int:
    if self._ShouldUseNdkMk():
        return self._BuildUsingNdkMk(targetProject)

    app_projects: List[Project] = []
    for name, proj in self.workspace.projects.items():
        if targetProject and name != targetProject:
            continue
        if proj.kind in (ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP):
            app_projects.append(proj)

    for proj in app_projects:
        if proj.kind == ProjectKind.CONSOLE_APP:
            # Console apps : compiler une seule fois
            code = super().Build(targetProject)
            if code != 0:
                return code
            continue

        # Windowed apps : compiler pour toutes les ABIs
        if not self._BuildUniversalAPK(proj):
            return 1

    return 0
```

#### 2. Créer `_BuildUniversalAPK()` pour compiler toutes les ABIs

```python
def _BuildUniversalAPK(self, project: Project) -> bool:
    """
    Compile le projet pour toutes les ABIs spécifiées dans androidAbis
    et génère une fat APK contenant toutes les architectures.
    """
    # Récupérer les ABIs depuis project.androidAbis
    target_abis = getattr(project, 'androidAbis', ['armeabi-v7a', 'arm64-v8a', 'x86', 'x86_64'])
    if not target_abis:
        target_abis = ['arm64-v8a']  # Fallback

    Reporter.Info(f"Building universal APK for {project.name} ({len(target_abis)} ABIs)")

    # Dictionnaire : {abi: [liste des .so]}
    all_native_libs = {}

    # Mapping ABI → TargetArch
    abi_to_arch = {
        'armeabi-v7a': TargetArch.ARM,
        'arm64-v8a': TargetArch.ARM64,
        'x86': TargetArch.X86,
        'x86_64': TargetArch.X86_64,
    }

    # Compiler pour chaque ABI
    for abi in target_abis:
        if abi not in abi_to_arch:
            Reporter.Warning(f"Unknown ABI: {abi}, skipping")
            continue

        Reporter.Info(f"  Compiling for {abi}...")

        # Sauvegarder les valeurs actuelles
        original_arch = self.targetArch
        original_ndk_abi = self.ndk_abi

        # Changer temporairement l'architecture
        self.targetArch = abi_to_arch[abi]
        self.ndk_abi = abi
        self._PrepareNDKToolchain()  # Reconfigurer la toolchain pour cette ABI

        # Compiler le code natif pour cette ABI
        code = super().Build(project.name)
        if code != 0:
            Reporter.Error(f"Failed to build for {abi}")
            return False

        # Collecter les bibliothèques natives (.so) pour cette ABI
        native_libs = []
        app_out = self.GetTargetPath(project)
        if app_out.exists():
            native_libs.append(str(app_out))

        for dep_name in project.dependsOn:
            dep = self.workspace.projects.get(dep_name)
            if not dep:
                continue
            dep_out = self.GetTargetPath(dep)
            if dep.kind == ProjectKind.SHARED_LIB and dep_out.exists():
                native_libs.append(str(dep_out))

        all_native_libs[abi] = native_libs

        # Restaurer les valeurs originales
        self.targetArch = original_arch
        self.ndk_abi = original_ndk_abi
        self._PrepareNDKToolchain()

    # Générer une fat APK avec toutes les ABIs
    if self.build_aab:
        return self._BuildUniversalAAB(project, all_native_libs)
    else:
        return self._BuildUniversalAPKFile(project, all_native_libs)
```

#### 3. Créer `_BuildUniversalAPKFile()` pour assembler la fat APK

```python
def _BuildUniversalAPKFile(self, project: Project, all_native_libs: Dict[str, List[str]]) -> bool:
    """
    Assemble une fat APK contenant toutes les ABIs.
    """
    Reporter.Info(f"Assembling universal APK for {project.name}")

    # Utiliser la première ABI pour la structure de base
    first_abi = list(all_native_libs.keys())[0]
    build_dir = Path(self.GetTargetDir(project)) / f"android-build-universal"
    FileSystem.RemoveDirectory(build_dir, recursive=True, ignoreErrors=True)
    FileSystem.MakeDirectory(build_dir)

    # 1. Créer la structure de l'APK
    apk_unsigned_unaligned = build_dir / "app-unsigned-unaligned.apk"
    apk_unsigned_aligned = build_dir / "app-unsigned.apk"
    apk_signed = build_dir / f"{project.targetName or project.name}-{self.config}.apk"

    # 2. Compiler les ressources avec aapt2 (une seule fois)
    res_zip = build_dir / "resources.zip"
    if not self._CompileResources(project, build_dir, res_zip):
        return False

    # 3. Lier les ressources
    r_java_dir = build_dir / "gen"
    FileSystem.MakeDirectory(r_java_dir)
    if not self._LinkResources(project, res_zip, r_java_dir, build_dir):
        return False

    # 4. Compiler Java + DEX (une seule fois)
    java_files = self._CollectJavaSourceFiles(project)
    java_libs = self._CollectJavaLibraries(project)
    classes_dir = build_dir / "classes"
    FileSystem.MakeDirectory(classes_dir)

    if java_files or java_libs:
        if not self._CompileJava(project, r_java_dir, java_files, java_libs, classes_dir):
            return False
        if project.androidProguard:
            if not self._RunProguard(project, classes_dir, java_libs, build_dir):
                return False
            proguard_out = build_dir / "proguard"
            classes_dir = proguard_out / "classes"

    dex_files = self._CompileDex(project, classes_dir, java_libs, build_dir)
    if dex_files is None:
        return False

    # 5. Assembler l'APK avec TOUTES les ABIs
    if not self._AssembleUniversalApk(project, build_dir, dex_files, res_zip, all_native_libs, apk_unsigned_unaligned):
        return False

    # 6. Zipalign
    if not self._Zipalign(apk_unsigned_unaligned, apk_unsigned_aligned):
        return False

    # 7. Signer
    if project.androidSign:
        if not self._SignApk(project, apk_unsigned_aligned, apk_signed):
            return False
    else:
        shutil.copy2(apk_unsigned_aligned, apk_signed)

    final_apk = Path(self.GetTargetDir(project)) / f"{project.targetName or project.name}.apk"
    shutil.copy2(apk_signed, final_apk)
    Reporter.Success(f"Universal APK generated: {apk_signed}")
    return True
```

#### 4. Créer `_AssembleUniversalApk()` pour organiser les .so par ABI

```python
def _AssembleUniversalApk(self, project: Project, build_dir: Path, dex_files: List[Path],
                          res_zip: Path, all_native_libs: Dict[str, List[str]],
                          out_apk: Path) -> bool:
    """
    Assemble une APK avec les .so organisés par ABI : lib/armeabi-v7a/, lib/arm64-v8a/, lib/x86/, lib/x86_64/
    """
    with zipfile.ZipFile(out_apk, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Ajouter les ressources
        if res_zip.exists():
            with zipfile.ZipFile(res_zip, 'r') as res_zip_file:
                for item in res_zip_file.namelist():
                    data = res_zip_file.read(item)
                    zf.writestr(item, data)

        # Ajouter les DEX files
        for dex_file in dex_files:
            zf.write(dex_file, f"classes{dex_files.index(dex_file) + 1 if dex_files.index(dex_file) > 0 else ''}.dex")

        # Ajouter les bibliothèques natives pour chaque ABI
        for abi, native_libs in all_native_libs.items():
            for lib_path in native_libs:
                lib_name = Path(lib_path).name
                zf.write(lib_path, f"lib/{abi}/{lib_name}")

        # Ajouter les assets
        assets = self._CollectAssets(project)
        for asset_file in assets:
            rel_path = asset_file.relative_to(Path(self.ResolveProjectPath(project, ".")))
            zf.write(asset_file, f"assets/{rel_path}")

        # Ajouter AndroidManifest.xml
        manifest = build_dir / "AndroidManifest.xml"
        if manifest.exists():
            zf.write(manifest, "AndroidManifest.xml")

    return True
```

---

## 📊 Comparaison des Solutions

| Critère | Solution 1 (Workaround) | Solution 2 (Fat APK) |
|---------|-------------------------|----------------------|
| **Complexité** | ⭐ Simple | ⭐⭐⭐⭐ Complexe |
| **Temps de dev** | 0 minutes | ~4-6 heures |
| **Compilation** | 1 fois par ABI (4x) | 1 fois (toutes ABIs) |
| **Taille APK** | ~50 KB par ABI | ~200 KB (4 ABIs) |
| **Compatibilité** | 1 ABI par APK | 4 ABIs dans 1 APK |
| **Installation MEmu** | ✅ Fonctionne (x86) | ✅ Fonctionne (universel) |
| **Google Play** | ✅ Optimal | ⚠️ Plus grosse APK |

---

## 💡 Recommandation

### Pour l'instant (Développement/Test)

**Utilisez Solution 1** : Compilez spécifiquement pour x86

```bash
# Pour MEmu
jenga build --platform android-x86

# Pour smartphones ARM récents
jenga build --platform android-arm64

# Pour anciens smartphones ARM
jenga build --platform android-arm
```

### Pour la production (Distribution)

**Si besoin de fat APK** : Implémentez Solution 2 en modifiant `Android.py`

**Sinon** : Utilisez les APK Split (recommandé Google Play) - Google Play optimise automatiquement la distribution des APKs par ABI

---

## 🔧 Implémentation Immédiate

Voulez-vous que j'implémente la **Solution 2 (Fat APK)** dans le builder Android maintenant?

**Impact** :
- ✅ Génération automatique de fat APK universelles
- ✅ Compatible MEmu, tous smartphones, tous émulateurs
- ⚠️ Temps de compilation 4x plus long (compile 4 ABIs)
- ⚠️ APKs 4x plus grosses

**Alternative** : Créer une commande séparée `jenga build-universal --platform android` qui utilise la Solution 2, et garder le comportement actuel pour `jenga build --platform android-{arch}`.

---

**Généré par** : Claude Code
**Build System** : Jenga v2.0.0
