#pragma once

// Macro principale pour créer automatiquement le point d'entrée
// Utilisation: inclure ce fichier dans un seul .cpp de votre projet
// qui contiendra le main automatique

#if !defined(UNIT_TEST_NO_AUTO_MAIN) && !defined(UNIT_TEST_CUSTOM_MAIN)

// Forward declaration pour éviter les dépendances circulaires
namespace nkentseu { namespace test { int RunUnitTests(int argc, char** argv); } }

// Macro pour créer un main automatique avec arguments
#define UNIT_TEST_AUTO_MAIN() \
int main(int argc, char** argv) { \
    return nkentseu::test::RunUnitTests(argc, argv); \
}

// Macro pour créer un main automatique sans arguments
#define UNIT_TEST_SIMPLE_MAIN() \
int main() { \
    return nkentseu::test::RunUnitTests(0, nullptr); \
}

// Macro pour créer un main avec configuration personnalisée
#define UNIT_TEST_CUSTOM_CONFIG(config) \
int main(int argc, char** argv) { \
    nkentseu::test::TestConfiguration configVar = config; \
    (void)argc; (void)argv; \
    return nkentseu::test::RunUnitTests(configVar); \
}

// Définition automatique du main si aucune macro n'est définie
// Cela permet à l'utilisateur de simplement inclure AutoMain.h
// sans avoir à écrire de code supplémentaire
#ifdef UNIT_TEST_AUTO_DEFINE_MAIN
UNIT_TEST_SIMPLE_MAIN()
#endif

#else
// Si l'utilisateur définit UNIT_TEST_NO_AUTO_MAIN ou UNIT_TEST_CUSTOM_MAIN,
// alors nous ne définissons pas de main automatique
#endif