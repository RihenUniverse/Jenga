// -----------------------------------------------------------------------------
// FICHIER: Test/ExampleDocumentation.h
// DESCRIPTION: Exemple complet de documentation Doxygen
// AUTEUR: Rihen
// DATE: 2026-02-07
// -----------------------------------------------------------------------------

#pragma once

#ifndef EXAMPLE_DOCUMENTATION_H_INCLUDED
#define EXAMPLE_DOCUMENTATION_H_INCLUDED

#include <vector>
#include <string>

namespace nkentseu {
namespace examples {

// ============================================================================
// CLASSE: Vector3D - Démonstration Documentation Complète
// ============================================================================

/**
 * @class Vector3D
 * @brief Vecteur 3D pour calculs géométriques
 * 
 * Cette classe représente un vecteur dans l'espace euclidien 3D.
 * Elle fournit des opérations mathématiques courantes comme l'addition,
 * la soustraction, le produit scalaire et vectoriel.
 * 
 * @note Structure POD - peut être copiée avec memcpy
 * @note Taille: 12 bytes (3 × float)
 * 
 * @threadsafe Oui (pas d'état partagé)
 * 
 * @example Utilisation basique
 * @code
 * Vector3D position(1.0f, 2.0f, 3.0f);
 * Vector3D velocity(0.5f, 0.0f, -0.5f);
 * 
 * position += velocity * deltaTime;
 * 
 * float distance = position.Length();
 * Vector3D direction = position.Normalized();
 * @endcode
 * 
 * @author Rihen
 * @since Version 1.0.0
 * @date 2026-02-07
 */
class Vector3D {
public:
    // ------------------------------------------------------------------------
    // CONSTRUCTEURS
    // ------------------------------------------------------------------------
    
    /**
     * @brief Constructeur par défaut (vecteur nul)
     * 
     * Initialise toutes les composantes à zéro.
     * 
     * @complexity O(1)
     */
    Vector3D();
    
    /**
     * @brief Constructeur avec valeurs
     * 
     * @param[in] x Composante X
     * @param[in] y Composante Y  
     * @param[in] z Composante Z
     * 
     * @example
     * @code
     * Vector3D v(1.0f, 2.0f, 3.0f);
     * @endcode
     */
    Vector3D(float x, float y, float z);
    
    /**
     * @brief Constructeur de copie
     * 
     * @param[in] other Vecteur à copier
     */
    Vector3D(const Vector3D& other);
    
    // ------------------------------------------------------------------------
    // MÉTHODES STATIQUES
    // ------------------------------------------------------------------------
    
    /**
     * @brief Calcule le produit scalaire de deux vecteurs
     * 
     * Le produit scalaire est défini comme: a·b = |a|×|b|×cos(θ)
     * où θ est l'angle entre les vecteurs.
     * 
     * @param[in] a Premier vecteur
     * @param[in] b Deuxième vecteur
     * 
     * @return Produit scalaire (a·b)
     * @retval 0.0f Si les vecteurs sont perpendiculaires
     * @retval >0   Si l'angle est aigu
     * @retval <0   Si l'angle est obtus
     * 
     * @complexity O(1)
     * @threadsafe
     * 
     * @see Cross() pour le produit vectoriel
     * 
     * @example
     * @code
     * Vector3D a(1, 0, 0);
     * Vector3D b(0, 1, 0);
     * float dot = Vector3D::Dot(a, b);  // 0.0 (perpendiculaires)
     * @endcode
     */
    static float Dot(const Vector3D& a, const Vector3D& b);
    
    /**
     * @brief Calcule le produit vectoriel de deux vecteurs
     * 
     * Le produit vectoriel produit un vecteur perpendiculaire aux deux
     * vecteurs d'entrée, dont la longueur est proportionnelle à sin(θ).
     * 
     * @param[in] a Premier vecteur
     * @param[in] b Deuxième vecteur
     * 
     * @return Vecteur perpendiculaire (a × b)
     * 
     * @note Suit la règle de la main droite
     * @warning Non commutatif: a × b ≠ b × a
     * 
     * @complexity O(1)
     * @threadsafe
     * 
     * @see Dot() pour le produit scalaire
     */
    static Vector3D Cross(const Vector3D& a, const Vector3D& b);
    
    /**
     * @brief Interpole linéairement entre deux vecteurs
     * 
     * @param[in] a Vecteur de départ (t=0)
     * @param[in] b Vecteur d'arrivée (t=1)
     * @param[in] t Facteur d'interpolation [0, 1]
     * 
     * @return Vecteur interpolé
     * 
     * @note Si t=0, retourne a. Si t=1, retourne b.
     * @warning t devrait être dans [0, 1] mais aucune vérification n'est faite
     */
    static Vector3D Lerp(const Vector3D& a, const Vector3D& b, float t);
    
    // ------------------------------------------------------------------------
    // MÉTHODES PUBLIQUES
    // ------------------------------------------------------------------------
    
    /**
     * @brief Calcule la longueur (magnitude) du vecteur
     * 
     * Calcule sqrt(x² + y² + z²)
     * 
     * @return Longueur du vecteur
     * @retval 0.0f Si c'est le vecteur nul
     * 
     * @complexity O(1)
     * 
     * @note Utilisez LengthSquared() si vous n'avez besoin que de comparer
     * @see LengthSquared() pour éviter la racine carrée
     */
    float Length() const;
    
    /**
     * @brief Calcule le carré de la longueur
     * 
     * Calcule x² + y² + z² sans la racine carrée.
     * Plus rapide que Length() pour les comparaisons.
     * 
     * @return Carré de la longueur
     * 
     * @complexity O(1)
     * 
     * @example Comparaison de distances
     * @code
     * if (v1.LengthSquared() < v2.LengthSquared()) {
     *     // v1 est plus proche que v2
     * }
     * @endcode
     */
    float LengthSquared() const;
    
    /**
     * @brief Normalise le vecteur (longueur = 1)
     * 
     * Divise chaque composante par la longueur du vecteur.
     * 
     * @warning Ne fait rien si le vecteur est nul (division par zéro)
     * 
     * @complexity O(1)
     * 
     * @see Normalized() pour une version const
     */
    void Normalize();
    
    /**
     * @brief Retourne une version normalisée du vecteur
     * 
     * @return Vecteur de même direction mais de longueur 1
     * 
     * @throw std::runtime_error Si le vecteur est nul
     * 
     * @complexity O(1)
     */
    Vector3D Normalized() const;
    
    // ------------------------------------------------------------------------
    // OPÉRATEURS
    // ------------------------------------------------------------------------
    
    /**
     * @brief Addition de vecteurs
     * 
     * @param[in] other Vecteur à additionner
     * @return Somme des deux vecteurs
     */
    Vector3D operator+(const Vector3D& other) const;
    
    /**
     * @brief Soustraction de vecteurs
     * 
     * @param[in] other Vecteur à soustraire
     * @return Différence des deux vecteurs
     */
    Vector3D operator-(const Vector3D& other) const;
    
    /**
     * @brief Multiplication par un scalaire
     * 
     * @param[in] scalar Facteur multiplicateur
     * @return Vecteur multiplié
     */
    Vector3D operator*(float scalar) const;
    
    /**
     * @brief Division par un scalaire
     * 
     * @param[in] scalar Diviseur
     * @return Vecteur divisé
     * 
     * @warning Pas de vérification de division par zéro
     */
    Vector3D operator/(float scalar) const;
    
    /**
     * @brief Opérateur d'égalité
     * 
     * @param[in] other Vecteur à comparer
     * @return true si égaux, false sinon
     * 
     * @note Utilise une comparaison exacte (==), pas de epsilon
     */
    bool operator==(const Vector3D& other) const;
    
    // ------------------------------------------------------------------------
    // MEMBRES PUBLICS
    // ------------------------------------------------------------------------
    
    /**
     * @var x
     * Composante X du vecteur
     */
    float x;
    
    /// Composante Y du vecteur
    float y;
    
    float z;  ///< Composante Z du vecteur
    
    // ------------------------------------------------------------------------
    // CONSTANTES STATIQUES
    // ------------------------------------------------------------------------
    
    /**
     * @brief Vecteur unitaire sur l'axe X (1, 0, 0)
     */
    static const Vector3D UnitX;
    
    /// Vecteur unitaire sur l'axe Y (0, 1, 0)
    static const Vector3D UnitY;
    
    /// Vecteur unitaire sur l'axe Z (0, 0, 1)  
    static const Vector3D UnitZ;
    
    /// Vecteur nul (0, 0, 0)
    static const Vector3D Zero;
    
    /// Vecteur de uns (1, 1, 1)
    static const Vector3D One;
};

// ============================================================================
// ENUMÉRATION: CoordinateSystem
// ============================================================================

/**
 * @enum CoordinateSystem
 * @brief Systèmes de coordonnées supportés
 * 
 * Définit les différents systèmes de coordonnées 3D utilisables.
 */
enum class CoordinateSystem {
    /**
     * @brief Système de coordonnées main droite (OpenGL, Vulkan)
     * 
     * X pointe vers la droite, Y vers le haut, Z vers l'observateur
     */
    RightHanded,
    
    /**
     * @brief Système de coordonnées main gauche (DirectX)
     * 
     * X pointe vers la droite, Y vers le haut, Z s'éloigne de l'observateur
     */
    LeftHanded
};

// ============================================================================
// STRUCTURE: BoundingBox
// ============================================================================

/**
 * @struct BoundingBox
 * @brief Boîte englobante alignée sur les axes (AABB)
 * 
 * Représente une boîte rectangulaire dont les faces sont alignées
 * avec les axes de coordonnées. Utilisée pour les tests de collision
 * et le culling de frustum.
 * 
 * @note Structure POD
 */
struct BoundingBox {
    /// Point minimum de la boîte
    Vector3D min;
    
    /// Point maximum de la boîte
    Vector3D max;
    
    /**
     * @brief Vérifie si un point est dans la boîte
     * 
     * @param[in] point Point à tester
     * @return true si le point est dans la boîte
     */
    bool Contains(const Vector3D& point) const;
    
    /**
     * @brief Vérifie l'intersection avec une autre boîte
     * 
     * @param[in] other Autre boîte
     * @return true si les boîtes se chevauchent
     */
    bool Intersects(const BoundingBox& other) const;
};

// ============================================================================
// MACROS
// ============================================================================

/**
 * @macro NK_PI
 * Valeur de Pi avec précision float
 */
#define NK_PI 3.14159265358979323846f

/**
 * @macro NK_DEG_TO_RAD
 * Convertit des degrés en radians
 */
#define NK_DEG_TO_RAD(deg) ((deg) * NK_PI / 180.0f)

/**
 * @macro NK_RAD_TO_DEG  
 * Convertit des radians en degrés
 */
#define NK_RAD_TO_DEG(rad) ((rad) * 180.0f / NK_PI)

// ============================================================================
// FONCTIONS UTILITAIRES
// ============================================================================

/**
 * @function Clamp
 * @brief Limite une valeur entre un min et un max
 * 
 * @tparam T Type de la valeur (doit supporter <)
 * 
 * @param[in] value Valeur à limiter
 * @param[in] min Valeur minimale
 * @param[in] max Valeur maximale
 * 
 * @return Valeur limitée dans [min, max]
 * 
 * @note Si value < min, retourne min. Si value > max, retourne max.
 */
template<typename T>
T Clamp(T value, T min, T max);

/**
 * @brief Calcule la distance entre deux points
 * 
 * @param[in] a Premier point
 * @param[in] b Deuxième point
 * 
 * @return Distance euclidienne
 * 
 * @complexity O(1)
 */
float Distance(const Vector3D& a, const Vector3D& b);

} // namespace examples
} // namespace nkentseu

#endif // EXAMPLE_DOCUMENTATION_H_INCLUDED

// ============================================================================
// Copyright © 2024-2026 Rihen. All rights reserved.
// Proprietary License - Free to use and modify
// ============================================================================
