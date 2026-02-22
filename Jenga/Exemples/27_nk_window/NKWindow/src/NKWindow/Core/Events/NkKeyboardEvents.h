#pragma once

// =============================================================================
// NkKeyboardEvents.h
// Données et classes d'événements clavier.
//
// Couvre :
//   NkKeyData        — touche physique pressée / relâchée / auto-repeat
//   NkTextInputData  — caractère Unicode produit (après traitement IME)
// =============================================================================

#include "NkEventTypes.h"
#include "NkScancode.h"
#include <string>

namespace nkentseu
{

// ===========================================================================
// NkKeyData — événement de touche physique
// ===========================================================================

struct NkKeyData
{
    static constexpr NkEventType TYPE = NkEventType::NK_KEY_PRESS;

    // --- Code logique (layout US-QWERTY invariant) ---------------------------
    NkKey           key       = NkKey::NK_UNKNOWN;
    ///< Identifie la POSITION de la touche (ex: NK_Q = touche en haut à gauche
    ///< des lettres sur un clavier US). Identique sur QWERTY/AZERTY/QWERTZ.
    ///< → Utiliser pour raccourcis clavier et contrôles de jeu.

    NkButtonState   state     = NkButtonState::NK_PRESSED;
    NkModifierState modifiers;

    // --- Code matériel (USB HID, layout-indépendant) -------------------------
    NkScancode scancode = NkScancode::NK_SC_UNKNOWN;
    ///< Code USB HID de la touche physique pressée.
    ///< Invariant quel que soit le layout clavier de l'utilisateur.
    ///< Sur AZERTY : appui touche physique 'A' → NK_SC_A (HID) mais NK_Q (logique).
    ///< → Utiliser pour enregistrement de macros et détection matérielle.

    // --- Code OS brut (non portable) ----------------------------------------
    NkU32 nativeKey = 0;
    ///< VK_* (Win32), KeySym (X11/XLib), keycode XCB, keyCode DOM...
    ///< Non portable entre plateformes. Utile pour débogage.

    // --- Flags ---------------------------------------------------------------
    bool  extended = false;
    ///< Touche étendue (bloc navigation, Numpad Enter, Numpad /).
    ///< Signification : préfixe E0 PS/2 / bit 24 LPARAM Win32.

    bool  repeat   = false;
    ///< true = touche maintenue, l'OS génère des répétitions.
    ///< L'état reste NK_PRESSED pour les répétitions (pas NK_RELEASED).

    NkKeyData() = default;
    NkKeyData(NkKey k, NkButtonState s, const NkModifierState& m,
              NkScancode sc = NkScancode::NK_SC_UNKNOWN,
              NkU32 native  = 0,
              bool ext = false, bool rep = false)
        : key(k), state(s), modifiers(m)
        , scancode(sc), nativeKey(native)
        , extended(ext), repeat(rep)
    {}

    // Commodités
    bool IsPress()   const { return state == NkButtonState::NK_PRESSED;  }
    bool IsRelease() const { return state == NkButtonState::NK_RELEASED; }
    bool IsRepeat()  const { return state == NkButtonState::NK_REPEAT;   }
    bool IsModifierKey() const { return NkKeyIsModifier(key); }

    std::string ToString() const
    {
        std::string s = "KeyEvent(";
        s += NkKeyToString(key);
        s += " [";
        s += NkScancodeToString(scancode);
        s += "], ";
        s += NkButtonStateToString(state);
        if (!modifiers.None()) { s += ", "; s += modifiers.ToString(); }
        if (repeat)   s += ", REPEAT";
        if (extended) s += ", EXTENDED";
        s += ")";
        return s;
    }
};

// ===========================================================================
// NkTextInputData — caractère Unicode produit (après IME)
// ===========================================================================

struct NkTextInputData
{
    static constexpr NkEventType TYPE = NkEventType::NK_TEXT_INPUT;

    NkU32 codepoint = 0;   ///< Code Unicode UTF-32
    char  utf8[5]   = {};  ///< Encodage UTF-8 du caractère (max 4 octets + '\0')

    NkTextInputData() = default;
    explicit NkTextInputData(NkU32 cp);

    // Construit depuis un code Unicode et encode en UTF-8
    static NkTextInputData FromCodepoint(NkU32 codepoint);

    bool IsPrintable() const { return codepoint >= 0x20 && codepoint != 0x7F; }
    bool IsAscii()     const { return codepoint < 0x80; }

    std::string ToString() const;
};

// ===========================================================================
// Implémentation inline de NkTextInputData
// ===========================================================================

inline NkTextInputData NkTextInputData::FromCodepoint(NkU32 cp)
{
    NkTextInputData d;
    d.codepoint = cp;

    // Encode en UTF-8
    if (cp < 0x80)
    {
        d.utf8[0] = static_cast<char>(cp);
    }
    else if (cp < 0x800)
    {
        d.utf8[0] = static_cast<char>(0xC0 | (cp >> 6));
        d.utf8[1] = static_cast<char>(0x80 | (cp & 0x3F));
    }
    else if (cp < 0x10000)
    {
        d.utf8[0] = static_cast<char>(0xE0 | (cp >> 12));
        d.utf8[1] = static_cast<char>(0x80 | ((cp >> 6) & 0x3F));
        d.utf8[2] = static_cast<char>(0x80 | (cp & 0x3F));
    }
    else if (cp < 0x110000)
    {
        d.utf8[0] = static_cast<char>(0xF0 | (cp >> 18));
        d.utf8[1] = static_cast<char>(0x80 | ((cp >> 12) & 0x3F));
        d.utf8[2] = static_cast<char>(0x80 | ((cp >> 6)  & 0x3F));
        d.utf8[3] = static_cast<char>(0x80 | (cp & 0x3F));
    }
    return d;
}

inline NkTextInputData::NkTextInputData(NkU32 cp)
    : NkTextInputData(NkTextInputData::FromCodepoint(cp))
{}

inline std::string NkTextInputData::ToString() const
{
    std::string s = "TextInput(U+";
    // hex
    char buf[16];
    snprintf(buf, sizeof(buf), "%04X", codepoint);
    s += buf;
    if (IsPrintable()) { s += " '"; s += utf8; s += "'"; }
    s += ")";
    return s;
}

} // namespace nkentseu
