// TestLauncher.h
// Lanceur centralisé pour l'exécution des tests
// Ce composant coordonne l'exécution de tous les projets de test

#pragma once

#include <string>
#include <vector>

namespace nkentseu {
namespace test {

    /**
     * @class TestLauncher
     * @brief Coordonne l'exécution centralisée de tous les tests du projet
     * 
     * Responsabilités:
     * - Découvrir les exécutables de test
     * - Les exécuter dans l'ordre
     * - Agréger les résultats via TestAggregator
     * - Afficher un résumé global (une seule fois)
     * 
     * Avantages:
     * - Affichage unique et centralisé
     * - Pas de duplication de résultats
     * - Vue d'ensemble immédiate
     */
    class TestLauncher
    {
    public:
        /**
         * Singleton instance accessor
         */
        static TestLauncher& GetInstance();

        /**
         * @brief Enregistre un exécutable de test
         * @param testName Nom du test (ex: "CoreTests")
         * @param executablePath Chemin complet vers l'exécutable
         * @param projectName Nom du projet testé (ex: "Core")
         */
        void RegisterTestExecutable(
            const std::string& testName,
            const std::string& executablePath,
            const std::string& projectName
        );

        /**
         * @brief Lance tous les tests et affiche les résultats
         * @return Code de sortie (0 = tous passed, >0 = au moins un failed)
         * 
         * Processus:
         * 1. Lance chaque exécutable de test enregistré
         * 2. Capture les résultats via TestAggregator
         * 3. Affiche un résumé global à la fin
         */
        int RunAllTestsAndReport();

        /**
         * @brief Lance un test spécifique
         * @param testName Nom du test
         * @return Code de sortie du test
         */
        int RunSpecificTest(const std::string& testName);

        /**
         * @brief Obtient le nombre de tests enregistrés
         */
        size_t GetTestCount() const;

    private:
        TestLauncher() = default;
        ~TestLauncher() = default;
        TestLauncher(const TestLauncher&) = delete;
        TestLauncher& operator=(const TestLauncher&) = delete;

        struct TestExecutableInfo
        {
            std::string testName;
            std::string executablePath;
            std::string projectName;
            int exitCode = -1;
            bool executed = false;
        };

        std::vector<TestExecutableInfo> registeredTests;
    };

} // namespace test
} // namespace nkentseu
