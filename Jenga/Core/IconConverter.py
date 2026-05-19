#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IconConverter.py
================
Module utilitaire pour la gestion des icones d'application multi-plateformes.

Responsabilites :
  - Detecter le format d'une icone (PNG, JPG, ICO, ICNS, dossier mipmap-*,
    dossier .iconset, dossier AppIcon.appiconset).
  - Determiner quelles plateformes peuvent consommer un format donne.
  - Convertir un PNG (format universel) vers les formats natifs :
      * Windows : .ico multi-tailles
      * macOS   : .icns multi-tailles
      * Android : hierarchie res/mipmap-* (ldpi..xxxhdpi)
      * Web     : favicon.ico + favicon-*.png + manifest icons
  - Resoudre l'icone effective pour une plateforme : override specifique
    > appIcon generique > None.

Dependance : Pillow (PIL) >= 10.0. Si absent, on logue un warning et on
retombe sur les formats natifs uniquement (pas de conversion auto).

Convention :
  - PNG / JPG -> dispatch vers TOUTES les plateformes (convertibles).
  - ICO       -> Windows uniquement.
  - ICNS      -> macOS uniquement.
  - SVG       -> non supporte pour l'instant (a venir via rasterisation).
  - mipmap-*/ -> Android uniquement.
  - .iconset/ -> macOS uniquement.
  - AppIcon.appiconset/ -> iOS uniquement.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Set, List, Dict
import shutil
import struct

# ─────────────────────────────────────────────────────────────────────────────
# Pillow detection (soft import) — on permet a jenga de tourner sans Pillow
# pour les projets qui ne configurent pas d'icone, mais on logue un warning
# clair si une icone PNG est demandee sans Pillow installe.
# ─────────────────────────────────────────────────────────────────────────────
try:
    from PIL import Image  # type: ignore
    _PILLOW_OK = True
except ImportError:
    Image = None  # type: ignore
    _PILLOW_OK = False


def HasPillow() -> bool:
    """Indique si Pillow est disponible (pour conversion PNG -> formats natifs)."""
    return _PILLOW_OK


# ─────────────────────────────────────────────────────────────────────────────
# Format detection
# ─────────────────────────────────────────────────────────────────────────────
# Cles canoniques retournees par DetectIconFormat. Permet aux builders de
# faire un dispatch lisible sans dependre des extensions.
FORMAT_PNG              = "png"
FORMAT_JPG              = "jpg"
FORMAT_ICO              = "ico"
FORMAT_ICNS             = "icns"
FORMAT_SVG              = "svg"
FORMAT_MIPMAP_DIR       = "mipmap-dir"      # dossier contenant res/mipmap-*/
FORMAT_ICONSET_DIR      = "iconset-dir"     # dossier .iconset (Apple)
FORMAT_APPICONSET_DIR   = "appiconset-dir"  # dossier AppIcon.appiconset (iOS)
FORMAT_UNKNOWN          = "unknown"


def DetectIconFormat(path: Path) -> str:
    """
    Detecte le format d'une icone par extension / contenu de dossier.
    Retourne une des constantes FORMAT_* ci-dessus.
    """
    p = Path(path)
    if p.is_dir():
        # Format dossier : on inspecte le nom et le contenu.
        name = p.name.lower()
        if name.endswith(".appiconset"):
            return FORMAT_APPICONSET_DIR
        if name.endswith(".iconset"):
            return FORMAT_ICONSET_DIR
        # Dossier res/ Android : doit contenir au moins un sous-dossier mipmap-*
        for child in p.iterdir():
            if child.is_dir() and child.name.startswith("mipmap-"):
                return FORMAT_MIPMAP_DIR
        # Si on tombe sur un dossier mipmap-* direct (sans wrapper res/), on
        # le considere aussi comme mipmap-dir, par convention.
        if name.startswith("mipmap-"):
            return FORMAT_MIPMAP_DIR
        return FORMAT_UNKNOWN

    ext = p.suffix.lower()
    if ext == ".png":  return FORMAT_PNG
    if ext in (".jpg", ".jpeg"): return FORMAT_JPG
    if ext == ".ico":  return FORMAT_ICO
    if ext == ".icns": return FORMAT_ICNS
    if ext == ".svg":  return FORMAT_SVG
    return FORMAT_UNKNOWN


# ─────────────────────────────────────────────────────────────────────────────
# Compatibilite format <-> plateforme
# ─────────────────────────────────────────────────────────────────────────────
# Plateformes connues. Le nom est aligne avec le filter system: (lowercase).
PLATFORM_ANDROID = "android"
PLATFORM_WINDOWS = "windows"
PLATFORM_MACOS   = "macos"
PLATFORM_IOS     = "ios"
PLATFORM_WEB     = "web"

ALL_PLATFORMS: Set[str] = {
    PLATFORM_ANDROID, PLATFORM_WINDOWS, PLATFORM_MACOS, PLATFORM_IOS, PLATFORM_WEB
}


def GetCompatiblePlatforms(path: Path) -> Set[str]:
    """
    Retourne l'ensemble des plateformes qui peuvent consommer ce fichier d'icone.

    Regle :
      - PNG / JPG : universel (5 plateformes) -- jenga convertit en interne.
      - ICO       : Windows uniquement.
      - ICNS      : macOS uniquement.
      - mipmap-dir: Android uniquement.
      - iconset   : macOS uniquement.
      - appiconset: iOS uniquement.
      - SVG       : (vide pour l'instant) -- a rasteriser plus tard.
      - inconnu   : (vide).
    """
    fmt = DetectIconFormat(path)
    if fmt in (FORMAT_PNG, FORMAT_JPG):
        return set(ALL_PLATFORMS)
    if fmt == FORMAT_ICO:              return {PLATFORM_WINDOWS}
    if fmt == FORMAT_ICNS:             return {PLATFORM_MACOS}
    if fmt == FORMAT_MIPMAP_DIR:       return {PLATFORM_ANDROID}
    if fmt == FORMAT_ICONSET_DIR:      return {PLATFORM_MACOS}
    if fmt == FORMAT_APPICONSET_DIR:   return {PLATFORM_IOS}
    return set()


def IsCompatible(path: Path, platform: str) -> bool:
    """Helper : true si `path` peut etre utilise pour `platform`."""
    return platform in GetCompatiblePlatforms(path)


# ─────────────────────────────────────────────────────────────────────────────
# Resolution per-project : override specifique > appIcon generique > None
# ─────────────────────────────────────────────────────────────────────────────
def ResolveIconFor(project, platform: str) -> Optional[str]:
    """
    Determine quelle icone utiliser pour `platform` (chaine en minuscule, ex:
    'android', 'windows', ...). Retourne le chemin (string) ou None si aucune
    icone n'est applicable.

    Ordre de priorite :
      1. Override specifique du projet (project.androidAppIcon, etc.).
      2. project.appIcon (generique), seulement si son format est compatible
         avec la plateforme cible.
      3. None.

    Le projet n'est pas type ici (dependance circulaire avec Api.py). On
    accede aux attributs via getattr defensif.
    """
    # Mapping plateforme -> nom d'attribut specifique sur le Project.
    specific_attr = {
        PLATFORM_ANDROID: "androidAppIcon",
        PLATFORM_WINDOWS: "windowsIcon",
        PLATFORM_MACOS:   "macosIcon",
        PLATFORM_IOS:     "iosAppIcon",
        PLATFORM_WEB:     "webFavicon",
    }.get(platform)

    if specific_attr is not None:
        specific = getattr(project, specific_attr, "") or ""
        if specific:
            return specific

    # Fallback : appIcon generique, mais on filtre par compatibilite.
    generic = getattr(project, "appIcon", "") or ""
    if not generic:
        return None
    if not IsCompatible(Path(generic), platform):
        # L'utilisateur a passe un format specifique a une autre plateforme
        # (ex: .ico) -- on ne l'applique pas a celle-ci.
        return None
    return generic


# ─────────────────────────────────────────────────────────────────────────────
# Convertisseurs PNG -> formats natifs
# ─────────────────────────────────────────────────────────────────────────────
def _LoadAndNormalizePng(src: Path):
    """
    Charge un PNG via Pillow et le convertit en RGBA carre si necessaire.
    Retourne un objet PIL.Image (ou leve si Pillow absent).
    """
    if not _PILLOW_OK:
        raise RuntimeError(
            "Pillow n'est pas installe. Installer via: pip install Pillow"
        )
    img = Image.open(src).convert("RGBA")
    # Si l'image n'est pas carree, on la pad en transparent pour eviter les
    # deformations a la conversion vers mipmap/.ico/.icns.
    w, h = img.size
    if w != h:
        side = max(w, h)
        square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        square.paste(img, ((side - w) // 2, (side - h) // 2))
        return square
    return img


def ConvertPngToIco(src: Path, dst: Path,
                    sizes: Optional[List[int]] = None) -> bool:
    """
    Convertit un PNG en .ico multi-tailles pour Windows.
    Tailles par defaut : 16, 24, 32, 48, 64, 128, 256.
    Retourne True si OK, False sinon.
    """
    if not _PILLOW_OK:
        return False
    sizes = sizes or [16, 24, 32, 48, 64, 128, 256]
    try:
        img = _LoadAndNormalizePng(src)
        dst.parent.mkdir(parents=True, exist_ok=True)
        # Pillow gere le format ICO multi-tailles via le param sizes.
        img.save(dst, format="ICO", sizes=[(s, s) for s in sizes])
        return True
    except Exception:
        return False


def ConvertPngToIcns(src: Path, dst: Path) -> bool:
    """
    Convertit un PNG en .icns multi-tailles pour macOS.
    Pillow supporte le format ICNS depuis 9.5. Si echec, on fallback sur
    une copie brute (Pillow ecrit un .icns minimal).
    """
    if not _PILLOW_OK:
        return False
    try:
        img = _LoadAndNormalizePng(src)
        dst.parent.mkdir(parents=True, exist_ok=True)
        # Pillow choisira les tailles supportees (16, 32, 64, 128, 256, 512, 1024).
        img.save(dst, format="ICNS")
        return True
    except Exception:
        return False


# Densites Android standards. Convention Google : 48dp = mdpi (1x = 48px).
# Sources : developer.android.com/training/multiscreen/screendensities
_ANDROID_MIPMAP_SIZES: Dict[str, int] = {
    "mipmap-ldpi":    36,   # 0.75x
    "mipmap-mdpi":    48,   # 1.0x  (base)
    "mipmap-hdpi":    72,   # 1.5x
    "mipmap-xhdpi":   96,   # 2.0x
    "mipmap-xxhdpi":  144,  # 3.0x
    "mipmap-xxxhdpi": 192,  # 4.0x
}


def GenerateAndroidMipmaps(src: Path, res_dir: Path,
                           icon_name: str = "ic_launcher") -> bool:
    """
    Genere la hierarchie complete res/mipmap-{ldpi..xxxhdpi}/ic_launcher.png
    a partir d'un PNG source (idealement >= 192x192). Pillow upscale/downscale
    en LANCZOS pour la qualite.

    Retourne True si toutes les densites ont ete ecrites.
    """
    if not _PILLOW_OK:
        return False
    try:
        img = _LoadAndNormalizePng(src)
        for folder, size in _ANDROID_MIPMAP_SIZES.items():
            mipmap_dir = res_dir / folder
            mipmap_dir.mkdir(parents=True, exist_ok=True)
            resized = img.resize((size, size), Image.LANCZOS)
            resized.save(mipmap_dir / f"{icon_name}.png", format="PNG")
        return True
    except Exception:
        return False


def CopyAndroidMipmapsFromDir(src_dir: Path, res_dir: Path,
                              icon_name: str = "ic_launcher") -> bool:
    """
    L'utilisateur a fourni un dossier deja organise en mipmap-*/. On copie
    son contenu dans res_dir, en renommant l'icone en `icon_name`.
    Accepte soit src_dir = res/ (contenant mipmap-*/) soit src_dir = mipmap-* direct.
    """
    try:
        if src_dir.name.startswith("mipmap-"):
            # Cas direct : un seul dossier de densite. On le copie vers la meme
            # densite cible.
            (res_dir / src_dir.name).mkdir(parents=True, exist_ok=True)
            # On prend le premier PNG du dossier comme icone.
            for f in src_dir.iterdir():
                if f.suffix.lower() == ".png":
                    shutil.copy2(f, res_dir / src_dir.name / f"{icon_name}.png")
                    break
            return True
        # Cas wrapper : src_dir contient plusieurs mipmap-*/
        copied_any = False
        for d in src_dir.iterdir():
            if d.is_dir() and d.name.startswith("mipmap-"):
                (res_dir / d.name).mkdir(parents=True, exist_ok=True)
                for f in d.iterdir():
                    if f.suffix.lower() == ".png":
                        shutil.copy2(f, res_dir / d.name / f"{icon_name}.png")
                        copied_any = True
                        break
        return copied_any
    except Exception:
        return False


# Tailles favicon Web standards (favicon.ico = 16+32+48 multi-tailles, plus
# des PNG pour iOS touch icons et manifest.json).
_FAVICON_SIZES: List[int] = [16, 32, 48, 96, 180, 192, 512]


def GenerateFaviconSet(src: Path, dst_dir: Path) -> List[Path]:
    """
    Genere un set de favicons web :
      - favicon.ico (16+32+48)
      - favicon-16.png, favicon-32.png, favicon-180.png, favicon-192.png,
        favicon-512.png (apple-touch-icon + PWA)
    Retourne la liste des fichiers generes (chemins absolus).
    """
    if not _PILLOW_OK:
        return []
    out: List[Path] = []
    try:
        img = _LoadAndNormalizePng(src)
        dst_dir.mkdir(parents=True, exist_ok=True)

        # favicon.ico multi-tailles
        ico_path = dst_dir / "favicon.ico"
        img.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
        out.append(ico_path)

        # PNG variants
        for size in _FAVICON_SIZES:
            png_path = dst_dir / f"favicon-{size}.png"
            resized = img.resize((size, size), Image.LANCZOS)
            resized.save(png_path, format="PNG")
            out.append(png_path)
    except Exception:
        return []
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Helper de log centralise (les builders importent ce module et logent eux-memes
# si besoin -- pas de coupling avec Colored/Reporter ici pour eviter les
# dependances croisees).
# ─────────────────────────────────────────────────────────────────────────────
def DescribePlatformDispatch(generic_icon: Optional[str]) -> str:
    """
    Genere une chaine descriptive du dispatch d'une icone generique pour
    diagnostic dans les logs jenga.
    Exemple : "icon.png -> {android, windows, macos, ios, web}"
    """
    if not generic_icon:
        return "(aucune)"
    compat = GetCompatiblePlatforms(Path(generic_icon))
    if not compat:
        return f"{generic_icon} -> (format non supporte / non dispatche)"
    return f"{generic_icon} -> {{{', '.join(sorted(compat))}}}"
