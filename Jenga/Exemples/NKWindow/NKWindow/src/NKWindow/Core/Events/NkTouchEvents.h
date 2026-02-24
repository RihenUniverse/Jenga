#pragma once

// =============================================================================
// NkTouchEvents.h
// Données et classes d'événements tactiles (multi-touch) et gestes.
//
// Couvre :
//   NkTouchPoint       — un point de contact individuel
//   NkTouchData        — ensemble de contacts (begin / move / end / cancel)
//   NkGesturePinchData — pincement (zoom)
//   NkGestureRotateData— rotation à 2 doigts
//   NkGesturePanData   — panoramique
//   NkGestureSwipeData — balayage
//   NkGestureTapData   — tape
//   NkGestureLongPressData — appui long
// =============================================================================

#include "NkEventTypes.h"
#include <algorithm>

namespace nkentseu
{

// ===========================================================================
// NkTouchPoint — un contact individuel
// ===========================================================================

struct NkTouchPoint
{
    NkU64       id        = 0;   ///< Identifiant unique du contact (tant qu'il est actif)
    NkTouchPhase phase    = NkTouchPhase::NK_TOUCH_PHASE_BEGAN;

    // Coordonnées dans la zone client (pixels physiques)
    float clientX = 0.f, clientY = 0.f;
    // Coordonnées écran
    float screenX = 0.f, screenY = 0.f;
    // Coordonnées normalisées [0,1] dans la zone client
    float normalX = 0.f, normalY = 0.f;
    // Déplacement depuis l'événement précédent
    float deltaX  = 0.f, deltaY  = 0.f;
    // Pression [0,1] (1 si la plateforme ne supporte pas)
    float pressure = 1.f;
    // Rayon de contact [pixels] (estimation, 0 si inconnu)
    float radiusX  = 0.f, radiusY = 0.f;
    // Angle du contact [degrés, 0 si inconnu]
    float angle    = 0.f;

    bool HasMoved() const { return deltaX != 0.f || deltaY != 0.f; }
    bool IsActive() const
    {
        return phase == NkTouchPhase::NK_TOUCH_PHASE_BEGAN
            || phase == NkTouchPhase::NK_TOUCH_PHASE_MOVED
            || phase == NkTouchPhase::NK_TOUCH_PHASE_STATIONARY;
    }
};

// ===========================================================================
// NkTouchData — ensemble de contacts pour un événement tactile
// ===========================================================================

static constexpr NkU32 NK_MAX_TOUCH_POINTS = 32;

struct NkTouchData
{
    static constexpr NkEventType TYPE = NkEventType::NK_TOUCH_BEGIN;

    NkU32      numTouches = 0;
    NkTouchPoint touches[NK_MAX_TOUCH_POINTS];

    // Centroïde de tous les contacts actifs
    float centroidX = 0.f, centroidY = 0.f;

    // Phase globale de l'événement
    NkTouchPhase globalPhase = NkTouchPhase::NK_TOUCH_PHASE_BEGAN;

    NkTouchData() = default;

    // Ajoute un contact
    void AddTouch(const NkTouchPoint& pt)
    {
        if (numTouches < NK_MAX_TOUCH_POINTS)
            touches[numTouches++] = pt;
    }

    // Recalcule le centroïde
    void UpdateCentroid()
    {
        if (!numTouches) { centroidX = centroidY = 0.f; return; }
        float sx = 0.f, sy = 0.f;
        for (NkU32 i = 0; i < numTouches; ++i)
        { sx += touches[i].clientX; sy += touches[i].clientY; }
        centroidX = sx / static_cast<float>(numTouches);
        centroidY = sy / static_cast<float>(numTouches);
    }

    // Trouve un contact par ID
    const NkTouchPoint* FindById(NkU64 id) const
    {
        for (NkU32 i = 0; i < numTouches; ++i)
            if (touches[i].id == id) return &touches[i];
        return nullptr;
    }

    std::string ToString() const
    {
        return "Touch(" + std::to_string(numTouches)
             + " contacts, centroid=" + std::to_string(centroidX)
             + "," + std::to_string(centroidY) + ")";
    }
};

// ===========================================================================
// NkGesturePinchData — pincement / zoom à 2 doigts
// ===========================================================================

struct NkGesturePinchData
{
    static constexpr NkEventType TYPE = NkEventType::NK_GESTURE_PINCH;

    float scale      = 1.f;  ///< Facteur de zoom cumulé depuis le début du geste
    float scaleDelta = 0.f;  ///< Variation depuis l'événement précédent
    float velocity   = 0.f;  ///< Vitesse de zoom (unités/s, approximatif)

    // Centre du pincement dans la zone client
    float centerX = 0.f, centerY = 0.f;

    // Distance entre les deux doigts (pixels)
    float distanceCurrent  = 0.f;
    float distanceStart    = 0.f;

    bool IsZoomIn()  const { return scaleDelta > 0.f; }
    bool IsZoomOut() const { return scaleDelta < 0.f; }

    std::string ToString() const
    {
        return "GesturePinch(scale=" + std::to_string(scale)
             + " delta=" + std::to_string(scaleDelta)
             + " center=" + std::to_string(centerX) + "," + std::to_string(centerY) + ")";
    }
};

// ===========================================================================
// NkGestureRotateData — rotation à 2 doigts
// ===========================================================================

struct NkGestureRotateData
{
    static constexpr NkEventType TYPE = NkEventType::NK_GESTURE_ROTATE;

    float angleDegrees      = 0.f; ///< Angle cumulé [degrés] depuis le début
    float angleDeltaDegrees = 0.f; ///< Variation depuis l'événement précédent
    float velocity          = 0.f; ///< Vitesse angulaire [degrés/s]

    // Centre de rotation dans la zone client
    float centerX = 0.f, centerY = 0.f;

    bool IsClockwise()        const { return angleDeltaDegrees < 0.f; }
    bool IsCounterClockwise() const { return angleDeltaDegrees > 0.f; }

    std::string ToString() const
    {
        return "GestureRotate(angle=" + std::to_string(angleDegrees) + "°"
             + " delta=" + std::to_string(angleDeltaDegrees) + "°)";
    }
};

// ===========================================================================
// NkGesturePanData — panoramique (scroll à N doigts)
// ===========================================================================

struct NkGesturePanData
{
    static constexpr NkEventType TYPE = NkEventType::NK_GESTURE_PAN;

    float deltaX     = 0.f;  ///< Déplacement horizontal depuis l'événement précédent
    float deltaY     = 0.f;  ///< Déplacement vertical
    float totalX     = 0.f;  ///< Déplacement total depuis le début du geste
    float totalY     = 0.f;
    float velocityX  = 0.f;  ///< Vitesse [pixels/s]
    float velocityY  = 0.f;

    NkU32 numFingers = 1;    ///< Nombre de doigts

    // Position du centroïde dans la zone client
    float centerX = 0.f, centerY = 0.f;

    std::string ToString() const
    {
        return "GesturePan(dx=" + std::to_string(deltaX)
             + " dy=" + std::to_string(deltaY)
             + " fingers=" + std::to_string(numFingers) + ")";
    }
};

// ===========================================================================
// NkGestureSwipeData — balayage rapide
// ===========================================================================

struct NkGestureSwipeData
{
    static constexpr NkEventType TYPE = NkEventType::NK_GESTURE_SWIPE;

    NkSwipeDirection direction = NkSwipeDirection::NK_SWIPE_NONE;
    float            speed     = 0.f;  ///< Vitesse au moment du lâcher [pixels/s]
    float            distance  = 0.f;  ///< Distance totale parcourue
    NkU32            numFingers = 1;

    // Position de début et de fin
    float startX = 0.f, startY = 0.f;
    float endX   = 0.f, endY   = 0.f;

    std::string ToString() const
    {
        const char* dirs[] = { "NONE","LEFT","RIGHT","UP","DOWN" };
        NkU32 di = static_cast<NkU32>(direction);
        const char* d = (di < 5) ? dirs[di] : "UNKNOWN";
        return std::string("GestureSwipe(") + d
             + " speed=" + std::to_string(speed)
             + " fingers=" + std::to_string(numFingers) + ")";
    }
};

// ===========================================================================
// NkGestureTapData — tape simple ou multiple
// ===========================================================================

struct NkGestureTapData
{
    static constexpr NkEventType TYPE = NkEventType::NK_GESTURE_TAP;

    NkU32 tapCount   = 1;    ///< 1 = simple, 2 = double, 3 = triple…
    NkU32 numFingers = 1;

    // Position de la tape dans la zone client
    float x = 0.f, y = 0.f;

    std::string ToString() const
    {
        return "GestureTap(count=" + std::to_string(tapCount)
             + " fingers=" + std::to_string(numFingers)
             + " at " + std::to_string(x) + "," + std::to_string(y) + ")";
    }
};

// ===========================================================================
// NkGestureLongPressData — appui long
// ===========================================================================

struct NkGestureLongPressData
{
    static constexpr NkEventType TYPE = NkEventType::NK_GESTURE_LONG_PRESS;

    float x = 0.f, y = 0.f;     ///< Position de l'appui
    float durationMs = 0.f;      ///< Durée de l'appui [ms]
    NkU32 numFingers = 1;

    std::string ToString() const
    {
        return "GestureLongPress(" + std::to_string(durationMs) + "ms"
             + " at " + std::to_string(x) + "," + std::to_string(y) + ")";
    }
};

} // namespace nkentseu
