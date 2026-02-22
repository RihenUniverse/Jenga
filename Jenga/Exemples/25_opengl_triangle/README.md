# 25_opengl_triangle

## Description

Exemple démontrant le rendu **OpenGL multi-plateformes** d'un triangle coloré avec interpolation de couleurs par vertex, à partir d'un **seul fichier source C++**.

Ce projet illustre comment Jenga permet de compiler le même code OpenGL pour 4 plateformes différentes, chacune utilisant son système de fenêtrage natif et son API graphique :

- **Windows** : Win32 + WGL + OpenGL
- **Linux** : X11 + GLX + OpenGL
- **Android** : NativeActivity + EGL + OpenGL ES 3.0
- **Web** : Emscripten + WebGL (via OpenGL ES 2.0)

Le code utilise des `#ifdef` pour gérer les spécificités de chaque plateforme tout en partageant les shaders et la logique de rendu.

## Plateformes supportées

| Plateforme | Windowing | Context | Graphics API | Toolchain |
|-----------|-----------|---------|--------------|-----------|
| **Windows** (x86_64) | Win32 | WGL | OpenGL 2.0+ | clang-mingw |
| **Linux** (x86_64) | X11 | GLX | OpenGL 2.0+ | zig-linux-x64 |
| **Android** (arm64/x86_64) | NativeActivity | EGL | OpenGL ES 3.0 | android-ndk |
| **Web** (wasm32) | Canvas | WebGL | OpenGL ES 2.0 | emscripten |

## Architecture

```
25_opengl_triangle/
├── 25_opengl_triangle.jenga    # Configuration multi-plateformes
└── src/
    └── main.cpp                 # Code source unique avec #ifdef par plateforme
```

## Rendu

Triangle avec 3 couleurs interpolées :
- **Sommet haut** : Rouge (1.0, 0.0, 0.0)
- **Sommet bas-gauche** : Vert (0.0, 1.0, 0.0)
- **Sommet bas-droit** : Bleu (0.0, 0.0, 1.0)

L'interpolation matérielle OpenGL crée un dégradé de couleurs entre les sommets.

## Fichiers

### main.cpp

Structure du code (environ 600+ lignes) :

1. **Shaders communs** : Vertex et Fragment shaders compatibles OpenGL ES 2.0
2. **Données de vertices** : Positions (x, y) + Couleurs (r, g, b)
3. **Section Android** : `#if defined(__ANDROID__)`
   - EGL initialization
   - NativeActivity event loop
   - Touch input handling
4. **Section Windows** : `#elif defined(_WIN32)`
   - Win32 window creation
   - WGL context setup
   - Message pump
5. **Section Web** : `#elif defined(__EMSCRIPTEN__)`
   - Canvas setup
   - Emscripten main loop
   - Keyboard callbacks
6. **Section Linux** : `#elif defined(__linux__)`
   - X11 window creation
   - GLX context
   - X11 event loop

### 25_opengl_triangle.jenga

Configuration DSL Jenga avec :
- 4 target OS : Windows, Linux, Android, Web
- Toolchains spécifiques par plateforme
- Linking des bibliothèques OpenGL natives
- Définition de macros de plateforme (`PLATFORM_WINDOWS`, etc.)

## Compilation

### Build pour toutes les plateformes

```bash
jenga build --platform jengaall
```

### Build par plateforme

```bash
# Windows (depuis Windows)
jenga build --platform windows-x64-mingw

# Linux (cross-compile avec Zig depuis Windows)
jenga build --platform linux-x64-gcc

# Android (génère APK)
jenga build --platform android-arm64-ndk

# Web (génère .wasm + .html)
jenga build --platform web-wasm32-emscripten
```

### Build avec configuration

```bash
jenga build --config Release --platform windows-x64-mingw
```

## Exécution

### Windows
```bash
./Build/Bin/Debug-Windows/GLTriangle/GLTriangle.exe
```

### Linux
```bash
./Build/Bin/Debug-Linux/GLTriangle/GLTriangle
```

### Android
```bash
# Déployer sur appareil connecté
jenga deploy --platform android
# Ou installer manuellement
adb install Build/Bin/Debug-Android/GLTriangle/GLTriangle.apk
```

### Web
```bash
# Ouvrir dans navigateur
firefox Build/Bin/Debug-Web/GLTriangle/GLTriangle.html
# Ou serveur HTTP local
python -m http.server 8000 -d Build/Bin/Debug-Web/GLTriangle/
# Puis http://localhost:8000/GLTriangle.html
```

## Contrôles

- **Toutes plateformes** : La fenêtre affiche un triangle coloré
- **Android** : Touch pour fermer (optionnel selon implémentation)
- **Web** : ESC pour fermer/reload
- **Windows/Linux** : Fermeture de fenêtre standard ou ESC

## Points clés

### Shaders portables

Les shaders utilisent la syntaxe **OpenGL ES 2.0** compatible avec :
- OpenGL 2.0+ (desktop)
- OpenGL ES 2.0/3.0 (mobile)
- WebGL 1.0/2.0 (web)

```glsl
// Vertex Shader
attribute vec2 aPos;
attribute vec3 aColor;
varying vec3 vColor;
void main() {
    gl_Position = vec4(aPos, 0.0, 1.0);
    vColor = aColor;
}

// Fragment Shader
precision mediump float;
varying vec3 vColor;
void main() {
    gl_FragColor = vec4(vColor, 1.0);
}
```

### Données de vertices

Format interleaved : `x, y, r, g, b` (5 floats par vertex)

```cpp
static const float kTriangle[] = {
     0.0f,  0.6f,   1.0f, 0.0f, 0.0f,   // rouge
    -0.6f, -0.4f,   0.0f, 1.0f, 0.0f,   // vert
     0.6f, -0.4f,   0.0f, 0.0f, 1.0f,   // bleu
};
```

### Compilation conditionnelle

Le code utilise des macros de plateforme :

```cpp
#if defined(__ANDROID__)
    // Code Android (EGL, NativeActivity)
#elif defined(_WIN32)
    // Code Windows (Win32, WGL)
#elif defined(__EMSCRIPTEN__)
    // Code Web (Canvas, WebGL)
#elif defined(__linux__)
    // Code Linux (X11, GLX)
#endif
```

### Bibliothèques requises

- **Windows** : `opengl32.lib`, `gdi32.lib`, `user32.lib`
- **Linux** : `libGL.so`, `libX11.so`
- **Android** : `libEGL.so`, `libGLESv3.so`, `libandroid.so`, `liblog.so`
- **Web** : Aucune (gérées par Emscripten)

## Concepts OpenGL démontrés

1. **Vertex Buffer Object (VBO)** : Stockage GPU des vertices
2. **Vertex Array Object (VAO)** : Configuration des attributs de vertices
3. **Shaders** : Programmation GPU (vertex + fragment)
4. **Attributes** : Passing de données par vertex (position, couleur)
5. **Varyings** : Interpolation automatique entre vertex et fragment shader
6. **Clear color** : Background noir
7. **Draw call** : `glDrawArrays(GL_TRIANGLES, 0, 3)`

## Prérequis par plateforme

### Windows
- Visual Studio ou MinGW-w64 avec OpenGL headers
- Drivers graphiques avec OpenGL 2.0+ support

### Linux
- Paquets requis :
  ```bash
  sudo apt install libgl1-mesa-dev libx11-dev
  ```
- Zig pour cross-compilation (voir exemple 21)

### Android
- Android SDK (`ANDROID_SDK_ROOT` env variable)
- Android NDK (`ANDROID_NDK_ROOT` env variable)
- Appareil ou émulateur avec OpenGL ES 3.0

### Web
- Emscripten SDK installed et configuré
- Navigateur moderne avec WebGL support

## Dépannage

**Fenêtre noire (pas de triangle)** :
- Vérifiez que les shaders compilent sans erreur (logs OpenGL)
- Vérifiez que le VBO et VAO sont correctement créés
- Sur Android : Vérifiez les logs `adb logcat | grep GL`

**Erreur de linking OpenGL** :
- Windows : Vérifiez que `opengl32.lib` est trouvé
- Linux : Installez `libgl1-mesa-dev`
- Android : Vérifiez NDK version >= r21

**Couleurs incorrectes** :
- Vérifiez l'ordre des composantes RGB dans kTriangle[]
- Vérifiez la configuration des attributs (stride = 5 * sizeof(float))

**Crash au démarrage (Android)** :
- Vérifiez MinSDK (24+) dans le manifest
- Vérifiez que NativeActivity est correctement configurée
- Logs : `adb logcat -s DEBUG:* AndroidRuntime:*`

**Page blanche (Web)** :
- Ouvrez la console navigateur (F12) pour voir les erreurs
- Servez depuis un serveur HTTP (pas file://)
- Vérifiez que le .wasm se charge correctement

## Optimisations possibles

- **Textures** : Ajouter texture mapping
- **Rotation** : Animer le triangle avec matrices de transformation
- **Multiple triangles** : Rendre plusieurs objets
- **Depth testing** : Ajouter `glEnable(GL_DEPTH_TEST)` pour 3D
- **Lighting** : Calculer illumination dans les shaders
- **Responsive** : Adapter au redimensionnement de fenêtre

## Étapes suivantes

Après cet exemple, explorez :
- **OpenGL avancé** : Textures, matrices, lighting, 3D
- **22_nk_multiplatform_sandbox** : Framework complet multi-plateformes
- **27_nk_window** : Abstraction de fenêtrage multi-plateformes
- Intégrez **ImGui** ou **Dear ImGui** pour une UI rapide

## Ressources

- [OpenGL ES 2.0 Reference](https://www.khronos.org/opengles/sdk/docs/man/)
- [WebGL Fundamentals](https://webglfundamentals.org/)
- [Learn OpenGL](https://learnopengl.com/)
- [Android NDK OpenGL ES Guide](https://developer.android.com/guide/topics/graphics/opengl)
