# Camera WSL2 (Windows + Ubuntu) - Guide complet

Ce document explique comment rendre la camera visible pour:

- `SandboxCamera`
- `SandboxCameraFull`

dans `Jenga/Exemples/27_nk_window` quand vous travaillez sous WSL2.

## 1. Pourquoi "No camera device found"

Le backend Linux de `NKWindow` utilise V4L2 et cherche des devices:

- `/dev/video0`
- `/dev/video1`
- etc.

Si ces fichiers n'existent pas, l'enumeration retourne 0 camera.

## 2. Cas actuel: `usbipd` non reconnu dans PowerShell

Apres `winget install dorssel.usbipd-win`, il faut souvent:

1. Fermer PowerShell
2. Ouvrir un nouveau PowerShell (de preference en Administrateur)

Puis tester:

```powershell
usbipd list
```

Si la commande n'est toujours pas reconnue, utilisez le chemin complet:

```powershell
& "C:\Program Files\usbipd-win\usbipd.exe" list
```

Option session courante seulement (sans redemarrage):

```powershell
$env:Path += ";C:\Program Files\usbipd-win"
usbipd list
```

## 3. Attacher une camera USB a WSL2

### 3.1 Cote Windows (PowerShell Admin)

Lister les peripheriques USB:

```powershell
usbipd list
```

Reperez le `BUSID` de la webcam, puis:

```powershell
usbipd bind --busid <BUSID>
usbipd attach --wsl --busid <BUSID>
```

Exemple:

```powershell
usbipd bind --busid 2-4
usbipd attach --wsl --busid 2-4
```

## 4. Verifier cote Ubuntu (WSL)

Installer outils de diagnostic:

```bash
sudo apt update
sudo apt install -y v4l-utils x11-utils ffmpeg
```

Paquets installes:

- `v4l-utils`: commandes V4L2 (`v4l2-ctl`)
- `x11-utils`: outils X11 (`xev`, `xwininfo`, etc.)
- `ffmpeg`: enregistrement vidéo (`R`) en mode vidéo

Verifier la camera:

```bash
ls -l /dev/video*
v4l2-ctl --list-devices
```

Verifier le groupe:

```bash
id -nG | tr ' ' '\n' | rg '^video$' || true
```

Si vous venez d'ajouter l'utilisateur au groupe `video`, reconnectez la session.

Verifier clavier X11 (utile pour la touche `Espace` dans les demos):

```bash
xev -event keyboard
```

Dans la fenetre `xev`, appuyer `Espace` doit afficher:

- `KeyPress ... keysym ... space`
- `KeyRelease ... keysym ... space`

## 5. Lancer les exemples camera

Depuis:

`Jenga/Exemples/27_nk_window`

```bash
python3 ../../jenga.py build --no-daemon --jenga-file 27_nk_window.jenga --platform Linux
./Build/Bin/Debug-Linux/SandboxCamera/SandboxCamera
./Build/Bin/Debug-Linux/SandboxCameraFull/SandboxCameraFull
```

## 6. Diagnostic rapide si ca ne marche pas

1. `usbipd list` ne montre aucune webcam:
- webcam interne non exportable vers WSL sur certaines machines
- ou webcam deja capturee par Windows (application ouverte)

2. `usbipd attach` echoue:
- relancer PowerShell en admin
- refaire `bind` puis `attach`

3. Pas de `/dev/video*` dans WSL:
- camera non attachee a WSL
- module V4L2 non charge (rare)

Tester:

```bash
sudo modprobe videodev
sudo modprobe uvcvideo
ls -l /dev/video*
```

4. Camera visible mais app indique toujours erreur:
- verifier permissions (`video`)
- verifier qu'une autre app n'utilise pas deja la camera
- tester avec `v4l2-ctl --list-formats-ext -d /dev/video0`

5. `/dev/video*` existe mais aucun frame n'arrive (fichier stream a 0 octet):

```bash
v4l2-ctl -d /dev/video0 --stream-mmap=4 --stream-count=60 --stream-to=/tmp/cam.raw --verbose
ls -lh /tmp/cam.raw
```

Si `/tmp/cam.raw` reste a `0` octet, le device est ouvert mais aucun paquet video n'arrive.
Ce cas signifie generalement un probleme de transport webcam via WSL2/usbip (pas un bug Jenga).

Actions recommandees:
- fermer toute application Windows qui utilise la webcam (Teams, Camera, navigateur, etc.),
- re-attacher le peripherique avec `usbipd bind` + `usbipd attach --wsl`,
- tester en forçant un format:
```bash
v4l2-ctl -d /dev/video0 --set-fmt-video=width=640,height=480,pixelformat=MJPG --stream-mmap=4 --stream-count=120 --stream-to=/tmp/cam.mjpg --verbose
```
- si toujours 0 octet: executer l'exemple en natif Windows (`--platform Windows`) pour valider la webcam.

## 7. Limite importante WSL2

Certaines webcams integrees laptop ne sont pas bien exposees a WSL2 selon modele/driver.

Si `usbipd` ne propose pas la webcam, que `/dev/video*` n'apparait jamais, ou que le stream reste a `0` octet, la solution la plus fiable est:

- compiler et executer l'exemple en natif Windows (`--platform Windows`)

Le projet dispose d'un backend camera Win32 dedie.

## 8. Check-list minimale

1. `usbipd list` fonctionne dans PowerShell.
2. La webcam est `bind` + `attach --wsl`.
3. Dans WSL: `ls /dev/video*` retourne au moins `video0`.
4. `v4l2-ctl --list-devices` voit la camera.
5. `SandboxCamera` ne log plus `No camera device found`.

## 9. Comportement attendu des demos camera

### SandboxCamera

- Affiche le flux camera dans la fenetre.
- `Espace` capture une photo sur disque et affiche une miniature temporaire (coin haut droit).
- `R` démarre/arrête l’enregistrement.
- `M` bascule le mode d’enregistrement:
  - `AUTO`: vidéo si codec/ffmpeg dispo, sinon fallback image-par-image.
  - `VIDEO_ONLY`: force vidéo, échoue si codec/ffmpeg indisponible.
  - `MANUAL` (`IMAGE_SEQUENCE_ONLY`): force image-par-image (`*_frames/frame_000001.jpg|ppm`).

### SandboxCameraFull

- Demarre en mode preview camera.
- `V` bascule preview camera <-> monde virtuel.
- `Espace` capture une photo sur disque + miniature temporaire.
- `R` démarre/arrête l’enregistrement.
- `M` bascule `AUTO`/`VIDEO_ONLY`/`MANUAL` (même logique que `SandboxCamera`).

### Tracking "physique" (IMU)

Le tracking mouvement physique -> camera virtuelle depend d'un capteur orientation/IMU.

- Sur mobile/tablette: normal.
- Sur laptop/desktop + webcam USB: generalement indisponible.

Donc absence de tracking IMU sur PC est normale.
