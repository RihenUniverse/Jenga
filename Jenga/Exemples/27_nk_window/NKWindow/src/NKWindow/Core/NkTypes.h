#pragma once

// =============================================================================
// NkTypes.h
// Types mathématiques et énumérations fondamentaux.
// Convention :
//   - Structs/classes/enums : PascalCase préfixé Nk
//   - Valeurs d'énumération : NK_UPPER_SNAKE_CASE
//   - Membres publics       : camelCase
//   - Membres privés        : mPascalCase
// =============================================================================

#include <cstdint>
#include <cstddef>
#include <string>
#include <memory>
#include <functional>
#include <algorithm>

namespace nkentseu
{

// ---------------------------------------------------------------------------
// Entiers fixes
// ---------------------------------------------------------------------------

using NkU8  = uint8_t;
using NkU16 = uint16_t;
using NkU32 = uint32_t;
using NkU64 = uint64_t;
using NkI8  = int8_t;
using NkI16 = int16_t;
using NkI32 = int32_t;
using NkI64 = int64_t;

// ---------------------------------------------------------------------------
// NkVec2u - vecteur 2D non-signé
// ---------------------------------------------------------------------------

struct NkVec2u
{
    NkU32 x = 0;
    NkU32 y = 0;

    NkVec2u() = default;
    NkVec2u(NkU32 x, NkU32 y) : x(x), y(y) {}

    bool operator==(const NkVec2u& other) const { return x == other.x && y == other.y; }
    bool operator!=(const NkVec2u& other) const { return !(*this == other); }

    template<typename T>
    NkVec2u operator*(T s) const
    { return { static_cast<NkU32>(x * s), static_cast<NkU32>(y * s) }; }

    template<typename T>
    NkVec2u operator/(T s) const
    { return { static_cast<NkU32>(x / s), static_cast<NkU32>(y / s) }; }
};

// ---------------------------------------------------------------------------
// NkVec2i - vecteur 2D signé
// ---------------------------------------------------------------------------

struct NkVec2i
{
    NkI32 x = 0;
    NkI32 y = 0;

    NkVec2i() = default;
    NkVec2i(NkI32 x, NkI32 y) : x(x), y(y) {}
};

// ---------------------------------------------------------------------------
// NkRect - rectangle entier
// ---------------------------------------------------------------------------

struct NkRect
{
    NkI32 x = 0;
    NkI32 y = 0;
    NkU32 width  = 0;
    NkU32 height = 0;

    NkRect() = default;
    NkRect(NkI32 x, NkI32 y, NkU32 w, NkU32 h) : x(x), y(y), width(w), height(h) {}
};


// ---------------------------------------------------------------------------
// NkVec2f - vecteur 2D flottant
// ---------------------------------------------------------------------------

struct NkVec2f
{
    float x = 0.f;
    float y = 0.f;

    NkVec2f() = default;
    NkVec2f(float x, float y) : x(x), y(y) {}

    NkVec2f operator+(const NkVec2f& o) const { return {x+o.x, y+o.y}; }
    NkVec2f operator-(const NkVec2f& o) const { return {x-o.x, y-o.y}; }
    NkVec2f operator*(float s)          const { return {x*s, y*s};      }
    NkVec2f operator/(float s)          const { return {x/s, y/s};      }
    NkVec2f& operator+=(const NkVec2f& o){ x+=o.x; y+=o.y; return *this;}
    NkVec2f& operator-=(const NkVec2f& o){ x-=o.x; y-=o.y; return *this;}
    NkVec2f& operator*=(float s)         { x*=s;   y*=s;   return *this;}

    float  LengthSq() const { return x*x + y*y; }
    float  Length()   const;          // impl inline ci-dessous
    NkVec2f Normalized() const;
    float  Dot(const NkVec2f& o) const { return x*o.x + y*o.y; }
};

// ---------------------------------------------------------------------------
// NkVec3f - vecteur 3D flottant (utile pour homogène 2D)
// ---------------------------------------------------------------------------

struct NkVec3f
{
    float x = 0.f, y = 0.f, z = 0.f;

    NkVec3f() = default;
    NkVec3f(float x, float y, float z) : x(x), y(y), z(z) {}
    explicit NkVec3f(const NkVec2f& v, float z = 1.f) : x(v.x), y(v.y), z(z) {}

    NkVec2f ToVec2() const { return {x, y}; }
    NkVec3f operator+(const NkVec3f& o) const { return {x+o.x,y+o.y,z+o.z}; }
    NkVec3f operator*(float s)          const { return {x*s, y*s, z*s};      }
};

// ---------------------------------------------------------------------------
// NkMat3f - matrice 3x3 (coordonnées homogènes 2D)
// Stockage row-major : [ligne][colonne]
// ---------------------------------------------------------------------------

struct NkMat3f
{
    float m[3][3] = {};

    NkMat3f()
    {
        m[0][0]=1; m[1][1]=1; m[2][2]=1; // identité
    }

    NkMat3f(float m00,float m01,float m02,
            float m10,float m11,float m12,
            float m20,float m21,float m22)
    {
        m[0][0]=m00; m[0][1]=m01; m[0][2]=m02;
        m[1][0]=m10; m[1][1]=m11; m[1][2]=m12;
        m[2][0]=m20; m[2][1]=m21; m[2][2]=m22;
    }

    static NkMat3f Identity() { return NkMat3f{}; }

    static NkMat3f Translation(float tx, float ty)
    {
        return NkMat3f(1,0,tx, 0,1,ty, 0,0,1);
    }

    static NkMat3f RotationRadians(float rad)
    {
        float c = std::cos(rad), s = std::sin(rad);
        return NkMat3f(c,-s,0, s,c,0, 0,0,1);
    }

    static NkMat3f RotationDegrees(float deg)
    {
        return RotationRadians(deg * (3.14159265358979323846f / 180.f));
    }

    static NkMat3f Scale(float sx, float sy)
    {
        return NkMat3f(sx,0,0, 0,sy,0, 0,0,1);
    }

    static NkMat3f Scale(float s) { return Scale(s, s); }

    NkMat3f operator*(const NkMat3f& o) const
    {
        NkMat3f r;
        for (int i = 0; i < 3; ++i)
            for (int j = 0; j < 3; ++j)
            {
                r.m[i][j] = 0;
                for (int k = 0; k < 3; ++k)
                    r.m[i][j] += m[i][k] * o.m[k][j];
            }
        return r;
    }

    NkVec3f operator*(const NkVec3f& v) const
    {
        return {
            m[0][0]*v.x + m[0][1]*v.y + m[0][2]*v.z,
            m[1][0]*v.x + m[1][1]*v.y + m[1][2]*v.z,
            m[2][0]*v.x + m[2][1]*v.y + m[2][2]*v.z
        };
    }

    /// Transforme un point 2D (w=1)
    NkVec2f TransformPoint(const NkVec2f& p) const
    {
        NkVec3f r = *this * NkVec3f(p, 1.f);
        return { r.x / r.z, r.y / r.z };
    }

    /// Transforme un vecteur 2D (w=0, ignore translation)
    NkVec2f TransformVector(const NkVec2f& v) const
    {
        NkVec3f r = *this * NkVec3f(v, 0.f);
        return { r.x, r.y };
    }

    NkMat3f Inverse() const;   // impl ci-dessous
    float   Det()     const
    {
        return m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])
              -m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])
              +m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]);
    }
};

// ---------------------------------------------------------------------------
// NkTransform2D - transformation 2D composable (TRS)
//
// Ordre de composition : T * R * S (scale d'abord, rotation, translation)
// Usage :
//   NkTransform2D t;
//   t.position = {100, 200};
//   t.rotation = 45.f;  // degrés
//   t.scale    = {2.f, 2.f};
//   NkMat3f mat = t.GetMatrix();
//   NkVec2f world = mat.TransformPoint({0, 0});
// ---------------------------------------------------------------------------

struct NkTransform2D
{
    NkVec2f position = {0.f, 0.f};  ///< Translation en pixels/unités
    float   rotation = 0.f;          ///< Rotation en degrés
    NkVec2f scale    = {1.f, 1.f};  ///< Facteur d'échelle

    NkTransform2D() = default;
    NkTransform2D(NkVec2f pos, float rot = 0.f, NkVec2f sc = {1.f,1.f})
        : position(pos), rotation(rot), scale(sc) {}

    /// Matrice TRS : T * R * S
    NkMat3f GetMatrix() const
    {
        return NkMat3f::Translation(position.x, position.y)
             * NkMat3f::RotationDegrees(rotation)
             * NkMat3f::Scale(scale.x, scale.y);
    }

    /// Matrice inverse (pour passer de world → local)
    NkMat3f GetInverseMatrix() const { return GetMatrix().Inverse(); }

    /// Transforme un point local → world
    NkVec2f TransformPoint(const NkVec2f& local) const
    { return GetMatrix().TransformPoint(local); }

    /// Transforme world → local
    NkVec2f InverseTransformPoint(const NkVec2f& world) const
    { return GetInverseMatrix().TransformPoint(world); }

    /// Combine deux transformations (this est le parent)
    NkTransform2D operator*(const NkTransform2D& child) const
    {
        // Composition matricielle
        NkMat3f combined = GetMatrix() * child.GetMatrix();
        NkTransform2D result;
        result.position = { combined.m[0][2], combined.m[1][2] };
        result.scale.x  = NkVec2f{combined.m[0][0], combined.m[1][0]}.Length();
        result.scale.y  = NkVec2f{combined.m[0][1], combined.m[1][1]}.Length();
        result.rotation = std::atan2(combined.m[1][0], combined.m[0][0])
                        * (180.f / 3.14159265358979323846f);
        return result;
    }

    void Translate(float dx, float dy) { position.x += dx; position.y += dy; }
    void Rotate   (float degrees)      { rotation   += degrees; }
    void ScaleBy  (float sx, float sy) { scale.x    *= sx; scale.y *= sy; }
    void ScaleBy  (float s)            { ScaleBy(s, s); }

    void Reset()
    {
        position = {0.f, 0.f};
        rotation = 0.f;
        scale    = {1.f, 1.f};
    }
};

// ---------------------------------------------------------------------------
// Inline implementations
// ---------------------------------------------------------------------------

#include <cmath>

inline float    NkVec2f::Length()        const { return std::sqrt(LengthSq()); }
inline NkVec2f  NkVec2f::Normalized()    const
{
    float l = Length();
    return l > 1e-8f ? NkVec2f{x/l, y/l} : NkVec2f{};
}

inline NkMat3f NkMat3f::Inverse() const
{
    float det = Det();
    if (std::abs(det) < 1e-10f) return NkMat3f{}; // singulière → identité
    float inv = 1.f / det;
    return NkMat3f(
         (m[1][1]*m[2][2]-m[1][2]*m[2][1])*inv,
        -(m[0][1]*m[2][2]-m[0][2]*m[2][1])*inv,
         (m[0][1]*m[1][2]-m[0][2]*m[1][1])*inv,
        -(m[1][0]*m[2][2]-m[1][2]*m[2][0])*inv,
         (m[0][0]*m[2][2]-m[0][2]*m[2][0])*inv,
        -(m[0][0]*m[1][2]-m[0][2]*m[1][0])*inv,
         (m[1][0]*m[2][1]-m[1][1]*m[2][0])*inv,
        -(m[0][0]*m[2][1]-m[0][1]*m[2][0])*inv,
         (m[0][0]*m[1][1]-m[0][1]*m[1][0])*inv
    );
}

// ---------------------------------------------------------------------------
// NkPixelFormat - formats de pixel supportés
// ---------------------------------------------------------------------------

enum class NkPixelFormat : NkU32
{
    NK_PIXEL_UNKNOWN = 0,
    NK_PIXEL_R8G8B8A8_UNORM,
    NK_PIXEL_B8G8R8A8_UNORM,
    NK_PIXEL_R8G8B8A8_SRGB,
    NK_PIXEL_B8G8R8A8_SRGB,
    NK_PIXEL_R16G16B16A16_FLOAT,
    NK_PIXEL_D24_UNORM_S8_UINT,
    NK_PIXEL_D32_FLOAT,
    NK_PIXEL_RGBA8   = 0, ///< 4 octets R G B A
    NK_PIXEL_BGRA8,        ///< 4 octets B G R A (natif Win32/macOS)
    NK_PIXEL_RGB8,         ///< 3 octets R G B
    NK_PIXEL_YUV420,       ///< YUV 4:2:0 planar (Android Camera2)
    NK_PIXEL_NV12,         ///< NV12 semi-planar (Media Foundation)
    NK_PIXEL_YUYV,         ///< YUYV packed (V4L2)
    NK_PIXEL_MJPEG,        ///< JPEG par frame
    NK_PIXEL_FORMAT_MAX
};

// ---------------------------------------------------------------------------
// NkError - résultat d'opération et message d'erreur
// ---------------------------------------------------------------------------

struct NkError
{
    NkU32       code    = 0;
    std::string message = "";

    NkError() = default;
    NkError(NkU32 code, std::string msg) : code(code), message(std::move(msg)) {}

    bool        IsOk()    const { return code == 0; }
    std::string ToString() const
    { return code == 0 ? "OK" : "[" + std::to_string(code) + "] " + message; }

    static NkError Ok() { return NkError(0, "OK"); }
};

// ---------------------------------------------------------------------------
// NkRendererApi - backends graphiques disponibles
// ---------------------------------------------------------------------------

enum class NkRendererApi : NkU32
{
    NK_NONE       = 0,
    NK_SOFTWARE,
    NK_OPENGL,
    NK_VULKAN,
    NK_DIRECTX11,
    NK_DIRECTX12,
    NK_METAL,
    NK_RENDERER_API_MAX
};

inline const char* NkRendererApiToString(NkRendererApi api)
{
    switch (api)
    {
    case NkRendererApi::NK_SOFTWARE:   return "Software";
    case NkRendererApi::NK_OPENGL:     return "OpenGL";
    case NkRendererApi::NK_VULKAN:     return "Vulkan";
    case NkRendererApi::NK_DIRECTX11:  return "DirectX 11";
    case NkRendererApi::NK_DIRECTX12:  return "DirectX 12";
    case NkRendererApi::NK_METAL:      return "Metal";
    default:                           return "None";
    }
}

} // namespace nkentseu
