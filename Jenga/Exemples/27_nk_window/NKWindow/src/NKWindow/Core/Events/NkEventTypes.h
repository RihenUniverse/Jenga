#pragma once

// =============================================================================
// NkEventTypes.h
// Énumérations fondamentales partagées par tout le système d'événements.
//
// Contient :
//   NkEventCategory  - catégories haut niveau
//   NkEventType      - tous les types d'événements
//   NkKey            - codes claviers cross-platform complets
//   NkButtonState    - état bouton (pressé / relâché / répété)
//   NkMouseButton    - boutons de la souris
//   NkGamepadButton  - boutons de manette
//   NkGamepadAxis    - axes de manette
//   NkTouchPhase     - phases tactiles
//   NkDropType       - types de drag & drop
// =============================================================================

#include "../NkTypes.h"

namespace nkentseu
{

// ===========================================================================
// NkEventCategory — masques de bits pour filtrer les événements
// ===========================================================================

enum class NkEventCategory : NkU32
{
    NK_CAT_NONE        = 0,
    NK_CAT_WINDOW      = (1u << 0),   ///< Événements fenêtre (create/close/resize…)
    NK_CAT_KEYBOARD    = (1u << 1),   ///< Clavier
    NK_CAT_MOUSE       = (1u << 2),   ///< Souris (position, boutons, roue, raw)
    NK_CAT_TOUCH       = (1u << 3),   ///< Tactile (multi-touch)
    NK_CAT_GAMEPAD     = (1u << 4),   ///< Manette / joystick
    NK_CAT_DROP        = (1u << 5),   ///< Drag & drop fichiers / texte
    NK_CAT_SYSTEM      = (1u << 6),   ///< Événements système (DPI, énergie, focus appli)
    NK_CAT_CUSTOM      = (1u << 7),   ///< Événements utilisateur personnalisés
    NK_CAT_ALL         = 0xFFFFFFFFu
};

inline NkEventCategory operator|(NkEventCategory a, NkEventCategory b)
{ return static_cast<NkEventCategory>(static_cast<NkU32>(a) | static_cast<NkU32>(b)); }
inline NkEventCategory operator&(NkEventCategory a, NkEventCategory b)
{ return static_cast<NkEventCategory>(static_cast<NkU32>(a) & static_cast<NkU32>(b)); }
inline bool NkCategoryHas(NkEventCategory set, NkEventCategory flag)
{ return (static_cast<NkU32>(set) & static_cast<NkU32>(flag)) != 0; }

// ===========================================================================
// NkEventType — identifiant précis de chaque événement
// ===========================================================================

enum class NkEventType : NkU32
{
    NK_NONE = 0,

    // ---[ FENÊTRE ]-----------------------------------------------------------
    NK_WINDOW_CREATE,         ///< Fenêtre créée (handle valide)
    NK_WINDOW_CLOSE,          ///< Demande de fermeture (croix, Alt+F4…)
    NK_WINDOW_DESTROY,        ///< Fenêtre détruite (handle libéré)
    NK_WINDOW_PAINT,          ///< Zone client à redessiner
    NK_WINDOW_RESIZE,         ///< Taille de la zone client modifiée
    NK_WINDOW_RESIZE_BEGIN,   ///< Début du redimensionnement (bouton souris appuyé)
    NK_WINDOW_RESIZE_END,     ///< Fin du redimensionnement (bouton souris relâché)
    NK_WINDOW_MOVE,           ///< Fenêtre déplacée
    NK_WINDOW_MOVE_BEGIN,     ///< Début du déplacement
    NK_WINDOW_MOVE_END,       ///< Fin du déplacement
    NK_WINDOW_FOCUS_GAINED,   ///< La fenêtre reçoit le focus clavier
    NK_WINDOW_FOCUS_LOST,     ///< La fenêtre perd le focus clavier
    NK_WINDOW_MINIMIZE,       ///< Fenêtre réduite en icône
    NK_WINDOW_MAXIMIZE,       ///< Fenêtre agrandie
    NK_WINDOW_RESTORE,        ///< Fenêtre restaurée depuis minimisée / maximisée
    NK_WINDOW_FULLSCREEN,     ///< Passage en plein écran
    NK_WINDOW_WINDOWED,       ///< Retour en mode fenêtré
    NK_WINDOW_DPI_CHANGE,     ///< Changement de facteur DPI (déplacement écran)
    NK_WINDOW_THEME_CHANGE,   ///< Changement de thème OS (clair ↔ sombre)
    NK_WINDOW_SHOWN,          ///< Fenêtre affichée (SetVisible(true))
    NK_WINDOW_HIDDEN,         ///< Fenêtre cachée (SetVisible(false))

    // ---[ CLAVIER ]-----------------------------------------------------------
    NK_KEY_PRESS,             ///< Touche enfoncée (première fois)
    NK_KEY_REPEAT,            ///< Touche maintenue (auto-repeat OS)
    NK_KEY_RELEASE,           ///< Touche relâchée
    NK_TEXT_INPUT,            ///< Caractère Unicode UTF-32 produit

    // ---[ SOURIS ]------------------------------------------------------------
    NK_MOUSE_MOVE,            ///< Curseur déplacé (coordonnées client)
    NK_MOUSE_RAW,             ///< Mouvement brut (sans accélération OS)
    NK_MOUSE_BUTTON_PRESS,    ///< Bouton souris enfoncé
    NK_MOUSE_BUTTON_RELEASE,  ///< Bouton souris relâché
    NK_MOUSE_DOUBLE_CLICK,    ///< Double-clic détecté
    NK_MOUSE_WHEEL_VERTICAL,  ///< Molette verticale
    NK_MOUSE_WHEEL_HORIZONTAL,///< Molette horizontale (Shift+molette / molette tiltable)
    NK_MOUSE_ENTER,           ///< Curseur entre dans la zone client
    NK_MOUSE_LEAVE,           ///< Curseur quitte la zone client
    NK_MOUSE_CAPTURE_BEGIN,   ///< SetCapture() activé
    NK_MOUSE_CAPTURE_END,     ///< SetCapture() relâché

    // ---[ TACTILE ]-----------------------------------------------------------
    NK_TOUCH_BEGIN,           ///< Nouveau(x) contact(s) posé(s)
    NK_TOUCH_MOVE,            ///< Contact(s) déplacé(s)
    NK_TOUCH_END,             ///< Contact(s) levé(s)
    NK_TOUCH_CANCEL,          ///< Contact(s) annulé(s) par le système
    NK_GESTURE_PINCH,         ///< Pincement (zoom) — 2 doigts
    NK_GESTURE_ROTATE,        ///< Rotation — 2 doigts
    NK_GESTURE_PAN,           ///< Panoramique — N doigts
    NK_GESTURE_SWIPE,         ///< Balayage rapide
    NK_GESTURE_TAP,           ///< Tape simple
    NK_GESTURE_LONG_PRESS,    ///< Appui long

    // ---[ MANETTE ]-----------------------------------------------------------
    NK_GAMEPAD_CONNECT,       ///< Manette branchée / détectée
    NK_GAMEPAD_DISCONNECT,    ///< Manette débranchée
    NK_GAMEPAD_BUTTON_PRESS,  ///< Bouton manette enfoncé
    NK_GAMEPAD_BUTTON_RELEASE,///< Bouton manette relâché
    NK_GAMEPAD_AXIS_MOVE,     ///< Axe analogique modifié (stick, gâchette)
    NK_GAMEPAD_RUMBLE,        ///< Retour haptique (informel — émis par l'app)

    // ---[ DRAG & DROP ]-------------------------------------------------------
    NK_DROP_ENTER,            ///< Objet glissé entre dans la fenêtre
    NK_DROP_OVER,             ///< Objet glissé survole la fenêtre
    NK_DROP_LEAVE,            ///< Objet glissé quitte la fenêtre sans lâcher
    NK_DROP_FILE,             ///< Fichier(s) lâché(s) sur la fenêtre
    NK_DROP_TEXT,             ///< Texte lâché sur la fenêtre
    NK_DROP_IMAGE,            ///< Image lâchée sur la fenêtre

    // ---[ SYSTÈME ]-----------------------------------------------------------
    NK_SYSTEM_POWER_SUSPEND,  ///< Système se met en veille
    NK_SYSTEM_POWER_RESUME,   ///< Système reprend (wake)
    NK_SYSTEM_LOW_MEMORY,     ///< Mémoire critique (Android/iOS)
    NK_SYSTEM_APP_PAUSE,      ///< Application mise en arrière-plan
    NK_SYSTEM_APP_RESUME,     ///< Application revenue au premier plan
    NK_SYSTEM_LOCALE_CHANGE,  ///< Changement de langue / région OS
    NK_SYSTEM_DISPLAY_CHANGE, ///< Moniteur ajouté / retiré / résolution changée

    // ---[ PERSONNALISÉ ]------------------------------------------------------
    NK_CUSTOM,                ///< Événement utilisateur (id libre ≥ NK_CUSTOM)

    NK_EVENT_TYPE_MAX
};

// Utilitaire : retourne la catégorie d'un type d'événement
NkEventCategory NkGetEventCategory(NkEventType type);

// Utilitaire : nom lisible du type
const char* NkEventTypeToString(NkEventType type);

// ===========================================================================
// NkKey — codes clavier uniformes cross-platform
// (Indépendants de la disposition physique — basés sur la position US-QWERTY)
// ===========================================================================

enum class NkKey : NkU32
{
    NK_UNKNOWN = 0,

    // ---[ Fonction ]----------------------------------------------------------
    NK_ESCAPE,
    NK_F1,  NK_F2,  NK_F3,  NK_F4,  NK_F5,  NK_F6,
    NK_F7,  NK_F8,  NK_F9,  NK_F10, NK_F11, NK_F12,
    NK_F13, NK_F14, NK_F15, NK_F16, NK_F17, NK_F18,
    NK_F19, NK_F20, NK_F21, NK_F22, NK_F23, NK_F24,

    // ---[ Chiffres ligne du haut ]--------------------------------------------
    NK_GRAVE,   ///< `~
    NK_NUM1,    ///< 1!
    NK_NUM2,    ///< 2@
    NK_NUM3,    ///< 3#
    NK_NUM4,    ///< 4$
    NK_NUM5,    ///< 5%
    NK_NUM6,    ///< 6^
    NK_NUM7,    ///< 7&
    NK_NUM8,    ///< 8*
    NK_NUM9,    ///< 9(
    NK_NUM0,    ///< 0)
    NK_MINUS,   ///< -_
    NK_EQUALS,  ///< =+
    NK_BACK,    ///< Retour arrière

    // ---[ Rangée QWERTY ]-----------------------------------------------------
    NK_TAB,
    NK_Q, NK_W, NK_E, NK_R, NK_T, NK_Y, NK_U, NK_I, NK_O, NK_P,
    NK_LBRACKET,  ///< [{
    NK_RBRACKET,  ///< ]}
    NK_BACKSLASH, ///< \|

    // ---[ Rangée ASDF ]-------------------------------------------------------
    NK_CAPSLOCK,
    NK_A, NK_S, NK_D, NK_F, NK_G, NK_H, NK_J, NK_K, NK_L,
    NK_SEMICOLON,  ///< ;:
    NK_APOSTROPHE, ///< '"
    NK_ENTER,

    // ---[ Rangée ZXCV ]-------------------------------------------------------
    NK_LSHIFT,
    NK_Z, NK_X, NK_C, NK_V, NK_B, NK_N, NK_M,
    NK_COMMA,   ///< ,<
    NK_PERIOD,  ///< .>
    NK_SLASH,   ///< /?
    NK_RSHIFT,

    // ---[ Rangée inférieure ]-------------------------------------------------
    NK_LCTRL,
    NK_LSUPER,  ///< Win (Windows) / Cmd (Apple) / Meta (Linux)
    NK_LALT,
    NK_SPACE,
    NK_RALT,    ///< AltGr sur claviers internationaux
    NK_RSUPER,
    NK_MENU,    ///< Touche application / menu contextuel
    NK_RCTRL,

    // ---[ Bloc navigation ]---------------------------------------------------
    NK_PRINT_SCREEN,
    NK_SCROLL_LOCK,
    NK_PAUSE_BREAK,
    NK_INSERT,
    NK_DELETE,
    NK_HOME,
    NK_END,
    NK_PAGE_UP,
    NK_PAGE_DOWN,

    // ---[ Flèches ]-----------------------------------------------------------
    NK_UP,
    NK_DOWN,
    NK_LEFT,
    NK_RIGHT,

    // ---[ Pavé numérique ]----------------------------------------------------
    NK_NUM_LOCK,
    NK_NUMPAD_DIV,    ///< /
    NK_NUMPAD_MUL,    ///< *
    NK_NUMPAD_SUB,    ///< -
    NK_NUMPAD_ADD,    ///< +
    NK_NUMPAD_ENTER,
    NK_NUMPAD_DOT,    ///< .
    NK_NUMPAD_0,
    NK_NUMPAD_1,
    NK_NUMPAD_2,
    NK_NUMPAD_3,
    NK_NUMPAD_4,
    NK_NUMPAD_5,
    NK_NUMPAD_6,
    NK_NUMPAD_7,
    NK_NUMPAD_8,
    NK_NUMPAD_9,
    NK_NUMPAD_EQUALS, ///< = (Mac)

    // ---[ Touches médias ]----------------------------------------------------
    NK_MEDIA_PLAY_PAUSE,
    NK_MEDIA_STOP,
    NK_MEDIA_NEXT,
    NK_MEDIA_PREV,
    NK_MEDIA_VOLUME_UP,
    NK_MEDIA_VOLUME_DOWN,
    NK_MEDIA_MUTE,

    // ---[ Touches navigateur / appli ]----------------------------------------
    NK_BROWSER_BACK,
    NK_BROWSER_FORWARD,
    NK_BROWSER_REFRESH,
    NK_BROWSER_HOME,
    NK_BROWSER_SEARCH,
    NK_BROWSER_FAVORITES,

    // ---[ Touches internationales / IME ]-------------------------------------
    NK_KANA,       ///< Japonais
    NK_KANJI,      ///< Japonais
    NK_CONVERT,    ///< Japonais
    NK_NONCONVERT, ///< Japonais
    NK_HANGUL,     ///< Coréen
    NK_HANJA,      ///< Coréen

    // ---[ Touches additionnelles ]--------------------------------------------
    NK_SLEEP,
    NK_CLEAR,      ///< NumPad 5 sans NumLock
    NK_SEPARATOR,  ///< Séparateur de pavé numérique (,)
    NK_OEM_1,      ///< Touches OEM supplémentaires (usage constructeur)
    NK_OEM_2,
    NK_OEM_3,
    NK_OEM_4,
    NK_OEM_5,
    NK_OEM_6,
    NK_OEM_7,
    NK_OEM_8,

    NK_KEY_MAX
};

// Retourne le nom lisible de la touche ("SPACE", "F1", "A"…)
const char* NkKeyToString(NkKey key);

// Retourne true si la touche est un modificateur (Ctrl/Alt/Shift/Super)
bool NkKeyIsModifier(NkKey key);

// Retourne true si la touche est sur le pavé numérique
bool NkKeyIsNumpad(NkKey key);

// Retourne true si c'est une touche de fonction (F1–F24)
bool NkKeyIsFunctionKey(NkKey key);

// ===========================================================================
// NkButtonState — état d'un bouton (clavier, souris, manette)
// ===========================================================================

enum class NkButtonState : NkU32
{
    NK_RELEASED = 0, ///< Relâché (état de repos)
    NK_PRESSED,      ///< Vient d'être enfoncé
    NK_REPEAT,       ///< Maintenu (auto-repeat généré par l'OS)
    NK_BUTTON_STATE_MAX
};

inline const char* NkButtonStateToString(NkButtonState s)
{
    switch (s)
    {
    case NkButtonState::NK_PRESSED:  return "PRESSED";
    case NkButtonState::NK_RELEASED: return "RELEASED";
    case NkButtonState::NK_REPEAT:   return "REPEAT";
    default:                         return "UNKNOWN";
    }
}

// ===========================================================================
// NkMouseButton — boutons de la souris
// ===========================================================================

enum class NkMouseButton : NkU32
{
    NK_MB_UNKNOWN = 0,
    NK_MB_LEFT,      ///< Bouton principal
    NK_MB_RIGHT,     ///< Bouton secondaire / menu contextuel
    NK_MB_MIDDLE,    ///< Bouton central / clic molette
    NK_MB_BACK,      ///< Bouton latéral arrière (Précédent navigateur)
    NK_MB_FORWARD,   ///< Bouton latéral avant (Suivant navigateur)
    NK_MB_6,         ///< Bouton supplémentaire 6
    NK_MB_7,         ///< Bouton supplémentaire 7
    NK_MB_8,         ///< Bouton supplémentaire 8
    NK_MOUSE_BUTTON_MAX
};

inline const char* NkMouseButtonToString(NkMouseButton b)
{
    switch (b)
    {
    case NkMouseButton::NK_MB_LEFT:    return "LEFT";
    case NkMouseButton::NK_MB_RIGHT:   return "RIGHT";
    case NkMouseButton::NK_MB_MIDDLE:  return "MIDDLE";
    case NkMouseButton::NK_MB_BACK:    return "BACK";
    case NkMouseButton::NK_MB_FORWARD: return "FORWARD";
    case NkMouseButton::NK_MB_6:       return "MB6";
    case NkMouseButton::NK_MB_7:       return "MB7";
    case NkMouseButton::NK_MB_8:       return "MB8";
    default:                           return "UNKNOWN";
    }
}

// ===========================================================================
// NkModifierState — état des touches modificatrices au moment de l'événement
// ===========================================================================

struct NkModifierState
{
    bool ctrl   = false; ///< LCtrl ou RCtrl
    bool alt    = false; ///< LAlt ou RAlt / AltGr
    bool shift  = false; ///< LShift ou RShift
    bool super  = false; ///< LWin / RWin / LCmd / RCmd / Meta
    bool altGr  = false; ///< AltGr spécifique (distinct de Alt sur certains layouts)
    bool numLock= false; ///< NumLock actif
    bool capLock= false; ///< CapsLock actif
    bool scrLock= false; ///< ScrollLock actif

    NkModifierState() = default;
    NkModifierState(bool ctrl, bool alt, bool shift, bool super = false)
        : ctrl(ctrl), alt(alt), shift(shift), super(super) {}

    bool Any()  const { return ctrl || alt || shift || super || altGr; }
    bool None() const { return !Any(); }

    bool operator==(const NkModifierState& o) const
    {
        return ctrl==o.ctrl && alt==o.alt && shift==o.shift
            && super==o.super && altGr==o.altGr;
    }
    bool operator!=(const NkModifierState& o) const { return !(*this == o); }

    std::string ToString() const;
};

// ===========================================================================
// NkGamepadButton — boutons de manette (layout Xbox universel)
// ===========================================================================

enum class NkGamepadButton : NkU32
{
    NK_GP_UNKNOWN = 0,
    // Face
    NK_GP_SOUTH,       ///< A (Xbox) / Cross (PlayStation)
    NK_GP_EAST,        ///< B (Xbox) / Circle (PlayStation)
    NK_GP_WEST,        ///< X (Xbox) / Square (PlayStation)
    NK_GP_NORTH,       ///< Y (Xbox) / Triangle (PlayStation)
    // Bumpers / Triggers (digitaux)
    NK_GP_LB,          ///< Left Bumper / L1
    NK_GP_RB,          ///< Right Bumper / R1
    NK_GP_LT_DIGITAL,  ///< Left Trigger digital (enfoncé au max)
    NK_GP_RT_DIGITAL,  ///< Right Trigger digital
    // Thumbsticks (clic)
    NK_GP_LSTICK,      ///< Left Stick click / L3
    NK_GP_RSTICK,      ///< Right Stick click / R3
    // Pavé directionnel
    NK_GP_DPAD_UP,
    NK_GP_DPAD_DOWN,
    NK_GP_DPAD_LEFT,
    NK_GP_DPAD_RIGHT,
    // Spéciaux
    NK_GP_START,       ///< Start / Options / + (Switch)
    NK_GP_BACK,        ///< Back / Select / Share / - (Switch)
    NK_GP_GUIDE,       ///< Bouton Xbox / PS / Home
    NK_GP_TOUCHPAD,    ///< Clic pavé tactile (DualShock 4/5)
    NK_GP_CAPTURE,     ///< Bouton capture (Switch)
    NK_GP_PADDLE_1,    ///< Palette arrière 1 (Elite controller)
    NK_GP_PADDLE_2,
    NK_GP_PADDLE_3,
    NK_GP_PADDLE_4,
    NK_GAMEPAD_BUTTON_MAX
};

inline const char* NkGamepadButtonToString(NkGamepadButton b)
{
    switch (b)
    {
    case NkGamepadButton::NK_GP_SOUTH:      return "A/Cross";
    case NkGamepadButton::NK_GP_EAST:       return "B/Circle";
    case NkGamepadButton::NK_GP_WEST:       return "X/Square";
    case NkGamepadButton::NK_GP_NORTH:      return "Y/Triangle";
    case NkGamepadButton::NK_GP_LB:         return "LB/L1";
    case NkGamepadButton::NK_GP_RB:         return "RB/R1";
    case NkGamepadButton::NK_GP_LT_DIGITAL: return "LT";
    case NkGamepadButton::NK_GP_RT_DIGITAL: return "RT";
    case NkGamepadButton::NK_GP_LSTICK:     return "L3";
    case NkGamepadButton::NK_GP_RSTICK:     return "R3";
    case NkGamepadButton::NK_GP_DPAD_UP:    return "DUp";
    case NkGamepadButton::NK_GP_DPAD_DOWN:  return "DDown";
    case NkGamepadButton::NK_GP_DPAD_LEFT:  return "DLeft";
    case NkGamepadButton::NK_GP_DPAD_RIGHT: return "DRight";
    case NkGamepadButton::NK_GP_START:      return "Start";
    case NkGamepadButton::NK_GP_BACK:       return "Back";
    case NkGamepadButton::NK_GP_GUIDE:      return "Guide";
    case NkGamepadButton::NK_GP_TOUCHPAD:   return "Touchpad";
    case NkGamepadButton::NK_GP_CAPTURE:    return "Capture";
    default:                                return "Unknown";
    }
}

// ===========================================================================
// NkGamepadAxis — axes analogiques
// ===========================================================================

enum class NkGamepadAxis : NkU32
{
    NK_GP_AXIS_LX = 0, ///< Stick gauche horizontal [-1=gauche, +1=droite]
    NK_GP_AXIS_LY,     ///< Stick gauche vertical   [-1=bas,    +1=haut]
    NK_GP_AXIS_RX,     ///< Stick droit horizontal
    NK_GP_AXIS_RY,     ///< Stick droit vertical
    NK_GP_AXIS_LT,     ///< Gâchette gauche [0=relâchée, +1=enfoncée]
    NK_GP_AXIS_RT,     ///< Gâchette droite
    NK_GP_AXIS_DPAD_X, ///< DPad analogique horizontal (certaines manettes)
    NK_GP_AXIS_DPAD_Y, ///< DPad analogique vertical
    NK_GAMEPAD_AXIS_MAX
};

inline const char* NkGamepadAxisToString(NkGamepadAxis a)
{
    switch (a)
    {
    case NkGamepadAxis::NK_GP_AXIS_LX:     return "LX";
    case NkGamepadAxis::NK_GP_AXIS_LY:     return "LY";
    case NkGamepadAxis::NK_GP_AXIS_RX:     return "RX";
    case NkGamepadAxis::NK_GP_AXIS_RY:     return "RY";
    case NkGamepadAxis::NK_GP_AXIS_LT:     return "LT";
    case NkGamepadAxis::NK_GP_AXIS_RT:     return "RT";
    case NkGamepadAxis::NK_GP_AXIS_DPAD_X: return "DPadX";
    case NkGamepadAxis::NK_GP_AXIS_DPAD_Y: return "DPadY";
    default:                               return "Unknown";
    }
}

// ===========================================================================
// NkTouchPhase — phase d'un contact tactile
// ===========================================================================

enum class NkTouchPhase : NkU32
{
    NK_TOUCH_PHASE_BEGAN     = 0, ///< Contact nouveau posé
    NK_TOUCH_PHASE_MOVED,         ///< Contact déplacé
    NK_TOUCH_PHASE_STATIONARY,    ///< Contact toujours en contact mais immobile
    NK_TOUCH_PHASE_ENDED,         ///< Contact levé
    NK_TOUCH_PHASE_CANCELLED,     ///< Contact annulé (appel entrant, etc.)
    NK_TOUCH_PHASE_MAX
};

// ===========================================================================
// NkDropType — type d'objet déposé
// ===========================================================================

enum class NkDropType : NkU32
{
    NK_DROP_TYPE_UNKNOWN = 0,
    NK_DROP_TYPE_FILE,           ///< Un ou plusieurs fichiers
    NK_DROP_TYPE_TEXT,           ///< Texte UTF-8
    NK_DROP_TYPE_IMAGE,          ///< Image brute / URI d'image
    NK_DROP_TYPE_URL,            ///< URL
    NK_DROP_TYPE_MAX
};

// ===========================================================================
// NkWindowTheme — thème OS
// ===========================================================================

enum class NkWindowTheme : NkU32
{
    NK_THEME_UNKNOWN = 0,
    NK_THEME_LIGHT,
    NK_THEME_DARK,
    NK_THEME_HIGH_CONTRAST
};

// ===========================================================================
// NkPowerEvent — sous-type des événements système énergie
// ===========================================================================

enum class NkPowerState : NkU32
{
    NK_POWER_NORMAL = 0,
    NK_POWER_LOW_BATTERY,
    NK_POWER_CRITICAL_BATTERY,
    NK_POWER_PLUGGED_IN,
    NK_POWER_SUSPENDED,
    NK_POWER_RESUMED
};

// ===========================================================================
// NkSwipeDirection — direction d'un swipe
// ===========================================================================

enum class NkSwipeDirection : NkU32
{
    NK_SWIPE_NONE  = 0,
    NK_SWIPE_LEFT,
    NK_SWIPE_RIGHT,
    NK_SWIPE_UP,
    NK_SWIPE_DOWN
};

} // namespace nkentseu

// Inclure NkKeycodeMap.h pour l'utiliser depuis les implementations plateforme
// #include "NkKeycodeMap.h"  // inclure explicitement dans les .cpp plateforme
