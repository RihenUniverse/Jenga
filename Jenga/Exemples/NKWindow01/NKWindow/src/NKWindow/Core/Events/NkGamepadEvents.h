#pragma once

// =============================================================================
// NkGamepadEvents.h
// Données et classes d'événements manette / joystick.
//
// Couvre :
//   NkGamepadInfo           — informations sur la manette
//   NkGamepadConnectData    — connexion / déconnexion
//   NkGamepadButtonData     — bouton enfoncé / relâché
//   NkGamepadAxisData       — axe analogique modifié
//   NkGamepadStateData      — snapshot complet de l'état (polling)
//   NkGamepadRumbleData     — commande de vibration
// =============================================================================

#include "NkEventTypes.h"
#include <string>
#include <cstring>

namespace nkentseu
{

// ===========================================================================
// NkGamepadType — type de manette détecté
// ===========================================================================

enum class NkGamepadType : NkU32
{
    NK_GP_TYPE_UNKNOWN = 0,
    NK_GP_TYPE_XBOX,           ///< Xbox 360 / One / Series X|S
    NK_GP_TYPE_PLAYSTATION,    ///< DualShock 3/4, DualSense
    NK_GP_TYPE_NINTENDO,       ///< Joy-Con, Pro Controller, SNES classic
    NK_GP_TYPE_STEAM,          ///< Steam Controller
    NK_GP_TYPE_GENERIC,        ///< HID générique
    NK_GP_TYPE_MOBILE          ///< Manette mobile (iOS/Android MFi…)
};

// ===========================================================================
// NkGamepadVendor — fabricant identifié par USB VID
// ===========================================================================

struct NkGamepadVendor
{
    NkU16 vendorId  = 0;
    NkU16 productId = 0;
    char  name[64]  = {};   ///< Nom du produit (ex : "Xbox Wireless Controller")
};

// ===========================================================================
// NkGamepadInfo — métadonnées de la manette
// ===========================================================================

struct NkGamepadInfo
{
    NkU32          index     = 0;        ///< Indice de manette (0 = joueur 1…)
    char           id[128]   = {};       ///< Identifiant opaque (GUID ou chemin)
    NkGamepadType  type      = NkGamepadType::NK_GP_TYPE_UNKNOWN;
    NkGamepadVendor vendor;

    // Capacités
    NkU32 numButtons = 0;
    NkU32 numAxes    = 0;
    bool  hasRumble  = false;  ///< Vibration moteurs
    bool  hasTriggerRumble = false; ///< Vibration dans les gâchettes (DualSense, Elite)
    bool  hasTouchpad = false;      ///< Pavé tactile intégré
    bool  hasGyro     = false;      ///< Gyroscope / accéléromètre
    bool  hasLED      = false;      ///< LED de couleur programmable

    // Niveau de batterie [0,1] ou -1 si câblé / inconnu
    float batteryLevel = -1.f;
};

// ===========================================================================
// NkGamepadConnectData — connexion / déconnexion
// ===========================================================================

struct NkGamepadConnectData
{
    static constexpr NkEventType TYPE = NkEventType::NK_GAMEPAD_CONNECT;

    bool         connected = false;
    NkGamepadInfo info;

    NkGamepadConnectData() = default;
    NkGamepadConnectData(bool c, const NkGamepadInfo& i) : connected(c), info(i) {}

    std::string ToString() const
    {
        return std::string(connected ? "GamepadConnect" : "GamepadDisconnect")
             + "(idx=" + std::to_string(info.index)
             + " \"" + info.id + "\")";
    }
};

// ===========================================================================
// NkGamepadButtonData — bouton enfoncé / relâché
// ===========================================================================

struct NkGamepadButtonData
{
    static constexpr NkEventType TYPE = NkEventType::NK_GAMEPAD_BUTTON_PRESS;

    NkU32           gamepadIndex = 0;
    NkGamepadButton button       = NkGamepadButton::NK_GP_UNKNOWN;
    NkButtonState   state        = NkButtonState::NK_PRESSED;

    // Valeur analogique si applicable (ex : gâchette digitale), [0,1]
    float analogValue = 0.f;

    NkGamepadButtonData() = default;
    NkGamepadButtonData(NkU32 idx, NkGamepadButton btn, NkButtonState st, float av = 0.f)
        : gamepadIndex(idx), button(btn), state(st), analogValue(av) {}

    bool IsPress()   const { return state == NkButtonState::NK_PRESSED;  }
    bool IsRelease() const { return state == NkButtonState::NK_RELEASED; }

    std::string ToString() const
    {
        return "GamepadButton(#" + std::to_string(gamepadIndex)
             + " " + NkGamepadButtonToString(button)
             + " " + NkButtonStateToString(state) + ")";
    }
};

// ===========================================================================
// NkGamepadAxisData — axe analogique modifié
// ===========================================================================

struct NkGamepadAxisData
{
    static constexpr NkEventType TYPE = NkEventType::NK_GAMEPAD_AXIS_MOVE;

    NkU32         gamepadIndex = 0;
    NkGamepadAxis axis         = NkGamepadAxis::NK_GP_AXIS_LX;
    float         value        = 0.f;  ///< Valeur courante ([-1,1] sticks, [0,1] gâchettes)
    float         prevValue    = 0.f;  ///< Valeur précédente
    float         delta        = 0.f;  ///< value - prevValue

    // Zone morte appliquée : en dessous, value est forcée à 0
    float deadzone = 0.05f;

    NkGamepadAxisData() = default;
    NkGamepadAxisData(NkU32 idx, NkGamepadAxis a, float v, float pv, float dz = 0.05f)
        : gamepadIndex(idx), axis(a), value(v), prevValue(pv)
        , delta(v - pv), deadzone(dz)
    {}

    bool IsInDeadzone() const { return value >= -deadzone && value <= deadzone; }

    std::string ToString() const
    {
        return "GamepadAxis(#" + std::to_string(gamepadIndex)
             + " " + NkGamepadAxisToString(axis)
             + " value=" + std::to_string(value)
             + " delta=" + std::to_string(delta) + ")";
    }
};

// ===========================================================================
// NkGamepadStateData — snapshot complet de l'état de la manette (pour le polling)
// ===========================================================================

struct NkGamepadStateData
{
    static constexpr NkEventType TYPE = NkEventType::NK_GAMEPAD_CONNECT; // reuse

    NkU32 gamepadIndex = 0;
    bool  connected    = false;

    // Boutons : tableau indexé par NkGamepadButton
    bool  buttons[static_cast<NkU32>(NkGamepadButton::NK_GAMEPAD_BUTTON_MAX)] = {};

    // Axes analogiques indexés par NkGamepadAxis
    float axes[static_cast<NkU32>(NkGamepadAxis::NK_GAMEPAD_AXIS_MAX)] = {};

    // Gyroscope [rad/s]
    float gyroX = 0.f, gyroY = 0.f, gyroZ = 0.f;
    // Accéléromètre [m/s²]
    float accelX = 0.f, accelY = 0.f, accelZ = 0.f;

    // Batterie
    float batteryLevel = -1.f;

    bool IsButtonDown(NkGamepadButton b) const
    {
        NkU32 idx = static_cast<NkU32>(b);
        return (idx < static_cast<NkU32>(NkGamepadButton::NK_GAMEPAD_BUTTON_MAX))
            && buttons[idx];
    }

    float GetAxis(NkGamepadAxis a) const
    {
        NkU32 idx = static_cast<NkU32>(a);
        return (idx < static_cast<NkU32>(NkGamepadAxis::NK_GAMEPAD_AXIS_MAX))
            ? axes[idx] : 0.f;
    }

    std::string ToString() const
    {
        return "GamepadState(#" + std::to_string(gamepadIndex)
             + (connected ? " connected)" : " disconnected)");
    }
};

// ===========================================================================
// NkGamepadRumbleData — commande de vibration (émise par l'application)
// ===========================================================================

struct NkGamepadRumbleData
{
    static constexpr NkEventType TYPE = NkEventType::NK_GAMEPAD_RUMBLE;

    NkU32 gamepadIndex  = 0;
    float motorLow      = 0.f;  ///< Moteur basse fréquence [0,1] (poignée gauche)
    float motorHigh     = 0.f;  ///< Moteur haute fréquence [0,1] (poignée droite)
    float triggerLeft   = 0.f;  ///< Vibration gâchette gauche [0,1] (DualSense / Elite)
    float triggerRight  = 0.f;  ///< Vibration gâchette droite [0,1]
    NkU32 durationMs    = 0;    ///< Durée [ms], 0 = jusqu'au prochain appel

    NkGamepadRumbleData() = default;
    NkGamepadRumbleData(NkU32 idx, float low, float high,
                        float tl = 0.f, float tr = 0.f, NkU32 dur = 0)
        : gamepadIndex(idx), motorLow(low), motorHigh(high)
        , triggerLeft(tl), triggerRight(tr), durationMs(dur)
    {}

    std::string ToString() const
    {
        return "GamepadRumble(#" + std::to_string(gamepadIndex)
             + " L=" + std::to_string(motorLow)
             + " R=" + std::to_string(motorHigh) + ")";
    }
};

} // namespace nkentseu
