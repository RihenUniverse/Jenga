// -----------------------------------------------------------------------------
// FICHIER: Core\NKCore\src\NKCore\Traits\NkTraits.h
// DESCRIPTION: Type traits SANS <type_traits>
// AUTEUR: Rihen
// DATE: 2026-02-07
// VERSION: 1.0.0
// -----------------------------------------------------------------------------

#pragma once

#ifndef NKENTSEU_CORE_NKCORE_SRC_NKCORE_TRAITS_NKTRAITS_H_INCLUDED
#define NKENTSEU_CORE_NKCORE_SRC_NKCORE_TRAITS_NKTRAITS_H_INCLUDED

#include "NKCore/NkTypes.h"
#include "NkCompilerDetect.h"
#include "NkPlatformDetect.h"
#include "NKCore/NkExport.h"

#include <type_traits> // Utilisé uniquement pour les intrinsèques comme __is_enum, __is_class, etc.

/**
 * - NK : Espace de noms principal pour les utilitaires de la bibliothèque NK.
 *
 * @Description :
 * Ce namespace regroupe des utilitaires pour la manipulation des types, des constantes conditionnelles,
 * et des outils de métaprogrammation pour assurer la portabilité multiplateforme. Les dépendances à la STL
 * sont limitées aux intrinsèques du compilateur (__is_enum, __is_class, etc.) pour vérifier les propriétés des types.
 */
namespace nkentseu {
    namespace core {
        namespace traits {

            // ========================================
            // TYPE TRAITS
            // ========================================
            /**
             * - NkBoolConstant : Représente une constante booléenne pour la métaprogrammation.
             *
             * @Description :
             * Encapsule une valeur booléenne constante pour les traits de type, avec conversion implicite en booléen.
             * Utilisé comme base pour d'autres traits booléens.
             *
             * @Template :
             * - (bool Val) : Valeur booléenne constante.
             *
             * @Members :
             * - (static constexpr bool) value : Valeur booléenne constante.
             * - (type) type : Type de la structure elle-même.
             * - (value_type) value_type : Type de la valeur (bool).
             * - (constexpr operator bool) : Conversion implicite en booléen.
             *
             * @Dépendances : Aucune
             */
            template<nk_bool Val>
            struct NkBoolConstant {
                static constexpr nk_bool value = Val;
                using type = NkBoolConstant;
                using value_type = nk_bool;
                constexpr operator nk_bool() const noexcept { return value; }
            };

            using NkTrueType = NkBoolConstant<true>;
            inline constexpr nk_bool NkTrueType_v = NkTrueType::value;

            using NkFalseType = NkBoolConstant<false>;
            inline constexpr nk_bool NkFalseType_v = NkFalseType::value;

            // Forward declarations needed by NkDeclVal
            template<typename T> struct NkAddRValueReference;
            template<typename T> using NkAddRValueReference_t = typename NkAddRValueReference<T>::type;

            /**
             * - NkDeclVal : Fournit une référence à un type en contexte non évalué.
             *
             * @Description :
             * Fournit une référence rvalue à un type T pour une utilisation dans des contextes non évalués (SFINAE).
             * Utilisé pour tester des expressions dans la métaprogrammation.
             *
             * @Template :
             * - (typename T) : Type à référencer.
             *
             * @Return : NkAddRValueReference_t<T> (référence rvalue de T).
             *
             * @Dépendances : NkAddRValueReference
             */
            template<typename T>
            NkAddRValueReference_t<T> NkDeclVal() noexcept {
                static_assert(!sizeof(T), "NkDeclVal should only be used in unevaluated contexts");
            }

            #define NkDeclType(...) decltype(__VA_ARGS__)

            /**
             * - NkIntegralConstant : Représente une constante intégrale pour la métaprogrammation.
             *
             * @Description :
             * Encapsule une valeur intégrale constante pour les traits de type, avec conversion implicite.
             * Utilisé pour représenter des valeurs comme la taille ou l’alignement.
             *
             * @Template :
             * - (typename T) : Type de la valeur constante.
             * - (T Value) : Valeur constante.
             *
             * @Members :
             * - (static constexpr T) value : Valeur constante.
             * - (type) type : Type de la structure elle-même.
             * - (value_type) value_type : Type de la valeur.
             * - (constexpr operator T) : Conversion implicite en T.
             *
             * @Dépendances : Aucune
             */
            template<typename T, T Value>
            struct NkIntegralConstant {
                static constexpr T value = Value;
                using type = NkIntegralConstant;
                using value_type = T;
                constexpr operator T() const noexcept { return value; }
            };

            /**
             * - NkIsSame : Vérifie si deux types sont identiques.
             *
             * @Description :
             * Détermine si les types T et U sont identiques, sans dépendance à std::is_same.
             * Utilisé comme base pour d'autres traits comme NkIsVoid ou NkIsReference.
             *
             * @Template :
             * - (typename T) : Premier type à comparer.
             * - (typename U) : Deuxième type à comparer.
             *
             * @Members :
             * - (static constexpr bool) value : True si T et U sont identiques, false sinon.
             *
             * @Dépendances : NkBoolConstant
             */
            template<typename T, typename U>
            struct NkIsSame : NkFalseType {};

            template<typename T>
            struct NkIsSame<T, T> : NkTrueType {};

            template<typename T, typename U>
            inline constexpr nk_bool NkIsSame_v = NkIsSame<T, U>::value;

            /**
             * - NkIsNullPointer : Vérifie si un type est un pointeur nul (nullptr_t).
             *
             * @Description :
             * Détermine si le type T est std::nullptr_t ou un type équivalent.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est un pointeur nul, false sinon.
             *
             * @Dépendances : NkIsSame
             */
            template<typename T>
            struct NkIsNullPointer : NkBoolConstant<false> {};

            template<>
            struct NkIsNullPointer<NkDeclType(nullptr)> : NkBoolConstant<true> {};

            template<typename T>
            inline constexpr nk_bool NkIsNullPointer_v = NkIsNullPointer<T>::value;

            /**
             * - NkEnableIf : Active un type conditionnellement pour SFINAE.
             *
             * @Description :
             * Active un type T si la condition booléenne B est vraie, utilisé pour SFINAE dans la métaprogrammation.
             * Utilisé pour activer ou désactiver des surcharges de fonctions/templates.
             *
             * @Template :
             * - (bool B) : Condition booléenne.
             * - (typename T) : Type à activer (void par défaut).
             *
             * @Members :
             * - (type) type : Type T si B est true, non défini sinon.
             *
             * @Dépendances : Aucune
             */
            template<bool B, typename T = void>
            struct NkEnableIf {};

            template<typename T>
            struct NkEnableIf<true, T> { using type = T; };

            template<bool B, typename T = void>
            using NkEnableIf_t = typename NkEnableIf<B, T>::type;

            /**
             * - NkConditional : Sélectionne un type selon une condition booléenne.
             *
             * @Description :
             * Choisit entre T (si B est true) ou F (si B est false) pour la métaprogrammation conditionnelle.
             * Utilisé pour sélectionner des types dans des contextes comme NkAddLValueReference.
             *
             * @Template :
             * - (bool Condition) : Condition booléenne.
             * - (typename T) : Type à sélectionner si Condition est true.
             * - (typename F) : Type à sélectionner si Condition est false.
             *
             * @Members :
             * - (type) type : T si Condition est true, F sinon.
             *
             * @Dépendances : Aucune
             */
            template<bool Condition, typename T, typename F>
            struct NkConditional { using type = T; };

            template<typename T, typename F>
            struct NkConditional<false, T, F> { using type = F; };

            template<bool B, typename T, typename F>
            using NkConditional_t = typename NkConditional<B, T, F>::type;

            /**
             * - NkIsVoid : Vérifie si un type est void.
             *
             * @Description :
             * Détermine si le type T est void. Fournit une constante booléenne `value` qui est true si T est void, false sinon.
             * Utilisé dans des traits comme NkIsReferenceable.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est void, false sinon.
             *
             * @Dépendances : NkIsSame
             */
            template<typename T>
            struct NkIsVoid : NkIsSame<T, void> {};

            template<typename T>
            inline constexpr nk_bool NkIsVoid_v = NkIsVoid<T>::value;

            /**
             * - NkIsReferenceable : Vérifie si un type peut être référencé.
             *
             * @Description :
             * Détermine si un type peut être utilisé comme référence (non-void). Utilisé pour gérer les références lvalue/rvalue.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est référenciable, false sinon.
             *
             * @Dépendances : NkTrueType, NkFalseType, NkIsVoid
             */
            template<typename T>
            struct NkIsReferenceable : NkConditional<NkIsVoid<T>::value, NkFalseType, NkTrueType>::type {};

            template<typename T>
            struct NkIsReferenceable<const T> : NkIsReferenceable<T> {};

            template<typename T>
            struct NkIsReferenceable<volatile T> : NkIsReferenceable<T> {};

            template<typename T>
            struct NkIsReferenceable<const volatile T> : NkIsReferenceable<T> {};

            template<typename T>
            inline constexpr nk_bool NkIsReferenceable_v = NkIsReferenceable<T>::value;

            /**
             * - NkRemoveConst : Supprime le qualificateur const d’un type.
             *
             * @Description :
             * Enlève le qualificateur const d’un type T. Utilisé dans des traits comme NkRemoveCV.
             *
             * @Template :
             * - (typename T) : Type à modifier.
             *
             * @Members :
             * - (type) type : Type sans const.
             *
             * @Dépendances : Aucune
             */
            template<typename T>
            struct NkRemoveConst { using type = T; };

            template<typename T>
            struct NkRemoveConst<const T> { using type = T; };

            template<typename T>
            using NkRemoveConst_t = typename NkRemoveConst<T>::type;

            /**
             * - NkRemoveVolatile : Supprime le qualificateur volatile d’un type.
             *
             * @Description :
             * Enlève le qualificateur volatile d’un type T. Utilisé dans des traits comme NkRemoveCV.
             *
             * @Template :
             * - (typename T) : Type à modifier.
             *
             * @Members :
             * - (type) type : Type sans volatile.
             *
             * @Dépendances : Aucune
             */
            template<typename T>
            struct NkRemoveVolatile { using type = T; };

            template<typename T>
            struct NkRemoveVolatile<volatile T> { using type = T; };

            template<typename T>
            using NkRemoveVolatile_t = typename NkRemoveVolatile<T>::type;

            /**
             * - NkRemoveCV : Supprime les qualificateurs const et volatile d’un type.
             *
             * @Description :
             * Enlève à la fois const et volatile d’un type T. Utilisé pour normaliser les types dans des traits comme NkIsIntegral.
             *
             * @Template :
             * - (typename T) : Type à modifier.
             *
             * @Members :
             * - (type) type : Type sans const ni volatile.
             *
             * @Dépendances : NkRemoveConst, NkRemoveVolatile
             */
            template<typename T>
            struct NkRemoveCV {
                using type = NkRemoveVolatile_t<NkRemoveConst_t<T>>;
            };

            template<typename T>
            using NkRemoveCV_t = typename NkRemoveCV<T>::type;

            /**
             * - NkIsIntegral : Vérifie si un type est intégral.
             *
             * @Description :
             * Détermine si un type est un type intégral (bool, char, int, etc.). Remplace std::is_integral sans dépendance STL, sauf pour la gestion des qualificateurs.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est intégral, false sinon.
             *
             * @Dépendances : NkBoolConstant, NkRemoveCV
             */
            template<typename T>
            struct NkIsIntegral : NkFalseType {};

            template<> struct NkIsIntegral<bool> : NkTrueType {};
            template<> struct NkIsIntegral<char> : NkTrueType {};
            template<> struct NkIsIntegral<signed char> : NkTrueType {};
            template<> struct NkIsIntegral<unsigned char> : NkTrueType {};
            template<> struct NkIsIntegral<nk_char16> : NkTrueType {};
            template<> struct NkIsIntegral<nk_char32> : NkTrueType {};
            template<> struct NkIsIntegral<short> : NkTrueType {};
            template<> struct NkIsIntegral<unsigned short> : NkTrueType {};
            template<> struct NkIsIntegral<int> : NkTrueType {};
            template<> struct NkIsIntegral<unsigned int> : NkTrueType {};
            template<> struct NkIsIntegral<long> : NkTrueType {};
            template<> struct NkIsIntegral<unsigned long> : NkTrueType {};
            template<> struct NkIsIntegral<long long> : NkTrueType {};
            template<> struct NkIsIntegral<unsigned long long> : NkTrueType {};

            #if defined(NKENTSEU_PLATFORM_WINDOWS)
            template<> struct NkIsIntegral<nk_wchar> : NkTrueType {};
            #endif

            #if defined(__cpp_char8_t)
            template<> struct NkIsIntegral<nk_char8> : NkTrueType {};
            #endif

            template<typename T>
            struct NkIsIntegral<const T> : NkIsIntegral<T> {};
            template<typename T>
            struct NkIsIntegral<volatile T> : NkIsIntegral<T> {};
            template<typename T>
            struct NkIsIntegral<const volatile T> : NkIsIntegral<T> {};

            template<typename T>
            inline constexpr nk_bool NkIsIntegral_v = NkIsIntegral<NkRemoveCV_t<T>>::value;

            /**
             * - NkIsFloatingPoint : Vérifie si un type est à virgule flottante.
             *
             * @Description :
             * Détermine si un type est un type à virgule flottante (float, double, long double).
             * Remplace std::is_floating_point sans dépendance STL, sauf pour la gestion des qualificateurs.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est à virgule flottante, false sinon.
             *
             * @Dépendances : NkBoolConstant, NkRemoveCV
             */
            template<typename T>
            struct NkIsFloatingPoint : NkFalseType {};

            template<> struct NkIsFloatingPoint<float> : NkTrueType {};
            template<> struct NkIsFloatingPoint<double> : NkTrueType {};
            template<> struct NkIsFloatingPoint<long double> : NkTrueType {};

            template<typename T>
            struct NkIsFloatingPoint<const T> : NkIsFloatingPoint<T> {};
            template<typename T>
            struct NkIsFloatingPoint<volatile T> : NkIsFloatingPoint<T> {};
            template<typename T>
            struct NkIsFloatingPoint<const volatile T> : NkIsFloatingPoint<T> {};

            template<typename T>
            inline constexpr nk_bool NkIsFloatingPoint_v = NkIsFloatingPoint<NkRemoveCV_t<T>>::value;

            /**
             * - NkIsArithmetic : Vérifie si un type est arithmétique.
             *
             * @Description :
             * Détermine si un type est intégral ou à virgule flottante. Utilisé dans des traits comme NkIsStandardLayout.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est arithmétique, false sinon.
             *
             * @Dépendances : NkIsIntegral, NkIsFloatingPoint
             */
            template<typename T>
            struct NkIsArithmetic : NkBoolConstant<NkIsIntegral_v<T> || NkIsFloatingPoint_v<T>> {};

            template<typename T>
            inline constexpr nk_bool NkIsArithmetic_v = NkIsArithmetic<T>::value;

            /**
             * - NkIsBooleanNatif : Vérifie si un type est un booléen natif.
             *
             * @Description :
             * Détermine si un type est exactement bool. Utilisé pour des vérifications spécifiques de type booléen.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est bool, false sinon.
             *
             * @Dépendances : NkIsSame
             */
            template<typename T>
            struct NkIsBooleanNatif : NkIsSame<T, nk_bool> {};

            template<typename T>
            inline constexpr nk_bool NkIsBooleanNatif_v = NkIsBooleanNatif<T>::value;

            /**
             * - NkIsSigned : Vérifie si un type est signé.
             *
             * @Description :
             * Détermine si un type est signé (entiers signés ou flottants). Remplace std::is_signed sans dépendance STL.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est signé, false sinon.
             *
             * @Dépendances : NkIsIntegral, NkIsFloatingPoint, NkRemoveCV
             */
            template<typename T>
            struct NkIsSigned : NkFalseType {};

            template<> struct NkIsSigned<signed char> : NkTrueType {};
            template<> struct NkIsSigned<short> : NkTrueType {};
            template<> struct NkIsSigned<int> : NkTrueType {};
            template<> struct NkIsSigned<long> : NkTrueType {};
            template<> struct NkIsSigned<long long> : NkTrueType {};
            template<> struct NkIsSigned<float> : NkTrueType {};
            template<> struct NkIsSigned<double> : NkTrueType {};
            template<> struct NkIsSigned<long double> : NkTrueType {};

            template<typename T>
            struct NkIsSigned<const T> : NkIsSigned<T> {};
            template<typename T>
            struct NkIsSigned<volatile T> : NkIsSigned<T> {};
            template<typename T>
            struct NkIsSigned<const volatile T> : NkIsSigned<T> {};

            template<typename T>
            inline constexpr nk_bool NkIsSigned_v = NkIsSigned<NkRemoveCV_t<T>>::value;

            /**
             * - NkIsUnsigned : Vérifie si un type est non signé.
             *
             * @Description :
             * Détermine si un type est non signé (entiers non signés). Remplace std::is_unsigned sans dépendance STL.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est non signé, false sinon.
             *
             * @Dépendances : NkIsIntegral, NkRemoveCV
             */
            template<typename T>
            struct NkIsUnsigned : NkFalseType {};

            template<> struct NkIsUnsigned<unsigned char> : NkTrueType {};
            template<> struct NkIsUnsigned<unsigned short> : NkTrueType {};
            template<> struct NkIsUnsigned<unsigned int> : NkTrueType {};
            template<> struct NkIsUnsigned<unsigned long> : NkTrueType {};
            template<> struct NkIsUnsigned<unsigned long long> : NkTrueType {};

            template<typename T>
            struct NkIsUnsigned<const T> : NkIsUnsigned<T> {};
            template<typename T>
            struct NkIsUnsigned<volatile T> : NkIsUnsigned<T> {};
            template<typename T>
            struct NkIsUnsigned<const volatile T> : NkIsUnsigned<T> {};

            template<typename T>
            inline constexpr nk_bool NkIsUnsigned_v = NkIsUnsigned<NkRemoveCV_t<T>>::value;

            /**
             * - NkRemoveReference : Supprime les références d’un type.
             *
             * @Description :
             * Enlève les références lvalue (T&) et rvalue (T&&) d’un type T. Utilisé dans des traits comme NkIsReference.
             *
             * @Template :
             * - (typename T) : Type à modifier.
             *
             * @Members :
             * - (type) type : Type sans référence.
             * - (const_thru_type) const_thru_type : Type avec const préservé à travers la référence.
             *
             * @Dépendances : Aucune
             */
            template<typename T>
            struct NkRemoveReference { 
                using type = T;
                using const_thru_type = const T;
            };

            template<typename T>
            struct NkRemoveReference<T&> { 
                using type = T;
                using const_thru_type = const T&;
            };

            template<typename T>
            struct NkRemoveReference<T&&> { 
                using type = T;
                using const_thru_type = const T&&;
            };

            template<typename T>
            using NkRemoveReference_t = typename NkRemoveReference<T>::type;

            /**
             * - NkAddRValueReference : Ajoute une référence rvalue à un type.
             *
             * @Description :
             * Ajoute une référence rvalue (T&&) à un type T si celui-ci est référenciable.
             * Utilisé dans des traits comme NkDeclVal.
             *
             * @Template :
             * - (typename T) : Type à modifier.
             *
             * @Members :
             * - (type) type : Type avec référence rvalue ou inchangé si non référenciable.
             *
             * @Dépendances : NkIsReferenceable, NkEnableIf
             */
            template<typename T, typename = void>
            struct NkAddRValueReference_impl {
                using type = T&&;
            };

            template<typename T>
            struct NkAddRValueReference_impl<T, NkEnableIf_t<!NkIsReferenceable<T>::value>> {
                using type = T;
            };

            template<typename T>
            struct NkAddRValueReference {
                using type = typename NkAddRValueReference_impl<T>::type;
            };

            template<typename T>
            using NkAddRValueReference_t = typename NkAddRValueReference<T>::type;

            /**
             * - NkAddLValueReference : Ajoute une référence lvalue à un type.
             *
             * @Description :
             * Ajoute une référence lvalue (T&) à un type T si celui-ci est référenciable.
             * Utilisé dans des traits comme NkForward.
             *
             * @Template :
             * - (typename T) : Type à modifier.
             *
             * @Members :
             * - (type) type : Type avec référence lvalue ou inchangé si non référenciable.
             *
             * @Dépendances : NkIsReferenceable, NkConditional
             */
            template<typename T>
            struct NkAddLValueReference {
                using type = typename NkConditional<NkIsReferenceable<T>::value, T&, T>::type;
            };

            template<typename T>
            using NkAddLValueReference_t = typename NkAddLValueReference<T>::type;

            /**
             * - NkIsReference : Vérifie si un type est une référence.
             *
             * @Description :
             * Détermine si un type est une référence (lvalue ou rvalue). Remplace std::is_reference sans dépendance STL.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est une référence, false sinon.
             *
             * @Dépendances : NkIsSame, NkRemoveReference
             */
            template<typename T>
            struct NkIsReference : NkBoolConstant<!NkIsSame<T, NkRemoveReference_t<T>>::value> {};

            template<typename T>
            inline constexpr nk_bool NkIsReference_v = NkIsReference<T>::value;

            /**
             * - NkIsLValueReference : Vérifie si un type est une référence lvalue.
             *
             * @Description :
             * Détermine si un type est une référence lvalue (T&). Remplace std::is_lvalue_reference sans dépendance STL.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est une référence lvalue, false sinon.
             *
             * @Dépendances : NkIsSame, NkRemoveReference
             */
            template<typename T>
            struct NkIsLValueReference : NkBoolConstant<NkIsSame<T, NkRemoveReference_t<T>&>::value> {};

            template<typename T>
            inline constexpr nk_bool NkIsLValueReference_v = NkIsLValueReference<T>::value;

            /**
             * - NkIsRValueReference : Vérifie si un type est une référence rvalue.
             *
             * @Description :
             * Détermine si un type est une référence rvalue (T&&). Remplace std::is_rvalue_reference sans dépendance STL.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est une référence rvalue, false sinon.
             *
             * @Dépendances : NkIsSame, NkRemoveReference
             */
            template<typename T>
            struct NkIsRValueReference : NkBoolConstant<NkIsSame<T, NkRemoveReference_t<T>&&>::value> {};

            template<typename T>
            inline constexpr nk_bool NkIsRValueReference_v = NkIsRValueReference<T>::value;

            /**
             * - NkMakeVoid : Crée un type void pour les contextes SFINAE.
             *
             * @Description :
             * Fournit un type void générique pour les contextes de métaprogrammation comme NkIsCompleteType.
             *
             * @Template :
             * - (class...) : Pack variadique de types (ignoré).
             *
             * @Members :
             * - (type) type : Type void.
             *
             * @Dépendances : Aucune
             */
            template<class...>
            struct NkMakeVoid { using type = void; };

            template<class... T>
            using NkVoid_t = typename NkMakeVoid<T...>::type;

            /**
             * - NkNullTerminator : Définit le caractère nul pour chaque type de caractère.
             *
             * @Description :
             * Fournit le caractère nul pour différents types de caractères (char, nk_wchar, etc.).
             * Utilisé pour manipuler des chaînes de caractères de manière portable.
             *
             * @Template :
             * - (typename CharT) : Type de caractère.
             *
             * @Members :
             * - (static constexpr CharT) value : Caractère nul pour CharT.
             *
             * @Dépendances : Aucune
             */
            template<typename CharT>
            struct NkNullTerminator {
                static constexpr CharT value = CharT(0);
            };

            template<> struct NkNullTerminator<nk_char>  { static constexpr nk_char  value = '\0'; };
            template<> struct NkNullTerminator<nk_char16> { static constexpr nk_char16 value = u'\0'; };
            template<> struct NkNullTerminator<nk_char32> { static constexpr nk_char32 value = U'\0'; };

            #if defined(NKENTSEU_PLATFORM_WINDOWS)
            template<> struct NkNullTerminator<nk_wchar>  { static constexpr nk_wchar  value = L'\0'; };
            #endif

            #if defined(__cpp_char8)
            template<> struct NkNullTerminator<nk_char8>  { static constexpr nk_char8  value = u8'\0'; };
            #endif

            /**
             * - NkDisjunction : Effectue une disjonction logique (OR) sur une liste de traits.
             *
             * @Description :
             * Effectue un OU logique sur les valeurs des traits fournis. Remplace std::disjunction sans dépendance STL.
             * Utilisé dans des traits comme NkIsAnyOf.
             *
             * @Template :
             * - (typename... Ts) : Pack variadique de traits.
             *
             * @Members :
             * - (static constexpr bool) value : True si au moins un trait a value=true, false sinon.
             *
             * @Dépendances : NkFalseType, NkConditional
             */
            template<typename... Ts>
            struct NkDisjunction : NkFalseType {};

            template<typename First, typename... Rest>
            struct NkDisjunction<First, Rest...> : NkConditional<First::value, First, NkDisjunction<Rest...>>::type {};

            template<typename... Ts>
            inline constexpr nk_bool NkDisjunction_v = NkDisjunction<Ts...>::value;

            /**
             * - NkIsAnyOf : Vérifie si un type est l’un des types d’un pack variadique.
             *
             * @Description :
             * Détermine si un type T est identique à l’un des types dans Types... Utilisé dans des traits comme NkIsUnique.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             * - (typename... Types) : Pack variadique de types à comparer.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est dans Types..., false sinon.
             *
             * @Dépendances : NkIsSame, NkDisjunction
             */
            template<typename T, typename... Types>
            struct NkIsAnyOf : NkDisjunction<NkIsSame<T, Types>...> {};

            template<typename T, typename... Types>
            inline constexpr nk_bool NkIsAnyOf_v = NkIsAnyOf<T, Types...>::value;

            /**
             * - NkIsConstantEvaluated : Vérifie si le contexte est en évaluation constante.
             *
             * @Description :
             * Utilise l’intrinsèque __builtin_is_constant_evaluated pour déterminer si le code est en évaluation constante.
             *
             * @Return : bool (true si en évaluation constante, false sinon).
             *
             * @Dépendances : Aucune
             */
            NKENTSEU_NODISCARD constexpr nk_bool NkIsConstantEvaluated() noexcept {
                return __builtin_is_constant_evaluated();
            }

            /**
             * - NkAddConst : Ajoute le qualificateur const à un type.
             *
             * @Description :
             * Ajoute le qualificateur const à un type T. Utilisé dans des traits comme NkAddCV.
             *
             * @Template :
             * - (typename T) : Type à modifier.
             *
             * @Members :
             * - (type) type : Type avec const ajouté.
             *
             * @Dépendances : Aucune
             */
            template<typename T>
            struct NkAddConst { using type = const T; };

            template<typename T>
            using NkAddConst_t = typename NkAddConst<T>::type;

            /**
             * - NkAddVolatile : Ajoute le qualificateur volatile à un type.
             *
             * @Description :
             * Ajoute le qualificateur volatile à un type T. Utilisé dans des traits comme NkAddCV.
             *
             * @Template :
             * - (typename T) : Type à modifier.
             *
             * @Members :
             * - (type) type : Type avec volatile ajouté.
             *
             * @Dépendances : Aucune
             */
            template<typename T>
            struct NkAddVolatile { using type = volatile T; };

            template<typename T>
            using NkAddVolatile_t = typename NkAddVolatile<T>::type;

            /**
             * - NkAddCV : Ajoute les qualificateurs const et volatile à un type.
             *
             * @Description :
             * Ajoute à la fois const et volatile à un type T. Utilisé pour manipuler des types qualifiés.
             *
             * @Template :
             * - (typename T) : Type à modifier.
             *
             * @Members :
             * - (type) type : Type avec const et volatile ajoutés.
             *
             * @Dépendances : Aucune
             */
            template<typename T>
            struct NkAddCV { using type = const volatile T; };

            template<typename T>
            using NkAddCV_t = typename NkAddCV<T>::type;

            /**
             * - NkIsConst : Vérifie si un type est const-qualifié.
             *
             * @Description :
             * Détermine si un type T est qualifié par const. Remplace std::is_const sans dépendance STL.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est const, false sinon.
             *
             * @Dépendances : NkIsSame, NkRemoveConst
             */
            template<typename T>
            struct NkIsConst : NkBoolConstant<!NkIsSame<T, NkRemoveConst_t<T>>::value> {};

            template<typename T>
            inline constexpr nk_bool NkIsConst_v = NkIsConst<T>::value;

            /**
             * - NkIsVolatile : Vérifie si un type est volatile-qualifié.
             *
             * @Description :
             * Détermine si un type T est qualifié par volatile. Remplace std::is_volatile sans dépendance STL.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est volatile, false sinon.
             *
             * @Dépendances : NkIsSame, NkRemoveVolatile
             */
            template<typename T>
            struct NkIsVolatile : NkBoolConstant<!NkIsSame<T, NkRemoveVolatile_t<T>>::value> {};

            template<typename T>
            inline constexpr nk_bool NkIsVolatile_v = NkIsVolatile<T>::value;

            /**
             * - NkNegation : Effectue une négation logique d'un trait.
             *
             * @Description :
             * Cette structure template retourne l'inverse de la valeur `value` d'un trait.
             *
             * @Template :
             * - (typename T) : Trait à inverser.
             *
             * @Members :
             * - (type) type : Type résultant (`NkTrueType` ou `NkFalseType`).
             * - (static constexpr bool) value : Résultat de la négation logique.
             */
            template<typename T>
            struct NkNegation : NkBoolConstant<!T::value> {};

            template<typename T>
            inline constexpr nk_bool NkNegation_v = NkNegation<T>::value;
            

            /**
             * @Struct NkTypeAt
             * @Description Récupère le type du N-ième élément d'une liste de types variadiques
             * 
             * @Template :
             * - (usize I) : Index de l'élément à récupérer
             * - (typename... Args) : Liste des types
             * 
             * @Members :
             * - (typedef type) : Type à l'index I
             */
            template<nk_usize I, typename... Args>
            struct NkTypeAt;

            // Cas de base : index 0
            template<typename T, typename... Rest>
            struct NkTypeAt<0, T, Rest...> {
                using type = T;
            };

            // Cas récursif
            template<nk_usize I, typename T, typename... Rest>
            struct NkTypeAt<I, T, Rest...> {
                using type = typename NkTypeAt<I - 1, Rest...>::type;
            };

            // Alias d'accès rapide
            template<nk_usize I, typename... Args>
            using NkTypeAt_t = typename NkTypeAt<I, Args...>::type;

            template <nk_int32> struct NkIntegerForSize;
            template <>      struct NkIntegerForSize<1> { typedef nk_uint8  Unsigned; typedef nk_int8  Signed; };
            template <>      struct NkIntegerForSize<2> { typedef nk_uint16 Unsigned; typedef nk_int16 Signed; };
            template <>      struct NkIntegerForSize<4> { typedef nk_uint32 Unsigned; typedef nk_int32 Signed; };
            template <>      struct NkIntegerForSize<8> { typedef nk_uint64 Unsigned; typedef nk_int64 Signed; };
            template <class T> struct NkIntegerForSizeof: NkIntegerForSize<sizeof(T)> { };
            using nkuintptr = NkIntegerForSizeof<nk_ptr>::Unsigned;
            using nkptrdiff = NkIntegerForSizeof<nk_ptr>::Signed;
            using nkintptr = nkptrdiff;
            
            /**
             * - IsNoexceptMoveConstructible : Trait pour vérifier si le constructeur de déplacement est noexcept.
             *
             * @Description :
             * Cette structure détermine si le type `T` a un constructeur de déplacement garanti
             * `noexcept`. Utilisée par `NkMoveIfNoexcept` pour choisir entre déplacement et copie.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Member :
             * - (static constexpr bool) Value : `true` si le constructeur de déplacement est noexcept, sinon `false`.
             */
            template<typename T>
            struct NkIsNoexceptMoveConstructible {
                static constexpr nk_bool Value = __is_abstract(T) ? false : __is_nothrow_constructible(T, T&&);
                // static constexpr bool Value = NkIsAbstract_v<T> ? false : __is_nothrow_constructible(T, T&&);
            };

            /**
             * - NkMoveIfNoexcept : Déplace un objet si son constructeur de déplacement est noexcept.
             *
             * @Description :
             * Cette fonction retourne une référence rvalue pour déplacer l'objet `value` si son
             * constructeur de déplacement est garanti `noexcept`. Sinon, elle retourne une référence
             * lvalue pour copier l'objet, assurant une sécurité forte contre les exceptions.
             * Utilisée pour optimiser les opérations comme le redimensionnement ou l'insertion dans
             * des conteneurs comme `NkArray`.
             *
             * @Template :
             * - (typename T) : Type de l'objet à déplacer ou copier.
             *
             * @param (T&) value : Objet à déplacer ou copier.
             * @return (T&& or T&) : Référence rvalue si déplacement sûr, sinon référence lvalue.
             *
             * Exemple :
             * struct Data { Data(Data&&) noexcept {} };
             * Data obj;
             * auto moved = NkMoveIfNoexcept(obj); // Retourne Data&& (déplacement)
             *
             * struct UnsafeData { UnsafeData(UnsafeData&&) {} };
             * UnsafeData unsafeObj;
             * auto copied = NkMoveIfNoexcept(unsafeObj); // Retourne UnsafeData& (copie)
             */
            template<typename T>
            constexpr auto NkMoveIfNoexcept(T& value) noexcept -> typename NkConditional<
                NkIsNoexceptMoveConstructible<T>::Value,
                T&&,
                T&
            >::type {
                return static_cast<typename NkConditional<
                    NkIsNoexceptMoveConstructible<T>::Value,
                    T&&,
                    T&
                >::type>(value);
            }
            
            template<typename T, typename... Args>
            struct NkAreConvertible {
                static constexpr bool value = true;
            };

            template<typename T, typename First, typename... Rest>
            struct NkAreConvertible<T, First, Rest...> {
                static constexpr bool value = __is_convertible_to(First, T) && NkAreConvertible<T, Rest...>::value;
            };

            template<template<typename...> class Template, typename T>
            struct NkIsTemplateInstanceOf : NkFalseType {};

            template<template<typename...> class Template, typename... Args>
            struct NkIsTemplateInstanceOf<Template, Template<Args...>> : NkTrueType {};


            template <class _Ty>
            NKENTSEU_NODISCARD constexpr _Ty* NkAddressOf(_Ty& _Val) noexcept {
                return __builtin_addressof(_Val);
            }

            template <class _Ty>
            const _Ty* NkAddressOf(const _Ty&&) = delete;

            /**
             * - NkPackSize : @Computes the size of a variadic template pack.
             *
             * @Description :
             * This metafunction calculates the number of types in a parameter pack.
             *
             * @Template :
             * - (typename... Ts) : The parameter pack.
             * @return (usize) : The number of types in the pack.
             */
            template<typename... Ts>
            struct NkPackSize {
                static constexpr nk_usize value = sizeof...(Ts);
            };

            
            /**
             * - NkInvokeResult : @Détermine le type de retour d'une invocation.
             *
             * @Description :
             * Cette structure template utilise SFINAE pour déterminer le type de retour de l'invocation F(Args...).
             * Si l'invocation n'est pas valide, le type est void.
             *
             * @Template :
             * - (typename F) : Type invocable.
             * - (typename... Args) : Types des arguments pour l'invocation.
             *
             * @Members :
             * - (type) type : Type de retour de l'invocation ou void si non valide.
             */
            template<typename F, typename... Args>
            struct NkInvokeResult {
            private:
                /**
                 * - test : @Obtient le type de retour de l'invocation.
                 *
                 * @Description :
                 * Retourne le type de l'expression F(Args...) si elle est valide.
                 *
                 * @Template :
                 * - (typename U) : Type invocable.
                 * @param (int) : Paramètre pour résolution SFINAE.
                 * @return (NkDeclType(...)) : Type de retour de l'invocation.
                 */
                template<typename U>
                static auto test(nk_int32) -> NkDeclType(NkDeclVal<U>()(NkDeclVal<Args>()...));

                /**
                 * - test : @Spécialisation pour l'échec de l'invocation.
                 *
                 * @Description :
                 * Retourne void si l'invocation n'est pas valide.
                 *
                 * @param (...) : Paramètre pour résolution SFINAE.
                 * @return (void) : Si l'invocation échoue.
                 */
                static auto test(...) -> void;

            public:
                using type = NkDeclType(test<F>(0));
            };

            /**
             * @Alias NkInvokeResult_t
             * @Description Alias pour accéder au type de retour d'une invocation.
             * @UnderlyingType typename NkInvokeResult<F, Args...>::type
             */
            template<typename F, typename... Args>
            using NkInvokeResult_t = typename NkInvokeResult<F, Args...>::type;

            

            /**
             * - NkIsNothrowInvocable : @Vérifie si un type est invocable sans lever d'exceptions.
             *
             * @Description :
             * Cette structure template utilise SFINAE pour vérifier si F peut être invoqué avec Args
             * dans un contexte noexcept (sans lever d'exceptions).
             *
             * @Template :
             * - (typename F) : Type invocable.
             * - (typename... Args) : Types des arguments pour l'invocation.
             *
             * @Members :
             * - (type) type : Résultat du test (NkTrueType ou NkFalseType).
             * - (static constexpr bool) value : Indique si l'invocation est noexcept.
             */
            template<typename F, typename... Args>
            struct NkIsNothrowInvocable {
            private:
                /**
                 * - test : @Teste si F est invocable sans exceptions.
                 *
                 * @Description :
                 * Vérifie si l'expression F(Args...) est marquée comme noexcept.
                 * Retourne NkBoolConstant avec la valeur de noexcept.
                 *
                 * @Template :
                 * - (typename U) : Type invocable.
                 * @param (int) : Paramètre pour résolution SFINAE.
                 * @return (NkBoolConstant) : Résultat de l'évaluation noexcept.
                 */
                template<typename U>
                static auto test(nk_int32) -> NkBoolConstant<noexcept(NkDeclVal<U>()(NkDeclVal<Args>()...))>;

                /**
                 * - test : @Spécialisation pour l'échec de l'invocation.
                 *
                 * @Description :
                 * Retourne NkFalseType si l'invocation n'est pas valide.
                 *
                 * @param (...) : Paramètre pour résolution SFINAE.
                 * @return (NkFalseType) : Si l'invocation échoue.
                 */
                static auto test(...) -> NkFalseType;

            public:
                using type = NkDeclType(test<F>(0));
                static constexpr bool value = type::value;
            };

            /**
             * @Description : Constante booléenne indiquant si un type est invocable sans lever d'exceptions.
             */
            template<typename F, typename... Args>
            inline constexpr nk_bool NkIsNothrowInvocable_v = NkIsNothrowInvocable<F, Args...>::value;

            /**
             * - NkReferenceWrapper : Encapsule une référence à un objet pour permettre la copie et l'invocation.
             *
             * @Description :
             * Cette classe template stocke une référence lvalue à un objet de type T, permettant
             * une copie et une affectation, une conversion implicite vers T&, et l'invocation
             * de fonctions membres via l'opérateur () ou NkInvoke.
             *
             * @Template :
             * - (typename T) : Type de l'objet référencé.
             *
             * @Members :
             * - (T*) ptr : Pointeur vers l'objet référencé.
             */
            template<typename T>
            class NkReferenceWrapper {
            public:
                // Type sous-jacent
                using type = T;

                /**
                 * - Constructor : Construit une NkReferenceWrapper à partir d'une référence lvalue.
                 *
                 * @Description :
                 * Stocke l'adresse de l'objet référencé.
                 *
                 * @param (T& ref) : Référence lvalue à encapsuler.
                 */
                constexpr NkReferenceWrapper(T& ref) noexcept : ptr(NkAddressOf(ref)) {}

                /**
                 * - Copy Constructor : Construit une copie d'une autre NkReferenceWrapper.
                 *
                 * @param (const NkReferenceWrapper& other) : Autre instance à copier.
                 */
                constexpr NkReferenceWrapper(const NkReferenceWrapper& other) noexcept = default;

                /**
                 * - Assignment Operator : Assigne une autre NkReferenceWrapper.
                 *
                 * @param (const NkReferenceWrapper& other) : Autre instance à assigner.
                 * @return (NkReferenceWrapper&) : Référence à l'instance courante.
                 */
                constexpr NkReferenceWrapper& operator=(const NkReferenceWrapper& other) noexcept = default;

                /**
                 * - Conversion Operator : Convertit implicitement en référence T&.
                 *
                 * @Description :
                 * Permet d'utiliser l'instance comme une référence T&.
                 *
                 * @return (T&) : Référence à l'objet encapsulé.
                 */
                constexpr operator T&() const noexcept { return *ptr; }

                /**
                 * - get : Accède à la référence encapsulée.
                 *
                 * @Description :
                 * Retourne une référence lvalue à l'objet encapsulé.
                 *
                 * @return (T&) : Référence à l'objet.
                 */
                NKENTSEU_NODISCARD constexpr T& get() const noexcept { return *ptr; }

                /**
                 * - operator() : Invoque une fonction membre sur l'objet référencé.
                 *
                 * @Description :
                 * Utilise NkInvoke pour appeler une fonction membre sur l'objet encapsulé.
                 *
                 * @Template :
                 * - (typename... Args) : Types des arguments de la fonction membre.
                 * @param (Args&&... args) : Arguments à passer à la fonction membre.
                 * @return : Résultat de l'invocation.
                 */
                template<typename... Args>
                NKENTSEU_NODISCARD constexpr auto operator()(Args&&... args) const
                    noexcept(NkIsNothrowInvocable_v<T&, Args...>)
                    -> NkInvokeResult_t<T&, Args...> {
                    return NkInvoke(get(), NkForward<Args>(args)...);
                }

            private:
                T* ptr; // Pointeur vers l'objet référencé
            };
                    
            template<typename T>
            void NkRef(const T&&) = delete;
            
            template<typename T>
            void NkCRef(const T&&) = delete;
            
            namespace detail {
                template<typename F, typename... BoundArgs>
                class NkBindExpression {
                public:
                    template<typename F2, typename... Args>
                    NkBindExpression(F2&& f, Args&&... args)
                        : mFunc(NkForward<F2>(f))
                    {}
                    
                    template<typename... CallArgs>
                    auto operator()(CallArgs&&... args) -> NkDeclType(auto) {
                        return NkInvokeWithBound(NkForward<CallArgs>(args)...);
                    }
                    
                private:
                    F mFunc;
                    
                    template<typename... CallArgs>
                    auto NkInvokeWithBound(CallArgs&&... args) -> NkDeclType(auto) {
                        return mFunc(NkForward<CallArgs>(args)...);
                    }
                };
            }

            /**
             * - NkIsReferenceWrapper : Trait pour vérifier si un type est une instance de NkReferenceWrapper.
             *
             * @Description :
             * Cette structure template détermine si un type T est une instance de NkReferenceWrapper.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             */
            template<typename T>
            struct NkIsReferenceWrapper : NkFalseType {};

            template<typename T>
            struct NkIsReferenceWrapper<NkReferenceWrapper<T>> : NkTrueType {};

            template<typename T>
            inline constexpr nk_bool NkIsReferenceWrapper_v = NkIsReferenceWrapper<T>::value;

            /**
             * - NkRef : Crée une NkReferenceWrapper à partir d'une référence lvalue.
             *
             * @Description :
             * Fonction utilitaire pour créer une instance de NkReferenceWrapper à partir d'une référence lvalue.
             *
             * @Template :
             * - (typename T) : Type de l'objet à encapsuler.
             * @param (T& t) : Référence lvalue à encapsuler.
             * @return (NkReferenceWrapper<T>) : Instance encapsulant la référence.
             */
            template<typename T>
            NKENTSEU_NODISCARD constexpr NkReferenceWrapper<T> NkRef(T& t) noexcept {
                return NkReferenceWrapper<T>(t);
            }

            /**
             * - NkRef : Surcharge pour NkReferenceWrapper (pour éviter la double encapsulation).
             *
             * @Description :
             * Retourne l'instance existante si l'argument est déjà une NkReferenceWrapper.
             *
             * @Template :
             * - (typename T) : Type de l'objet encapsulé.
             * @param (NkReferenceWrapper<T>& t) : Instance existante.
             * @return (NkReferenceWrapper<T>) : Instance inchangée.
             */
            template<typename T>
            NKENTSEU_NODISCARD constexpr NkReferenceWrapper<T> NkRef(NkReferenceWrapper<T>& t) noexcept {
                return t;
            }

            /**
             * - NkCref : Crée une NkReferenceWrapper pour une référence const lvalue.
             *
             * @Description :
             * Fonction utilitaire pour créer une instance de NkReferenceWrapper à partir d'une référence const lvalue.
             *
             * @Template :
             * - (typename T) : Type de l'objet à encapsuler.
             * @param (const T& t) : Référence const lvalue à encapsuler.
             * @return (NkReferenceWrapper<const T>) : Instance encapsulant la référence const.
             */
            template<typename T>
            NKENTSEU_NODISCARD constexpr NkReferenceWrapper<const T> NkCref(const T& t) noexcept {
                return NkReferenceWrapper<const T>(t);
            }

            /**
             * - NkCref : Surcharge pour NkReferenceWrapper const.
             *
             * @Description :
             * Retourne l'instance existante si l'argument est déjà une NkReferenceWrapper const.
             *
             * @Template :
             * - (typename T) : Type de l'objet encapsulé.
             * @param (const NkReferenceWrapper<T>& t) : Instance existante.
             * @return (NkReferenceWrapper<const T>) : Instance encapsulant la référence const.
             */
            template<typename T>
            NKENTSEU_NODISCARD constexpr NkReferenceWrapper<const T> NkCref(const NkReferenceWrapper<T>& t) noexcept {
                return NkReferenceWrapper<const T>(t.get());
            }

            /**
             * - NkConjunction : Effectue une conjonction logique (AND) sur une liste de traits.
             *
             * @Description :
             * Cette structure template évalue la conjonction logique des valeurs `value` des traits fournis.
             * Elle retourne `NkTrueType` si tous les traits sont vrais, sinon `NkFalseType`.
             *
             * @Template :
             * - (typename... Ts) : Liste des traits à évaluer.
             *
             * @Members :
             * - (type) type : Type résultant (`NkTrueType` ou `NkFalseType`).
             * - (static constexpr bool) value : Résultat de la conjonction logique.
             */
            template<typename... Ts>
            struct NkConjunction : NkTrueType {};

            template<typename T>
            struct NkConjunction<T> : T {};

            template<typename T, typename... Rest>
            struct NkConjunction<T, Rest...> : NkConditional<T::value, NkConjunction<Rest...>, NkFalseType>::type {};

            template<typename... Ts>
            inline constexpr nk_bool NkConjunction_v = NkConjunction<Ts...>::value;

            /**
             * - NkRemovePointer : Supprime un niveau de pointeur d’un type.
             *
             * @Description :
             * Enlève un niveau de pointeur d’un type T, y compris pour les pointeurs const/volatile.
             * Utilisé dans des traits comme NkIsPointer.
             *
             * @Template :
             * - (typename T) : Type à modifier.
             *
             * @Members :
             * - (type) type : Type sans un niveau de pointeur.
             *
             * @Dépendances : Aucune
             */
            template<typename T>
            struct NkRemovePointer { using type = T; };

            template<typename T>
            struct NkRemovePointer<T*> { using type = T; };

            template<typename T>
            struct NkRemovePointer<T* const> { using type = T; };

            template<typename T>
            struct NkRemovePointer<T* volatile> { using type = T; };

            template<typename T>
            struct NkRemovePointer<T* const volatile> { using type = T; };

            template<typename T>
            using NkRemovePointer_t = typename NkRemovePointer<T>::type;

            /**
             * - NkAddPointer : Ajoute un pointeur à un type.
             *
             * @Description :
             * Ajoute un niveau de pointeur (T*) à un type T. Utilisé dans des traits comme NkDecay.
             *
             * @Template :
             * - (typename T) : Type à modifier.
             *
             * @Members :
             * - (type) type : Type avec un pointeur ajouté.
             *
             * @Dépendances : Aucune
             */
            template<typename T>
            struct NkAddPointer { using type = T*; };

            template<typename T>
            using NkAddPointer_t = typename NkAddPointer<T>::type;

            /**
             * - NkIsPointer : Vérifie si un type est un pointeur.
             *
             * @Description :
             * Détermine si un type T est un pointeur. Remplace std::is_pointer sans dépendance STL.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est un pointeur, false sinon.
             *
             * @Dépendances : NkIsSame, NkRemovePointer
             */
            template<typename T>
            struct NkIsPointer : NkBoolConstant<!NkIsSame<T, NkRemovePointer_t<T>>::value> {};

            template<typename T>
            inline constexpr nk_bool NkIsPointer_v = NkIsPointer<T>::value;

            /**
             * - NkIsMemberPointer : Vérifie si un type est un pointeur de membre.
             *
             * @Description :
             * Détermine si un type T est un pointeur de membre (donnée ou fonction).
             * Utilise l’intrinsèque __is_member_pointer.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est un pointeur de membre, false sinon.
             *
             * @Dépendances : NkBoolConstant
             */
            template<typename T>
            struct NkIsMemberPointer : NkBoolConstant<__is_member_pointer(T)> {};

            template<typename T>
            inline constexpr nk_bool NkIsMemberPointer_v = NkIsMemberPointer<T>::value;

            /**
             * - NkIsNothrowDestructible : Vérifie si un type est destructible sans exception.
             *
             * @Description :
             * Cette structure template utilise `__is_nothrow_destructible` pour vérifier si le destructeur de T est marqué comme `noexcept`.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             */
            template<typename T>
            struct NkIsNothrowDestructible : NkBoolConstant<std::is_nothrow_destructible<T>::value> {};

            template<typename T>
            inline constexpr nk_bool NkIsNothrowDestructible_v = NkIsNothrowDestructible<T>::value;
            
            /**
             * - NkIsMemberFunctionPointer : Vérifie si un type est un pointeur de fonction membre.
             *
             * @Description :
             * Cette structure template utilise `__is_member_function_pointer` pour vérifier si T est un pointeur de fonction membre.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             */
            template<typename T>
            struct NkIsMemberFunctionPointer : NkBoolConstant<__is_member_function_pointer(T)> {};

            template<typename T>
            inline constexpr nk_bool NkIsMemberFunctionPointer_v = NkIsMemberFunctionPointer<T>::value;

            /**
             * - NkIsMemberObjectPointer : Vérifie si un type est un pointeur de donnée membre.
             *
             * @Description :
             * Cette structure template utilise `__is_member_object_pointer` pour vérifier si T est un pointeur de donnée membre.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             */
            template<typename T>
            struct NkIsMemberObjectPointer : NkBoolConstant<__is_member_object_pointer(T)> {};

            template<typename T>
            inline constexpr nk_bool NkIsMemberObjectPointer_v = NkIsMemberObjectPointer<T>::value;

            /**
             * - NkIsArray : Vérifie si un type est un tableau.
             *
             * @Description :
             * Détermine si un type T est un tableau (de taille fixe ou indéfinie).
             * Remplace std::is_array sans dépendance STL.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est un tableau, false sinon.
             *
             * @Dépendances : NkFalseType, NkTrueType
             */
            template<typename T>
            struct NkIsArray : NkFalseType {};

            template<typename T, nk_usize N>
            struct NkIsArray<T[N]> : NkTrueType {};

            template<typename T>
            struct NkIsArray<T[]> : NkTrueType {};

            template<typename T>
            inline constexpr nk_bool NkIsArray_v = NkIsArray<T>::value;

            /**
             * - NkIsBoundedArray : Vérifie si un type est un tableau de taille fixe.
             *
             * @Description :
             * Cette structure template vérifie si T est un tableau avec une taille définie (T[N]).
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             */
            template<typename T>
            struct NkIsBoundedArray : NkFalseType {};

            template<typename T, nk_usize N>
            struct NkIsBoundedArray<T[N]> : NkTrueType {};

            template<typename T>
            inline constexpr nk_bool NkIsBoundedArray_v = NkIsBoundedArray<T>::value;

            /**
             * - NkRemoveExtent : Supprime une dimension d’un type tableau.
             *
             * @Description :
             * Enlève une dimension d’un type tableau T. Remplace std::remove_extent sans dépendance STL.
             *
             * @Template :
             * - (typename T) : Type à modifier.
             *
             * @Members :
             * - (type) type : Type avec une dimension de tableau enlevée.
             *
             * @Dépendances : Aucune
             */
            template<typename T>
            struct NkRemoveExtent { using type = T; };

            template<typename T, usize N>
            struct NkRemoveExtent<T[N]> { using type = T; };

            template<typename T>
            struct NkRemoveExtent<T[]> { using type = T; };

            template<typename T>
            using NkRemoveExtent_t = typename NkRemoveExtent<T>::type;

            /**
             * - NkRemoveAllExtents : Supprime toutes les dimensions d’un type tableau.
             *
             * @Description :
             * Enlève toutes les dimensions d’un type tableau T. Remplace std::remove_all_extents sans dépendance STL.
             *
             * @Template :
             * - (typename T) : Type à modifier.
             *
             * @Members :
             * - (type) type : Type sans aucune dimension de tableau.
             *
             * @Dépendances : NkRemoveExtent
             */
            template<typename T>
            struct NkRemoveAllExtents { using type = T; };

            template<typename T, nk_usize N>
            struct NkRemoveAllExtents<T[N]> { using type = typename NkRemoveAllExtents<T>::type; };

            template<typename T>
            struct NkRemoveAllExtents<T[]> { using type = typename NkRemoveAllExtents<T>::type; };

            template<typename T>
            using NkRemoveAllExtents_t = typename NkRemoveAllExtents<T>::type;

            /**
             * - NkIsFunction : Vérifie si un type est une fonction.
             *
             * @Description :
             * Détermine si un type T est un type fonction (non const, non référence, non tableau).
             * Utilise une heuristique basée sur les traits existants.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est une fonction, false sinon.
             *
             * @Dépendances : NkIsConst, NkIsReference, NkIsArray
             */
            template<typename T>
            struct NkIsFunction : NkBoolConstant<
                !NkIsConst_v<const T> && !NkIsReference_v<T> && !NkIsArray_v<T>
            > {};

            template<typename T>
            inline constexpr nk_bool NkIsFunction_v = NkIsFunction<T>::value;

            /**
             * - NkDecay : Applique les règles de dégradation de type.
             *
             * @Description :
             * Applique les règles de dégradation de type (suppression des références, CV-qualificateurs, conversion des tableaux/fonctions en pointeurs).
             * Remplace std::decay sans dépendance STL.
             *
             * @Template :
             * - (typename T) : Type à dégrader.
             *
             * @Members :
             * - (type) type : Type dégradé.
             *
             * @Dépendances : NkRemoveCV, NkRemoveReference, NkIsArray, NkIsFunction, NkAddPointer, NkConditional
             */
            template<typename T>
            struct NkDecay {
                using U = NkRemoveCV_t<NkRemoveReference_t<T>>;
                using type = NkConditional_t<
                    NkIsArray_v<U>,
                    NkAddPointer_t<NkRemoveExtent_t<U>>,
                    NkConditional_t<
                        NkIsFunction_v<U>,
                        NkAddPointer_t<U>,
                        U
                    >
                >;
            };

            template<typename T>
            using NkDecayT = typename NkDecay<T>::type;

            /**
             * - NkIsDefaultConstructible : Vérifie si un type est constructible par défaut.
             *
             * @Description :
             * Détermine si un type T peut être construit par défaut. Simplifié, suppose que les types arithmétiques, pointeurs et tableaux sont constructibles.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est constructible par défaut, false sinon.
             *
             * @Dépendances : NkIsArithmetic, NkIsPointer, NkIsArray
             */
            template<typename T>
            struct NkIsDefaultConstructible : NkBoolConstant<
                NkIsArithmetic_v<T> || NkIsPointer_v<T> || NkIsArray_v<T>
            > {};

            template<typename T>
            inline constexpr nk_bool NkIsDefaultConstructible_v = NkIsDefaultConstructible<T>::value;

            /**
             * - NkIsCopyConstructible : Vérifie si un type est constructible par copie.
             *
             * @Description :
             * Détermine si un type T peut être construit par copie. Simplifié, suppose que les types arithmétiques et pointeurs sont copiables.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est constructible par copie, false sinon.
             *
             * @Dépendances : NkIsArithmetic, NkIsPointer
             */
            template<typename T>
            struct NkIsCopyConstructible : NkBoolConstant<
                NkIsArithmetic_v<T> || NkIsPointer_v<T>
            > {};

            template<typename T>
            inline constexpr nk_bool NkIsCopyConstructible_v = NkIsCopyConstructible<T>::value;

            /**
             * - NkIsMoveConstructible : Vérifie si un type est constructible par déplacement.
             *
             * @Description :
             * Détermine si un type T peut être construit par déplacement. Simplifié, basé sur NkIsCopyConstructible.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est constructible par déplacement, false sinon.
             *
             * @Dépendances : NkIsCopyConstructible
             */
            template<typename T>
            struct NkIsMoveConstructible : NkIsCopyConstructible<T> {};

            template<typename T>
            inline constexpr nk_bool NkIsMoveConstructible_v = NkIsMoveConstructible<T>::value;

            /**
             * - NkIsCopyAssignable : Vérifie si un type est assignable par copie.
             *
             * @Description :
             * Détermine si un type T peut être assigné par copie. Simplifié, suppose que les types arithmétiques et pointeurs sont assignables.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est assignable par copie, false sinon.
             *
             * @Dépendances : NkIsArithmetic, NkIsPointer
             */
            template<typename T>
            struct NkIsCopyAssignable : NkBoolConstant<
                NkIsArithmetic_v<T> || NkIsPointer_v<T>
            > {};

            template<typename T>
            inline constexpr nk_bool NkIsCopyAssignable_v = NkIsCopyAssignable<T>::value;

            /**
             * - NkIsMoveAssignable : Vérifie si un type est assignable par déplacement.
             *
             * @Description :
             * Détermine si un type T peut être assigné par déplacement. Simplifié, basé sur NkIsCopyAssignable.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est assignable par déplacement, false sinon.
             *
             * @Dépendances : NkIsCopyAssignable
             */
            template<typename T>
            struct NkIsMoveAssignable : NkIsCopyAssignable<T> {};

            template<typename T>
            inline constexpr nk_bool NkIsMoveAssignable_v = NkIsMoveAssignable<T>::value;

            /**
             * - NkIsDestructible : Vérifie si un type est destructible.
             *
             * @Description :
             * Détermine si un type T peut être détruit. Simplifié, suppose que les types arithmétiques, pointeurs et tableaux sont destructibles.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est destructible, false sinon.
             *
             * @Dépendances : NkIsArithmetic, NkIsPointer, NkIsArray
             */
            template<typename T>
            struct NkIsDestructible : NkBoolConstant<
                NkIsArithmetic_v<T> || NkIsPointer_v<T> || NkIsArray_v<T>
            > {};

            template<typename T>
            inline constexpr nk_bool NkIsDestructible_v = NkIsDestructible<T>::value;

            /**
             * - NkIsNothrowConstructible : Vérifie si un type est constructible sans exception.
             *
             * @Description :
             * Détermine si un type T peut être construit sans lever d’exceptions. Simplifié, basé sur les types arithmétiques et pointeurs.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             * - (typename... Args) : Arguments du constructeur.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est constructible sans exception, false sinon.
             *
             * @Dépendances : NkIsArithmetic, NkIsPointer
             */
            template<typename T, typename... Args>
            struct NkIsNothrowConstructible : NkBoolConstant<
                NkIsArithmetic_v<T> || NkIsPointer_v<T>
            > {};

            template<typename T, typename... Args>
            inline constexpr nk_bool NkIsNothrowConstructible_v = NkIsNothrowConstructible<T, Args...>::value;

            /**
             * - NkIsNothrowCopyConstructible : Vérifie si un type est constructible par copie sans exception.
             *
             * @Description :
             * Détermine si un type T peut être construit par copie sans lever d’exceptions. Simplifié, basé sur NkIsCopyConstructible.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est constructible par copie sans exception, false sinon.
             *
             * @Dépendances : NkIsCopyConstructible
             */
            template<typename T>
            struct NkIsNothrowCopyConstructible : NkIsCopyConstructible<T> {};

            template<typename T>
            inline constexpr nk_bool NkIsNothrowCopyConstructible_v = NkIsNothrowCopyConstructible<T>::value;

            /**
             * - NkIsNothrowMoveConstructible : Vérifie si un type est constructible par déplacement sans exception.
             *
             * @Description :
             * Détermine si un type T peut être construit par déplacement sans lever d’exceptions. Simplifié, basé sur NkIsMoveConstructible.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est constructible par déplacement sans exception, false sinon.
             *
             * @Dépendances : NkIsMoveConstructible
             */
            template<typename T>
            struct NkIsNothrowMoveConstructible : NkIsMoveConstructible<T> {};

            template<typename T>
            inline constexpr nk_bool NkIsNothrowMoveConstructible_v = NkIsNothrowMoveConstructible<T>::value;

            /**
             * - NkIsNothrowAssignable : Vérifie si un type est assignable sans exception.
             *
             * @Description :
             * Détermine si un type T peut être assigné sans lever d’exceptions. Simplifié, basé sur NkIsCopyAssignable.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est assignable sans exception, false sinon.
             *
             * @Dépendances : NkIsCopyAssignable
             */
            template<typename T>
            struct NkIsNothrowAssignable : NkIsCopyAssignable<T> {};

            template<typename T>
            inline constexpr nk_bool NkIsNothrowAssignable_v = NkIsNothrowAssignable<T>::value;

            /**
             * - NkIsNothrowCopyAssignable : Vérifie si un type est assignable par copie sans exception.
             *
             * @Description :
             * Détermine si un type T peut être assigné par copie sans lever d’exceptions. Simplifié, basé sur NkIsCopyAssignable.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est assignable par copie sans exception, false sinon.
             *
             * @Dépendances : NkIsCopyAssignable
             */
            template<typename T>
            struct NkIsNothrowCopyAssignable : NkIsCopyAssignable<T> {};

            template<typename T>
            inline constexpr nk_bool NkIsNothrowCopyAssignable_v = NkIsNothrowCopyAssignable<T>::value;

            /**
             * - NkIsNothrowMoveAssignable : Vérifie si un type est assignable par déplacement sans exception.
             *
             * @Description :
             * Détermine si un type T peut être assigné par déplacement sans lever d’exceptions. Simplifié, basé sur NkIsMoveAssignable.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est assignable par déplacement sans exception, false sinon.
             *
             * @Dépendances : NkIsMoveAssignable
             */
            template<typename T>
            struct NkIsNothrowMoveAssignable : NkIsMoveAssignable<T> {};

            template<typename T>
            inline constexpr nk_bool NkIsNothrowMoveAssignable_v = NkIsNothrowMoveAssignable<T>::value;

            /**
             * - NkIsTriviallyDefaultConstructible : Vérifie si un type est trivialement constructible par défaut.
             *
             * @Description :
             * Détermine si un type T peut être construit par défaut de manière triviale. Simplifié, basé sur les types arithmétiques.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est trivialement constructible par défaut, false sinon.
             *
             * @Dépendances : NkIsArithmetic
             */
            template<typename T>
            struct NkIsTriviallyDefaultConstructible : NkBoolConstant<NkIsArithmetic_v<T>> {};

            template<typename T>
            inline constexpr nk_bool NkIsTriviallyDefaultConstructible_v = NkIsTriviallyDefaultConstructible<T>::value;

            /**
             * - NkIsTriviallyConstructible : Vérifie si un type est trivialement constructible.
             *
             * @Description :
             * Détermine si un type T peut être construit de manière triviale avec les arguments donnés.
             * Simplifié, basé sur les types arithmétiques.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             * - (typename... Args) : Arguments du constructeur.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est trivialement constructible, false sinon.
             *
             * @Dépendances : NkIsArithmetic
             */
            template<typename T, typename... Args>
            struct NkIsTriviallyConstructible : NkBoolConstant<NkIsArithmetic_v<T>> {};

            template<typename T, typename... Args>
            inline constexpr nk_bool NkIsTriviallyConstructible_v = NkIsTriviallyConstructible<T, Args...>::value;

            /**
             * - NkIsTriviallyCopyConstructible : Vérifie si un type est trivialement constructible par copie.
             *
             * @Description :
             * Détermine si un type T peut être construit par copie de manière triviale. Simplifié, basé sur NkIsCopyConstructible.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est trivialement constructible par copie, false sinon.
             *
             * @Dépendances : NkIsCopyConstructible
             */
            template<typename T>
            struct NkIsTriviallyCopyConstructible : NkIsCopyConstructible<T> {};

            template<typename T>
            inline constexpr nk_bool NkIsTriviallyCopyConstructible_v = NkIsTriviallyCopyConstructible<T>::value;

            /**
             * - NkIsTriviallyMoveConstructible : Vérifie si un type est trivialement constructible par déplacement.
             *
             * @Description :
             * Détermine si un type T peut être construit par déplacement de manière triviale. Simplifié, basé sur NkIsMoveConstructible.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est trivialement constructible par déplacement, false sinon.
             *
             * @Dépendances : NkIsMoveConstructible
             */
            template<typename T>
            struct NkIsTriviallyMoveConstructible : NkIsMoveConstructible<T> {};

            template<typename T>
            inline constexpr nk_bool NkIsTriviallyMoveConstructible_v = NkIsTriviallyMoveConstructible<T>::value;

            /**
             * - NkIsTriviallyCopyable : Vérifie si un type est trivialement copiable.
             *
             * @Description :
             * Détermine si un type T peut être copié de manière triviale (memcpy). Simplifié, basé sur les types arithmétiques et pointeurs.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est trivialement copiable, false sinon.
             *
             * @Dépendances : NkIsArithmetic, NkIsPointer
             */
            template<typename T>
            struct NkIsTriviallyCopyable : NkBoolConstant<
                NkIsArithmetic_v<T> || NkIsPointer_v<T>
            > {};

            template<typename T>
            inline constexpr nk_bool NkIsTriviallyCopyable_v = NkIsTriviallyCopyable<T>::value;

            /**
             * - NkIsTriviallyDestructible : Vérifie si un type est trivialement destructible.
             *
             * @Description :
             * Détermine si un type T peut être détruit de manière triviale. Simplifié, basé sur NkIsDestructible.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est trivialement destructible, false sinon.
             *
             * @Dépendances : NkIsDestructible
             */
            template<typename T>
            struct NkIsTriviallyDestructible : NkIsDestructible<T> {};

            template<typename T>
            inline constexpr nk_bool NkIsTriviallyDestructible_v = NkIsTriviallyDestructible<T>::value;

            /**
             * - NkIsTriviallyRelocatable : Vérifie si un type est trivialement relocalisable.
             *
             * @Description :
             * Détermine si un type T peut être déplacé en mémoire de manière triviale (memcpy + destruction triviale).
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est trivialement relocalisable, false sinon.
             *
             * @Dépendances : NkIsTriviallyCopyable, NkIsTriviallyDestructible
             */
            template<typename T>
            struct NkIsTriviallyRelocatable : NkBoolConstant<
                NkIsTriviallyCopyable_v<T> && NkIsTriviallyDestructible_v<T>
            > {};

            template<typename T>
            inline constexpr nk_bool NkIsTriviallyRelocatable_v = NkIsTriviallyRelocatable<T>::value;

            /**
             * - NkIsTriviallyCopyAssignable : Vérifie si un type est trivialement assignable par copie.
             *
             * @Description :
             * Détermine si un type T peut être assigné par copie de manière triviale. Simplifié, basé sur NkIsCopyAssignable.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est trivialement assignable par copie, false sinon.
             *
             * @Dépendances : NkIsCopyAssignable
             */
            template<typename T>
            struct NkIsTriviallyCopyAssignable : NkIsCopyAssignable<T> {};

            template<typename T>
            inline constexpr nk_bool NkIsTriviallyCopyAssignable_v = NkIsTriviallyCopyAssignable<T>::value;

            /**
             * - NkIsTriviallyMoveAssignable : Vérifie si un type est trivialement assignable par déplacement.
             *
             * @Description :
             * Détermine si un type T peut être assigné par déplacement de manière triviale. Simplifié, basé sur NkIsMoveAssignable.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est trivialement assignable par déplacement, false sinon.
             *
             * @Dépendances : NkIsMoveAssignable
             */
            template<typename T>
            struct NkIsTriviallyMoveAssignable : NkIsMoveAssignable<T> {};

            template<typename T>
            inline constexpr nk_bool NkIsTriviallyMoveAssignable_v = NkIsTriviallyMoveAssignable<T>::value;

            /**
             * - NkIsClass : Vérifie si un type est une classe.
             *
             * @Description :
             * Détermine si un type T est une classe (non-union, non-énumération, non-fondamental).
             * Utilise l’intrinsèque __is_class.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est une classe, false sinon.
             *
             * @Dépendances : NkBoolConstant
             */
            template<typename T>
            struct NkIsClass : NkBoolConstant<__is_class(T)> {};

            template<typename T>
            inline constexpr nk_bool NkIsClass_v = NkIsClass<T>::value;

            /**
             * - NkIsUnion : Vérifie si un type est une union.
             *
             * @Description :
             * Détermine si un type T est une union. Utilise l’intrinsèque __is_union.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est une union, false sinon.
             *
             * @Dépendances : NkBoolConstant
             */
            template<typename T>
            struct NkIsUnion : NkBoolConstant<__is_union(T)> {};

            template<typename T>
            inline constexpr nk_bool NkIsUnion_v = NkIsUnion<T>::value;

            /**
             * - NkIsEnum : Vérifie si un type est une énumération.
             *
             * @Description :
             * Détermine si un type T est une énumération. Utilise l’intrinsèque __is_enum.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est une énumération, false sinon.
             *
             * @Dépendances : NkBoolConstant
             */
            template<typename T>
            struct NkIsEnum : NkBoolConstant<__is_enum(T)> {};

            template<typename T>
            inline constexpr nk_bool NkIsEnum_v = NkIsEnum<T>::value;

            /**
             * - NkUnderlyingType : Obtient le type sous-jacent d’une énumération.
             *
             * @Description :
             * Fournit le type sous-jacent d’une énumération T. Utilise std::underlying_type_t (intrinsèque).
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (type) type : Type sous-jacent de T si c’est une énumération, T sinon.
             *
             * @Dépendances : NkIsEnum, NkConditional
             */
            template<typename T>
            struct NkUnderlyingType {
                using type = NkConditional_t<NkIsEnum_v<T>, std::underlying_type_t<T>, T>;
            };

            template<typename T>
            using NkUnderlyingType_t = typename NkUnderlyingType<T>::type;

            /**
             * - NkIsAbstract : Vérifie si un type est abstrait.
             *
             * @Description :
             * Détermine si un type T est une classe abstraite. Utilise l’intrinsèque __is_abstract.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est abstrait, false sinon.
             *
             * @Dépendances : NkBoolConstant
             */
            template<typename T>
            struct NkIsAbstract : NkBoolConstant<__is_abstract(T)> {};

            template<typename T>
            inline constexpr nk_bool NkIsAbstract_v = NkIsAbstract<T>::value;

            /**
             * - NkIsPolymorphic : Vérifie si un type est polymorphe.
             *
             * @Description :
             * Détermine si un type T est polymorphe (contient des fonctions virtuelles). Utilise l’intrinsèque __is_polymorphic.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est polymorphe, false sinon.
             *
             * @Dépendances : NkBoolConstant
             */
            template<typename T>
            struct NkIsPolymorphic : NkBoolConstant<__is_polymorphic(T)> {};

            template<typename T>
            inline constexpr nk_bool NkIsPolymorphic_v = NkIsPolymorphic<T>::value;

            /**
             * - NkIsFinal : Vérifie si un type est marqué comme final.
             *
             * @Description :
             * Détermine si un type T est marqué comme final. Utilise l’intrinsèque __is_final.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est final, false sinon.
             *
             * @Dépendances : NkBoolConstant
             */
            template<typename T>
            struct NkIsFinal : NkBoolConstant<__is_final(T)> {};

            template<typename T>
            inline constexpr nk_bool NkIsFinal_v = NkIsFinal<T>::value;

            /**
             * - NkRank : Obtient le rang d’un type tableau.
             *
             * @Description :
             * Calcule le nombre de dimensions d’un type tableau T. Remplace std::rank sans dépendance STL.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr usize) value : Nombre de dimensions du tableau.
             *
             * @Dépendances : NkIntegralConstant, NkRemoveExtent
             */
            template<typename T>
            struct NkRank : NkIntegralConstant<nk_usize, 0> {};

            template<typename T, nk_usize N>
            struct NkRank<T[N]> : NkIntegralConstant<nk_usize, NkRank<T>::value + 1> {};

            template<typename T>
            struct NkRank<T[]> : NkIntegralConstant<nk_usize, NkRank<T>::value + 1> {};

            template<typename T>
            inline constexpr nk_usize NkRank_v = NkRank<T>::value;

            /**
             * - NkExtent : Fournit la taille de la dimension N d’un type tableau.
             *
             * @Description :
             * Détermine la taille de la dimension N d’un type tableau T. Si T n’est pas un tableau ou si N dépasse le nombre de dimensions, retourne 0.
             *
             * @Template :
             * - (typename T) : Type à analyser.
             * - (usize N) : Dimension du tableau (0 pour la première dimension, 1 pour la suivante, etc.).
             *
             * @Members :
             * - (static constexpr usize) value : Taille de la dimension N, ou 0 si non applicable.
             *
             * @Dépendances : NkIntegralConstant
             */
            template<typename T, nk_usize N = 0>
            struct NkExtent : NkIntegralConstant<nk_usize, 0> {};

            template<typename T, nk_usize N>
            struct NkExtent<T[], N> : NkExtent<T, N - 1> {};

            template<typename T, nk_usize N>
            struct NkExtent<T[N], 0> : NkIntegralConstant<nk_usize, N> {};

            template<typename T, nk_usize N, nk_usize M>
            struct NkExtent<T[M], N> : NkExtent<T, N - 1> {};

            template<typename T, nk_usize N = 0>
            inline constexpr nk_usize NkExtent_v = NkExtent<T, N>::value;

            /**
             * - NkIsScalar : Vérifie si un type est scalaire.
             *
             * @Description :
             * Détermine si un type T est scalaire (arithmétique, énumération, pointeur, pointeur de membre).
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est scalaire, false sinon.
             *
             * @Dépendances : NkIsArithmetic, NkIsEnum, NkIsPointer, NkIsMemberPointer
             */
            template<typename T>
            struct NkIsScalar : NkBoolConstant<
                NkIsArithmetic_v<T> || NkIsEnum_v<T> || NkIsPointer_v<T> || NkIsMemberPointer_v<T> || NkIsNullPointer_v<T>
            > {};

            template<typename T>
            inline constexpr nk_bool NkIsScalar_v = NkIsScalar<T>::value;

            /**
             * - NkIsConstructible : Vérifie si un type peut être construit avec les arguments donnés.
             *
             * @Description :
             * Détermine si un type T peut être construit avec un ensemble d’arguments Args...
             * Simplifié pour les types arithmétiques, pointeurs, et types scalaires.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             * - (typename... Args) : Types des arguments pour la construction.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est constructible avec Args..., false sinon.
             *
             * @Dépendances : NkIsScalar
             */
            template<typename T, typename... Args>
            struct NkIsConstructible : NkBoolConstant<__is_constructible(T, Args...)> {};

            template<typename T, typename... Args>
            inline constexpr nk_bool NkIsConstructible_v = NkIsConstructible<T, Args...>::value;

            /**
             * - NkIsBaseOf : Vérifie si un type est une classe de base d’un autre.
             *
             * @Description :
             * Détermine si Base est une classe de base de Derived. Utilise l’intrinsèque __is_base_of.
             *
             * @Template :
             * - (typename Base) : Type de base potentiel.
             * - (typename Derived) : Type dérivé potentiel.
             *
             * @Members :
             * - (static constexpr bool) value : True si Base est une base de Derived, false sinon.
             *
             * @Dépendances : NkBoolConstant
             */
            template<typename Base, typename Derived>
            struct NkIsBaseOf : NkBoolConstant<__is_base_of(Base, Derived)> {};

            template<typename Base, typename Derived>
            inline constexpr nk_bool NkIsBaseOf_v = NkIsBaseOf<Base, Derived>::value;

            /**
             * - NkIsConvertible : Vérifie si un type peut être converti en un autre.
             *
             * @Description :
             * Détermine si un type From peut être converti en un type To. Utilise l’intrinsèque __is_convertible.
             *
             * @Template :
             * - (typename From) : Type source.
             * - (typename To) : Type cible.
             *
             * @Members :
             * - (static constexpr bool) value : True si From est convertible en To, false sinon.
             *
             * @Dépendances : NkBoolConstant
             */
            template<typename From, typename To>
            struct NkIsConvertible : NkBoolConstant<__is_convertible(From, To)> {};

            template<typename From, typename To>
            inline constexpr nk_bool NkIsConvertible_v = NkIsConvertible<From, To>::value;

            /**
             * - NkIsCompleteType : Vérifie si un type est complet.
             *
             * @Description :
             * Détermine si un type T est complet (peut être instancié avec sizeof).
             * Utilisé pour éviter les erreurs avec des types incomplets.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est complet, false sinon.
             *
             * @Dépendances : NkMakeVoid, NkFalseType, NkTrueType
             */
            template<typename T, typename = void>
            struct NkIsCompleteTypeHelper : NkFalseType {};

            template<typename T>
            struct NkIsCompleteTypeHelper<T, NkVoid_t<NkDeclType(sizeof(T))>> : NkTrueType {};

            template<typename T>
            struct NkIsCompleteType : NkBoolConstant<NkIsCompleteTypeHelper<T>::value> {};

            template<typename T>
            inline constexpr nk_bool NkIsCompleteType_v = NkIsCompleteType<T>::value;

            /**
             * - NkCommonType : Détermine le type commun entre plusieurs types.
             *
             * @Description :
             * Détermine le type commun entre plusieurs types pour des conversions implicites.
             * Simplifié pour gérer les types arithmétiques.
             *
             * @Template :
             * - (typename... Ts) : Pack variadique de types.
             *
             * @Members :
             * - (type) type : Type commun ou void si aucun type commun.
             *
             * @Dépendances : NkDecay, NkIsSame, NkIsArithmetic, NkConditional
             */
            template<typename... Ts>
            struct NkCommonType {};

            template<typename T>
            struct NkCommonType<T> { using type = NkDecayT<T>; };

            template<typename T1, typename T2>
            struct NkCommonType<T1, T2> {
                using type = NkConditional_t<
                    NkIsSame_v<NkDecayT<T1>, NkDecayT<T2>>,
                    NkDecayT<T1>,
                    NkConditional_t<
                        NkIsArithmetic_v<T1> && NkIsArithmetic_v<T2>,
                        NkConditional_t<
                            sizeof(NkDecayT<T1>) >= sizeof(NkDecayT<T2>),
                            NkDecayT<T1>,
                            NkDecayT<T2>
                        >,
                        void
                    >
                >;
            };

            template<typename T1, typename T2, typename... Ts>
            struct NkCommonType<T1, T2, Ts...> {
                using type = typename NkCommonType<typename NkCommonType<T1, T2>::type, Ts...>::type;
            };

            template<typename... Ts>
            using NkCommonType_t = typename NkCommonType<Ts...>::type;

            /**
             * - NkAlignedStorage : Fournit un stockage aligné pour un type.
             *
             * @Description :
             * Fournit un stockage aligné pour un type avec une taille et un alignement donnés.
             * Utilisé dans des structures comme NkAlignedUnion.
             *
             * @Template :
             * - (usize Len) : Taille du stockage.
             * - (usize Align) : Alignement du stockage (par défaut alignof(double)).
             *
             * @Members :
             * - (type) type : Type de stockage aligné (tableau de unsigned char).
             *
             * @Dépendances : Aucune
             */
            template<nk_usize Len, nk_usize Align = alignof(double)>
            struct NkAlignedStorage {
                struct type {
                    alignas(Align) unsigned char data[Len];
                };
            };

            template<nk_usize Len, nk_usize Align>
            using NkAlignedStorage_t = typename NkAlignedStorage<Len, Align>::type;

            /**
             * - MaxSize : Calcule la taille maximale parmi plusieurs types.
             *
             * @Description :
             * Calcule la taille maximale (sizeof) parmi un pack variadique de types.
             * Utilisé dans NkAlignedUnion.
             *
             * @Template :
             * - (typename... Ts) : Pack variadique de types.
             *
             * @Members :
             * - (static constexpr usize) value : Taille maximale des types.
             *
             * @Dépendances : Aucune
             */
            template<typename... Ts>
            struct NkMaxSize;

            template<>
            struct NkMaxSize<> {
                static constexpr nk_usize value = 0;
            };

            template<typename T, typename... Ts>
            struct NkMaxSize<T, Ts...> {
                static constexpr nk_usize value = sizeof(T) > NkMaxSize<Ts...>::value ? sizeof(T) : NkMaxSize<Ts...>::value;
            };

            /**
             * - MaxAlign : Calcule l’alignement maximal parmi plusieurs types.
             *
             * @Description :
             * Calcule l’alignement maximal (alignof) parmi un pack variadique de types.
             * Utilisé dans NkAlignedUnion pour garantir un alignement correct.
             *
             * @Template :
             * - (typename... Ts) : Pack variadique de types.
             *
             * @Members :
             * - (static constexpr usize) value : Alignement maximal des types.
             *
             * @Dépendances : Aucune
             */
            template<typename... Ts>
            struct NkMaxAlign;

            template<>
            struct NkMaxAlign<> {
                static constexpr nk_usize value = 1;
            };

            template<typename T, typename... Ts>
            struct NkMaxAlign<T, Ts...> {
                static constexpr nk_usize value = alignof(T) > NkMaxAlign<Ts...>::value ? alignof(T) : NkMaxAlign<Ts...>::value;
            };

            /**
             * - NkAlignedUnion : Fournit un stockage aligné pour une union de types.
             *
             * @Description :
             * Fournit un type de stockage aligné capable de contenir n’importe lequel des types donnés,
             * avec la taille et l’alignement nécessaires pour une union.
             *
             * @Template :
             * - (usize Len) : Taille minimale du stockage.
             * - (typename... Types) : Pack variadique de types.
             *
             * @Members :
             * - (type) type : Type de stockage aligné (tableau de unsigned char).
             *
             * @Dépendances : NkAlignedStorage, MaxSize, MaxAlign
             */
            template<nk_usize Len, typename... Types>
            struct NkAlignedUnion {
                static constexpr nk_usize size_value = NkMaxSize<Types...>::value > Len ? NkMaxSize<Types...>::value : Len;
                static constexpr nk_usize align_value = NkMaxAlign<Types...>::value;
                using type = typename NkAlignedStorage<size_value, align_value>::type;
            };

            template<nk_usize Len, typename... Types>
            using NkAlignedUnion_t = typename NkAlignedUnion<Len, Types...>::type;

            /**
             * - NkIsStandardLayout : Vérifie si un type a une disposition standard.
             *
             * @Description :
             * Détermine si un type T a une disposition standard (compatible avec C).
             * Simplifié, suppose que les types arithmétiques, pointeurs et tableaux ont une disposition standard.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T a une disposition standard, false sinon.
             *
             * @Dépendances : NkIsArithmetic, NkIsPointer, NkIsArray
             */
            template<typename T>
            struct NkIsStandardLayout : NkBoolConstant<
                NkIsArithmetic_v<T> || NkIsPointer_v<T> || NkIsArray_v<T>
            > {};

            template<typename T>
            inline constexpr nk_bool NkIsStandardLayout_v = NkIsStandardLayout<T>::value;

            /**
             * - NkIsLiteralType : Vérifie si un type est un type littéral.
             *
             * @Description :
             * Cette structure template utilise `__is_literal_type` pour vérifier si T est un type littéral utilisable en contexte `constexpr`.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             */
            template<typename T>
            struct NkIsLiteralType : NkBoolConstant<__is_literal_type(T)> {};

            template<typename T>
            inline constexpr nk_bool NkIsLiteralType_v = NkIsLiteralType<T>::value;

            /**
             * - NkIsScopedEnum : Vérifie si un type est une énumération avec portée.
             *
             * @Description :
             * Cette structure template vérifie si T est une énumération avec portée (`enum class` ou `enum struct`).
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             */
            template<typename T>
            struct NkIsScopedEnum : NkBoolConstant<NkIsEnum_v<T> && !NkIsConvertible_v<T, NkUnderlyingType_t<T>>> {};

            template<typename T>
            inline constexpr nk_bool NkIsScopedEnum_v = NkIsScopedEnum<T>::value;

            /**
             * - NkIsTrivial : Vérifie si un type est trivial.
             *
             * @Description :
             * Détermine si un type T est trivial (triviellement copiable et destructible).
             * Simplifié, basé sur NkIsTriviallyCopyable et NkIsTriviallyDestructible.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est trivial, false sinon.
             *
             * @Dépendances : NkIsTriviallyCopyable, NkIsTriviallyDestructible
             */
            template<typename T>
            struct NkIsTrivial : NkBoolConstant<
                NkIsTriviallyCopyable_v<T> && NkIsTriviallyDestructible_v<T>
            > {};

            template<typename T>
            inline constexpr nk_bool NkIsTrivial_v = NkIsTrivial<T>::value;

            /**
             * - NkIsEmpty : Vérifie si un type est une classe vide.
             *
             * @Description :
             * Détermine si un type T est une classe vide (sans données membres non statiques).
             * Utilise l’intrinsèque __is_empty.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est une classe vide, false sinon.
             *
             * @Dépendances : NkBoolConstant
             */
            template<typename T>
            struct NkIsEmpty : NkBoolConstant<__is_empty(T)> {};

            template<typename T>
            inline constexpr nk_bool NkIsEmpty_v = NkIsEmpty<T>::value;

            
            /**
             * - NkIsAllSame : Vérifie si tous les types d’un pack variadique sont identiques.
             *
             * @Description :
             * Cette structure template vérifie si tous les types dans un pack variadique sont identiques.
             *
             * @Template :
             * - (typename... Ts) : Types à comparer.
             */
            template<typename... Ts>
            struct NkIsAllSame : NkTrueType {};

            template<typename T, typename... Rest>
            struct NkIsAllSame<T, Rest...> : NkConjunction<NkIsSame<T, Rest>...> {};

            template<typename... Ts>
            inline constexpr nk_bool NkIsAllSame_v = NkIsAllSame<Ts...>::value;

            /**
             * - NkIsUnique : Vérifie si un type est unique dans un pack variadique.
             *
             * @Description :
             * Détermine si un type T apparaît une seule fois dans un pack variadique Types...
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             * - (typename... Types) : Pack variadique de types.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est unique dans Types..., false sinon.
             *
             * @Dépendances : NkIsSame, NkIsAnyOf
             */
            template<typename T, typename... Types>
            struct NkIsUnique;

            template<typename T>
            struct NkIsUnique<T> : NkTrueType {};

            template<typename T, typename First, typename... Rest>
            struct NkIsUnique<T, First, Rest...> : NkBoolConstant<
                !NkIsSame_v<T, First> && NkIsUnique<T, Rest...>::value
            > {};

            template<typename T, typename... Rest>
            struct NkIsUnique<T, T, Rest...> : NkBoolConstant<!NkIsAnyOf_v<T, Rest...>> {};

            template<typename T, typename... Types>
            inline constexpr nk_bool NkIsUnique_v = NkIsUnique<T, Types...>::value;
            
            /**
             * - NkIsInvocable : @Vérifie si un type est invocable avec des arguments donnés.
             *
             * @Description :
             * Cette structure template utilise SFINAE pour vérifier si F peut être invoqué avec les arguments Args.
             * Elle teste si l'expression F(Args...) est valide dans un contexte non évalué.
             *
             * @Template :
             * - (typename F) : Type invocable (fonction, lambda, functor, etc.).
             * - (typename... Args) : Types des arguments pour l'invocation.
             *
             * @Members :
             * - (type) type : Résultat du test (NkTrueType ou NkFalseType).
             * - (static constexpr bool) value : Indique si F est invocable avec Args.
             */
            template<typename F, typename... Args>
            struct NkIsInvocable {
            private:
                /**
                 * - test : @Teste si F est invocable avec Args.
                 *
                 * @Description :
                 * Utilise SFINAE pour vérifier si l'invocation F(Args...) est valide.
                 * Retourne NkTrueType si l'expression est bien formée.
                 *
                 * @Template :
                 * - (typename U) : Type invocable.
                 * - (typename = NkDeclType(...)) : SFINAE pour vérifier l'invocation.
                 * @param (int) : Paramètre pour résolution SFINAE.
                 * @return (NkTrueType) : Si l'invocation est valide.
                 */
                template<typename U, typename = NkDeclType(NkDeclVal<U>()(NkDeclVal<Args>()...))>
                static NkTrueType test(nk_int32);

                /**
                 * - test : @Spécialisation pour l'échec de l'invocation.
                 *
                 * @Description :
                 * Retourne NkFalseType si l'invocation F(Args...) n'est pas valide.
                 *
                 * @param (...) : Paramètre pour résolution SFINAE.
                 * @return (NkFalseType) : Si l'invocation échoue.
                 */
                static NkFalseType test(...);

            public:
                using type = NkDeclType(test<F>(0));
                static constexpr nk_bool value = type::value;
            };

            /**
             * @Description : Constante booléenne indiquant si un type est invocable avec des arguments donnés.
             */
            template<typename F, typename... Args>
            inline constexpr nk_bool NkIsInvocable_v = NkIsInvocable<F, Args...>::value;

            /**
             * - NkIsInvocableR : Vérifie si un type est invocable avec un type de retour spécifique.
             *
             * @Description :
             * Cette structure template vérifie si F peut être invoqué avec Args et si le résultat est convertible en R.
             *
             * @Template :
             * - (typename R) : Type de retour attendu.
             * - (typename F) : Type invocable.
             * - (typename... Args) : Types des arguments pour l'invocation.
             */
            template<typename R, typename F, typename... Args>
            struct NkIsInvocableR : NkBoolConstant<
                NkIsInvocable_v<F, Args...> && NkIsConvertible_v<NkInvokeResult_t<F, Args...>, R>
            > {};

            template<typename R, typename F, typename... Args>
            inline constexpr nk_bool NkIsInvocableR_v = NkIsInvocableR<R, F, Args...>::value;

            /**
             * - NkIsNothrowInvocableR : Vérifie si un type est invocable sans exception avec un type de retour spécifique.
             *
             * @Description :
             * Cette structure template vérifie si F peut être invoqué avec Args sans lever d'exceptions et si le résultat est convertible en R.
             *
             * @Template :
             * - (typename R) : Type de retour attendu.
             * - (typename F) : Type invocable.
             * - (typename... Args) : Types des arguments pour l'invocation.
             */
            template<typename R, typename F, typename... Args>
            struct NkIsNothrowInvocableR : NkBoolConstant<
                NkIsNothrowInvocable_v<F, Args...> && NkIsConvertible_v<NkInvokeResult_t<F, Args...>, R>
            > {};

            template<typename R, typename F, typename... Args>
            inline constexpr nk_bool NkIsNothrowInvocableR_v = NkIsNothrowInvocableR<R, F, Args...>::value;

            /**
             * - NkNounType : @Détermine le type non qualifié d'un type.
             *
             * @Description :
             * Cette structure template applique les règles de dégradation (suppression des références et qualifiers CV, conversion des tableaux en pointeurs).
             *
             * @Template :
             * - (typename T) : Type à dégrader.
             */
            template<typename T>
            struct NkNounType {
                using type = typename NkRemoveCV<typename NkRemoveReference<T>::type>::type;
            };

            /**
             * @Alias NkNounType_t
             * @Description Alias pour accéder au type dégradé.
             * @UnderlyingType typename NkNounType<T>::type
             */
            template<typename T>
            using NkNounType_t = typename NkNounType<T>::type;

            /**
             * - NkIsSwappable : Vérifie si un type est échangeable (swappable).
             *
             * @Description :
             * Cette structure template vérifie si deux objets de type T peuvent être échangés via une opération comme `std::swap`.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             */
            template<typename T>
            struct NkIsSwappable {
                private:
                    template<typename U, typename = NkDeclType(swap(NkDeclVal<U&>(), NkDeclVal<U&>()))>
                    static NkTrueType test(nk_int32);
                    static NkFalseType test(...);

                public:
                    static constexpr nk_bool value = NkDeclType(test<T>(0))::value;
            };

            template<typename T>
            inline constexpr nk_bool NkIsSwappable_v = NkIsSwappable<T>::value;

            /**
             * - NkIsNothrowSwappable : Vérifie si un type est swappable sans exception.
             *
             * @Description :
             * Détermine si un type T peut être échangé (swapped) sans lever d’exceptions.
             * Simplifié, basé sur les types arithmétiques et pointeurs.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est swappable sans exception, false sinon.
             *
             * @Dépendances : NkIsArithmetic, NkIsPointer
             */
            template<typename T>
            struct NkIsNothrowSwappable : NkBoolConstant<
                NkIsArithmetic_v<T> || NkIsPointer_v<T>
            > {};

            template<typename T>
            inline constexpr nk_bool NkIsNothrowSwappable_v = NkIsNothrowSwappable<T>::value;

            /**
             * - NkIdentity : @Fournit une identité de type.
             *
             * @Description :
             * Cette structure template sert à encapsuler un type T pour éviter des problèmes de déduction dans certains contextes.
             *
             * @Template :
             * - (typename T) : Type à encapsuler.
             *
             * @Members :
             * - (type) type : Type T.
             */
            template<typename T>
            struct NkIdentity {
                using type = T;
            };

            /**
             * - NkForward : Effectue un transfert parfait (perfect forwarding).
             *
             * @Description :
             * Transfère un argument en préservant sa catégorie de valeur (lvalue/rvalue).
             * Remplace std::forward sans dépendance STL.
             *
             * @Template :
             * - (typename T) : Type de l’argument.
             * - (typename U) : Type de l’argument passé.
             *
             * @Parameters :
             * - (U&& arg) : Argument à transférer.
             *
             * @Return : T (lvalue ou rvalue selon arg).
             *
             * @Dépendances : NkRemoveReference, NkAddLValueReference, NkAddRValueReference
             */
            // template<typename T, typename U>
            // constexpr T&& NkForward(NkRemoveReference_t<U>& arg) noexcept {
            //     return static_cast<T&&>(arg);
            // }

            // template<typename T, typename U>
            // constexpr T&& NkForward(NkRemoveReference_t<U>&& arg) noexcept {
            //     static_assert(!NkIsLValueReference_v<U>, "Cannot forward an rvalue as an lvalue");
            //     return static_cast<T&&>(arg);
            // }

            /**
             * - NkForward : Transfère un argument en préservant sa catégorie de valeur (lvalue ou rvalue).
             *
             * @Description :
             * Similaire à std::forward, transfère un argument en tant que lvalue ou rvalue selon son type.
             *
             * @Template :
             * - (typename T) : Type de l'argument à transférer.
             *
             * @Parameters :
             * - (arg) : Argument à transférer.
             *
             * @Returns :
             * - (T&&) : Argument transféré avec la catégorie de valeur préservée.
             */
            template<typename T>
            constexpr T&& NkForward(NkRemoveReference_t<T>& arg) noexcept {
                return static_cast<T&&>(arg);
            }

            template<typename T>
            constexpr T&& NkForward(NkRemoveReference_t<T>&& arg) noexcept {
                return static_cast<T&&>(arg);
            }
            // std::forward<T>(arg);
            /**
             * - NkMove : Convertit un argument en rvalue.
             *
             * @Description :
             * Convertit un argument en rvalue pour forcer le déplacement. Remplace std::move sans dépendance STL.
             *
             * @Template :
             * - (typename T) : Type de l’argument.
             *
             * @Parameters :
             * - (T&& arg) : Argument à déplacer.
             *
             * @Return : NkRemoveReference_t<T>&& (rvalue).
             *
             * @Dépendances : NkRemoveReference
             */
            template<typename T>
            constexpr NkRemoveReference_t<T>&& NkMove(T&& arg) noexcept {
                return static_cast<NkRemoveReference_t<T>&&>(arg);
            }

            /**
             * - NkIsCharacterType : Vérifie si un type est un type de caractère.
             *
             * @Description :
             * Détermine si un type T est un type de caractère (char, nk_wchar, nk_char8, nk_char16, nk_char32).
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est un type de caractère, false sinon.
             *
             * @Dépendances : NkIsAnyOf
             */
            template<typename T>
            struct NkIsCharacterType : NkIsAnyOf<T, nk_char, nk_wchar, nk_char8, nk_char16, nk_char32> {};

            template<typename T>
            inline constexpr nk_bool NkIsCharacterType_v = NkIsCharacterType<T>::value;

            /**
             * - NkIsFundamental : Vérifie si un type est fondamental.
             *
             * @Description :
             * Détermine si un type T est un type fondamental (arithmétique ou void).
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est fondamental, false sinon.
             *
             * @Dépendances : NkIsArithmetic, NkIsVoid
             */
            template<typename T>
            struct NkIsFundamental : NkBoolConstant<NkIsArithmetic_v<T> || NkIsVoid_v<T>> {};

            template<typename T>
            inline constexpr nk_bool NkIsFundamental_v = NkIsFundamental<T>::value;

            /**
             * - NkIsObject : Vérifie si un type est un type objet.
             *
             * @Description :
             * Détermine si un type T est un type objet (scalaire, tableau, classe, union).
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est un type objet, false sinon.
             *
             * @Dépendances : NkIsScalar, NkIsArray, NkIsClass, NkIsUnion
             */
            template<typename T>
            struct NkIsObject : NkBoolConstant<
                NkIsScalar_v<T> || NkIsArray_v<T> || NkIsClass_v<T> || NkIsUnion_v<T>
            > {};

            template<typename T>
            inline constexpr nk_bool NkIsObject_v = NkIsObject<T>::value;

            /**
             * - NkIsCompound : Vérifie si un type est un type composé.
             *
             * @Description :
             * Détermine si un type T est un type composé (non fondamental, inclut tableaux, classes, unions, références, pointeurs, etc.).
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est composé, false sinon.
             *
             * @Dépendances : NkIsFundamental
             */
            template<typename T>
            struct NkIsCompound : NkBoolConstant<!NkIsFundamental_v<T>> {};

            template<typename T>
            inline constexpr nk_bool NkIsCompound_v = NkIsCompound<T>::value;

            /**
             * - NkIsValidCharType : Vérifie si un type est un type de caractère valide.
             *
             * @Description :
             * Détermine si un type T est un type de caractère valide (nkchar, char8, char16, char32, wchar, ou leurs variantes signées/non signées).
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est un type de caractère valide, false sinon.
             *
             * @Dépendances : NkIsSame, NkIsAnyOf
             */
            template<typename T>
            struct NkIsValidCharType : NkIsAnyOf<T, nk_char, nk_char8, nk_char16, nk_char32, nk_wchar, signed char, unsigned char> {};

            /**
             * - NkIsValidCharType : Vérifie si un type est un type de caractère valide.
             *
             * @Description :
             * Détermine si un type T est un type de caractère valide (nkchar, char8, char16, char32, wchar, ou leurs variantes signées/non signées).
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             *
             * @Members :
             * - (static constexpr bool) value : True si T est un type de caractère valide, false sinon.
             *
             * @Dépendances : NkIsSame, NkIsAnyOf
             */
            // template<typename T>
            // struct NkIsValidCharType : NkIsAnyOf<T, nkchar, nk_char8, nk_char16, nk_char32, nk_wchar, signed char, unsigned char, uint16_t, int32_t, uint32_t> {};
            
            template<typename T>
            inline constexpr bool NkIsValidCharType_v = NkIsValidCharType<T>::value;

            /**
             * - NkIsPlatformSupported : Vérifie si un type est supporté sur la plateforme actuelle.
             *
             * @Description :
             * Cette structure template vérifie si un type est supporté sur la plateforme actuelle,
             * basé sur les définitions de NkPlatformDetect.h.
             *
             * @Template :
             * - (typename T) : Type à vérifier.
             */
            template<typename T>
            struct NkIsPlatformSupported : NkTrueType {};

            #if !defined(__cpp_char8)
            template<>
            struct NkIsPlatformSupported<nk_char8> : NkFalseType {};
            #endif

            #if !defined(__SIZEOF_INT128__)
            template<>
            struct NkIsPlatformSupported<nk_int128> : NkFalseType {};
            template<>
            struct NkIsPlatformSupported<nk_uint128> : NkFalseType {};
            #endif

            template<typename T>
            inline constexpr bool NkIsPlatformSupported_v = NkIsPlatformSupported<T>::value;
        } // traits
    } // core
} // namespace nkentseu

#endif // NKENTSEU_CORE_NKCORE_SRC_NKCORE_TRAITS_NKTRAITS_H_INCLUDED

// ============================================================
// Copyright © 2024-2026 Rihen. All rights reserved.
// Proprietary License - Free to use and modify
//
// Generated by Rihen on 2026-02-07
// Creation Date: 2026-02-07
// ============================================================