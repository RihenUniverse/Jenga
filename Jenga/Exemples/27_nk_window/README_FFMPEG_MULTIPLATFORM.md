# FFmpeg - Installation Multi-plateforme

Ce guide couvre l'installation de FFmpeg pour les plateformes cibles de Jenga/NKWindow.

## Linux

### Ubuntu / Debian / WSL2
```bash
sudo apt update
sudo apt install -y ffmpeg
ffmpeg -version
```

### Fedora
```bash
sudo dnf install -y ffmpeg
ffmpeg -version
```

### Arch Linux
```bash
sudo pacman -S --noconfirm ffmpeg
ffmpeg -version
```

## macOS

### Homebrew
```bash
brew install ffmpeg
ffmpeg -version
```

### MacPorts
```bash
sudo port install ffmpeg
ffmpeg -version
```

## Windows

### winget (recommande)
```powershell
winget install --id Gyan.FFmpeg -e
ffmpeg -version
```

Si `ffmpeg` n'est pas reconnu immediatement, fermer/reouvrir le terminal.

### Chocolatey
```powershell
choco install ffmpeg -y
ffmpeg -version
```

## Android

Deux cas:

1. **Terminal Android (Termux)**: outil CLI local
```bash
pkg update
pkg install ffmpeg
ffmpeg -version
```

2. **Application Android (NDK/JNI)**: pas de ffmpeg systeme partage.
- Il faut embarquer des bibliotheques FFmpeg (`.so`) par ABI (`arm64-v8a`, etc.).
- Alternative recommandee pour une app camera Android: MediaCodec/MediaMuxer natifs.

## iOS

iOS n'a pas de `ffmpeg` systeme installable comme sur desktop.

- Pour l'application iOS, il faut embarquer FFmpeg en bibliotheque (build iOS specifique).
- Alternative recommandee pour capture/encodage camera: AVFoundation natif.
- Sur le Mac de developpement, vous pouvez installer l'outil CLI:
```bash
brew install ffmpeg
ffmpeg -version
```

## Emscripten (WebAssembly)

Le navigateur ne fournit pas un `ffmpeg` systeme.

Options:

1. **ffmpeg.wasm** (dans le navigateur)
```bash
npm install @ffmpeg/ffmpeg @ffmpeg/util
```

2. **Encodage cote serveur**
- Encoder avec FFmpeg natif sur un backend (Linux/Windows/macOS).
- Le client web envoie les frames/bruts, le serveur produit le MP4/WebM.

## Verification rapide

Apres installation sur plateforme desktop:
```bash
ffmpeg -version
```

Si la commande renvoie une version, `VIDEO_ONLY` pourra fonctionner dans `SandboxCamera`/`SandboxCameraFull`.
