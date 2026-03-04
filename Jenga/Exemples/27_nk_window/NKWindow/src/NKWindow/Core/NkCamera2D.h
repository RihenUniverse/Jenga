#pragma once

// =============================================================================
// NkCamera2D.h
// Caméra 2D avec pan, zoom, rotation et viewport.
//
// Coordonnées :
//   Monde (world)   — espace de jeu non borné
//   Écran (screen)  — pixels fenêtre [0, viewportW] × [0, viewportH]
//
// Utilisation :
//   NkCamera2D cam;
//   cam.SetViewport(1280, 720);
//   cam.SetPosition(400.f, 300.f);   // centre caméra sur (400,300) monde
//   cam.SetZoom(2.f);                // zoom × 2
//
//   // Dans le renderer :
//   renderer.SetTransform(cam.GetTransform());
//
//   // Conversions :
//   NkVec2f worldPos = cam.ScreenToWorld({mouseX, mouseY});
//   NkVec2f screenPos = cam.WorldToScreen({entityX, entityY});
// =============================================================================

#include "NkTypes.h"   // NkVec2f, NkMat3f, NkTransform2D

#include <algorithm>
#include <cmath>

namespace nkentseu
{

class NkCamera2D
{
public:
    // -----------------------------------------------------------------------
    // Construction
    // -----------------------------------------------------------------------

    NkCamera2D() = default;

    explicit NkCamera2D(NkU32 viewportWidth, NkU32 viewportHeight)
    {
        SetViewport(viewportWidth, viewportHeight);
    }

    // -----------------------------------------------------------------------
    // Viewport
    // -----------------------------------------------------------------------

    void SetViewport(NkU32 w, NkU32 h)
    {
        mViewportW = static_cast<float>(w);
        mViewportH = static_cast<float>(h);
        mDirty     = true;
    }

    NkU32 GetViewportWidth()  const { return static_cast<NkU32>(mViewportW); }
    NkU32 GetViewportHeight() const { return static_cast<NkU32>(mViewportH); }

    // -----------------------------------------------------------------------
    // Position (centre de la caméra dans le monde)
    // -----------------------------------------------------------------------

    void  SetPosition(float x, float y)  { mPosition = {x, y}; mDirty = true; }
    void  SetPosition(NkVec2f p)         { mPosition = p;       mDirty = true; }
    NkVec2f GetPosition()          const { return mPosition; }

    void Move(float dx, float dy)        { mPosition.x += dx; mPosition.y += dy; mDirty = true; }
    void Move(NkVec2f delta)             { Move(delta.x, delta.y); }

    // -----------------------------------------------------------------------
    // Zoom
    // -----------------------------------------------------------------------

    void  SetZoom(float zoom)     { mZoom = std::max(mZoomMin, std::min(zoom, mZoomMax)); mDirty = true; }
    float GetZoom()         const { return mZoom; }

    void  SetZoomLimits(float minZ, float maxZ) { mZoomMin = minZ; mZoomMax = maxZ; }
    void  ZoomAt(float factor, NkVec2f screenAnchor)
    {
        // Zoom centré sur un point écran (comportement pinch / molette)
        NkVec2f worldBefore = ScreenToWorld(screenAnchor);
        float newZoom = std::max(mZoomMin, std::min(mZoom * factor, mZoomMax));
        mZoom  = newZoom;
        mDirty = true;
        NkVec2f worldAfter  = ScreenToWorld(screenAnchor);
        mPosition.x -= (worldAfter.x - worldBefore.x);
        mPosition.y -= (worldAfter.y - worldBefore.y);
        mDirty = true;
    }

    // -----------------------------------------------------------------------
    // Rotation (degrés)
    // -----------------------------------------------------------------------

    void  SetRotation(float degrees) { mRotation = degrees; mDirty = true; }
    float GetRotation()        const { return mRotation; }

    void Rotate(float degrees) { mRotation += degrees; mDirty = true; }

    // -----------------------------------------------------------------------
    // Bornes monde (optionnel)
    // -----------------------------------------------------------------------

    void SetWorldBounds(float left, float top, float right, float bottom)
    {
        mBoundsEnabled = true;
        mBoundsLeft = left; mBoundsTop = top;
        mBoundsRight = right; mBoundsBottom = bottom;
        ClampToBounds();
    }

    void DisableWorldBounds() { mBoundsEnabled = false; }

    // -----------------------------------------------------------------------
    // Matrices
    // -----------------------------------------------------------------------

    /// Vue → matrice monde-vers-écran
    const NkMat3f& GetViewMatrix() const
    {
        if (mDirty) Recalculate();
        return mViewMatrix;
    }

    /// Projection inverse → matrice écran-vers-monde
    const NkMat3f& GetInverseViewMatrix() const
    {
        if (mDirty) Recalculate();
        return mInvMatrix;
    }

    // -----------------------------------------------------------------------
    // NkTransform2D pour le Renderer
    // -----------------------------------------------------------------------

    /**
     * @brief Retourne le transform à passer à renderer.SetTransform().
     * Le renderer transforme les coordonnées monde en pixels écran.
     */
    NkTransform2D GetTransform() const
    {
        if (mDirty) Recalculate();
        return mCachedTransform;
    }

    // -----------------------------------------------------------------------
    // Conversions
    // -----------------------------------------------------------------------

    /// Convertit un point écran (pixels) en coordonnées monde.
    NkVec2f ScreenToWorld(NkVec2f screen) const
    {
        if (mDirty) Recalculate();
        return mInvMatrix.TransformPoint(screen);
    }

    /// Convertit un point monde en pixels écran.
    NkVec2f WorldToScreen(NkVec2f world) const
    {
        if (mDirty) Recalculate();
        return mViewMatrix.TransformPoint(world);
    }

    // -----------------------------------------------------------------------
    // Visibilité — frustum culling 2D
    // -----------------------------------------------------------------------

    bool IsVisible(NkVec2f worldPos, float radius = 0.f) const
    {
        NkVec2f sp = WorldToScreen(worldPos);
        return sp.x + radius >= 0.f && sp.x - radius <= mViewportW
            && sp.y + radius >= 0.f && sp.y - radius <= mViewportH;
    }

    bool IsRectVisible(float wx, float wy, float ww, float wh) const
    {
        // Test les 4 coins + approximation rapide
        return IsVisible({wx,      wy},       0.f)
            || IsVisible({wx + ww, wy},       0.f)
            || IsVisible({wx,      wy + wh},  0.f)
            || IsVisible({wx + ww, wy + wh},  0.f);
    }

    // -----------------------------------------------------------------------
    // Reset
    // -----------------------------------------------------------------------

    void Reset()
    {
        mPosition  = {mViewportW * 0.5f, mViewportH * 0.5f};
        mZoom      = 1.f;
        mRotation  = 0.f;
        mDirty     = true;
    }

    // -----------------------------------------------------------------------
    // Shake (trauma-based camera shake)
    // -----------------------------------------------------------------------

    /**
     * @brief Applique un traumatisme (0=aucun, 1=maximum).
     * Chaque frame : Update(dt) applique le shake basé sur mTrauma²
     * et décrémente le trauma.
     */
    void AddTrauma(float amount)
    {
        mTrauma = std::min(1.f, mTrauma + amount);
    }

    void Update(float dt)
    {
        if (mTrauma <= 0.f) return;
        float shake = mTrauma * mTrauma; // shake = trauma²
        // Offsets pseudo-aléatoires (simplifié — remplacer par noise Perlin en production)
        mShakeOffsetX = shake * mShakeMaxOffset * NextRand();
        mShakeOffsetY = shake * mShakeMaxOffset * NextRand();
        mShakeAngle   = shake * mShakeMaxAngle  * NextRand();
        mTrauma = std::max(0.f, mTrauma - mTraumaDecay * dt);
        mDirty = true;
    }

    void SetShakeParameters(float maxOffset, float maxAngleDeg, float decay)
    {
        mShakeMaxOffset = maxOffset;
        mShakeMaxAngle  = maxAngleDeg;
        mTraumaDecay    = decay;
    }

private:
    // -----------------------------------------------------------------------
    // Données internes
    // -----------------------------------------------------------------------

    float    mViewportW = 800.f, mViewportH = 600.f;
    NkVec2f  mPosition  = {400.f, 300.f};
    float    mZoom      = 1.f;
    float    mRotation  = 0.f;
    float    mZoomMin   = 0.05f, mZoomMax = 50.f;

    // Bornes monde
    bool     mBoundsEnabled = false;
    float    mBoundsLeft = -1e9f, mBoundsTop = -1e9f;
    float    mBoundsRight =  1e9f, mBoundsBottom = 1e9f;

    // Shake
    float    mTrauma        = 0.f;
    float    mShakeMaxOffset = 12.f;
    float    mShakeMaxAngle  = 3.f;
    float    mTraumaDecay    = 1.f;
    float    mShakeOffsetX  = 0.f, mShakeOffsetY = 0.f;
    float    mShakeAngle    = 0.f;

    // Cache
    mutable bool        mDirty         = true;
    mutable NkMat3f     mViewMatrix    = NkMat3f::Identity();
    mutable NkMat3f     mInvMatrix     = NkMat3f::Identity();
    mutable NkTransform2D mCachedTransform;

    // -----------------------------------------------------------------------
    // Recalcul des matrices
    // -----------------------------------------------------------------------

    void Recalculate() const
    {
        // Vue = Translation(-pos) × Rotation × Zoom × Translation(+viewport/2)
        // (transforme des coordonnées monde → écran)

        float cx = mViewportW * 0.5f;
        float cy = mViewportH * 0.5f;

        // 1. Translate monde vers origine caméra
        NkMat3f T1 = NkMat3f::Translation(-mPosition.x + mShakeOffsetX,
                                           -mPosition.y + mShakeOffsetY);
        // 2. Rotation caméra
        NkMat3f R  = NkMat3f::RotationDegrees(-mRotation - mShakeAngle);
        // 3. Zoom
        NkMat3f S  = NkMat3f::Scale(mZoom, mZoom);
        // 4. Translate vers centre viewport
        NkMat3f T2 = NkMat3f::Translation(cx, cy);

        mViewMatrix = T2 * S * R * T1;
        mInvMatrix  = mViewMatrix.Inverse();

        // Construire NkTransform2D pour Renderer::SetTransform
        mCachedTransform.position = {cx, cy};
        mCachedTransform.scale    = {mZoom, mZoom};
        mCachedTransform.rotation = -mRotation - mShakeAngle;
        // Note : le transform 2D ne supporte pas la translation de caméra directement,
        // mais GetMatrix() de NkTransform2D construit T*R*S — on override ici
        // en fournissant mViewMatrix directement via un helper dans Renderer.

        mDirty = false;
    }

    void ClampToBounds()
    {
        if (!mBoundsEnabled) return;
        float hw = (mViewportW * 0.5f) / mZoom;
        float hh = (mViewportH * 0.5f) / mZoom;
        mPosition.x = std::max(mBoundsLeft   + hw, std::min(mPosition.x, mBoundsRight  - hw));
        mPosition.y = std::max(mBoundsTop    + hh, std::min(mPosition.y, mBoundsBottom - hh));
    }

    static float NextRand()
    {
        // LCG simplifié (-1 à +1)
        static unsigned int seed = 42;
        seed = seed * 1664525u + 1013904223u;
        return static_cast<float>(static_cast<int>(seed)) / 2147483648.f;
    }
};

// ---------------------------------------------------------------------------
// NkCamera2DController — contrôleur souris/clavier/touch standard
// ---------------------------------------------------------------------------

class NkCamera2DController
{
public:
    explicit NkCamera2DController(NkCamera2D& cam) : mCam(cam) {}

    // Appeler sur NkMouseWheelEvent
    void OnScroll(float deltaY, float mouseX, float mouseY, float sensitivity = 0.1f)
    {
        float factor = 1.f + deltaY * sensitivity;
        mCam.ZoomAt(factor, {mouseX, mouseY});
    }

    // Appeler sur NkMouseMoveEvent quand bouton central pressé
    void OnMiddleDrag(float dx, float dy)
    {
        float inv = 1.f / mCam.GetZoom();
        mCam.Move(-dx * inv, -dy * inv);
    }

    // Appeler sur NkMouseMoveEvent quand bouton droit pressé
    void OnRightDrag(float dx, float /*dy*/)
    {
        mCam.Rotate(dx * 0.5f);
    }

    // Déplacement clavier (appeler chaque frame)
    void UpdateKeyboard(bool left, bool right, bool up, bool down,
                        float speed, float dt)
    {
        float inv = 1.f / mCam.GetZoom();
        float s = speed * dt * inv;
        if (left)  mCam.Move(-s, 0.f);
        if (right) mCam.Move( s, 0.f);
        if (up)    mCam.Move(0.f, -s);
        if (down)  mCam.Move(0.f,  s);
    }

    // Pinch-to-zoom (touch)
    void OnPinch(float scale, float centerX, float centerY)
    {
        mCam.ZoomAt(scale, {centerX, centerY});
    }

private:
    NkCamera2D& mCam;
};

} // namespace nkentseu
