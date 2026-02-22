#pragma once

// =============================================================================
// NkWindowConfig.h
// Configuration de création de fenêtre + Safe Area pour mobile.
// =============================================================================

#include "NkTypes.h"
#include <string>

namespace nkentseu
{

// ---------------------------------------------------------------------------
// NkSafeAreaInsets — marges de zone sécurisée (notch, barre système…)
// Sur desktop : toutes les valeurs sont 0.
// Sur mobile   : renseignées par la plateforme via ISafeAreaProvider.
// ---------------------------------------------------------------------------

struct NkSafeAreaInsets
{
    float top    = 0.f;  ///< Notch / Dynamic Island / barre de statut
    float bottom = 0.f;  ///< Barre de navigation / home indicator
    float left   = 0.f;  ///< Découpe latérale (rare)
    float right  = 0.f;  ///< Découpe latérale (rare)

    /// Applique les marges à un rect {x,y,w,h} et retourne le rect sécurisé.
    NkRect Apply(NkRect r) const
    {
        NkI32 t = static_cast<NkI32>(top);
        NkI32 b = static_cast<NkI32>(bottom);
        NkI32 l = static_cast<NkI32>(left);
        NkI32 ri= static_cast<NkI32>(right);
        r.x      += l;
        r.y      += t;
        r.width   = (r.width  > static_cast<NkU32>(l + ri)) ? r.width  - static_cast<NkU32>(l + ri)  : 0;
        r.height  = (r.height > static_cast<NkU32>(t + b))  ? r.height - static_cast<NkU32>(t + b) : 0;
        return r;
    }

    bool IsZero() const { return top==0.f && bottom==0.f && left==0.f && right==0.f; }
};

// ---------------------------------------------------------------------------
// NkWindowConfig
// ---------------------------------------------------------------------------

struct NkWindowConfig
{
    // --- Position et taille ---
    NkI32  x         = 100;
    NkI32  y         = 100;
    NkU32  width     = 1280;
    NkU32  height    = 720;
    NkU32  minWidth  = 160;
    NkU32  minHeight = 90;
    NkU32  maxWidth  = 0xFFFF;
    NkU32  maxHeight = 0xFFFF;

    // --- Comportement ---
    bool   centered      = true;
    bool   resizable     = true;
    bool   movable       = true;
    bool   closable      = true;
    bool   minimizable   = true;
    bool   maximizable   = true;
    bool   canFullscreen = true;
    bool   fullscreen    = false;
    bool   modal         = false;
    bool   vsync         = true;

    // --- Apparence ---
    bool        frame       = true;
    bool        hasShadow   = true;
    bool        transparent = false;
    bool        visible     = true;
    NkU32       bgColor     = 0x141414FF;

    // --- Identité ---
    std::string title    = "NkWindow";
    std::string name     = "NkApp";
    std::string iconPath;

    // --- Mobile / Safe Area ---
    // Si true : le renderer recevra les insets via Window::GetSafeAreaInsets().
    // Sur desktop : sans effet.
    bool respectSafeArea = true;
};

} // namespace nkentseu
