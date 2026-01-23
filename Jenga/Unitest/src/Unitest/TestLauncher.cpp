// TestLauncher.cpp
// Implémentation du lanceur centralisé de tests

#include "Unitest/TestLauncher.h"
#include "Unitest/TestAggregator.h"
#include <iostream>
#include <cstdlib>
#include <iomanip>

namespace nkentseu {
namespace test {

    TestLauncher& TestLauncher::GetInstance()
    {
        static TestLauncher instance;
        return instance;
    }

    void TestLauncher::RegisterTestExecutable(
        const std::string& testName,
        const std::string& executablePath,
        const std::string& projectName)
    {
        TestExecutableInfo info;
        info.testName = testName;
        info.executablePath = executablePath;
        info.projectName = projectName;
        registeredTests.push_back(info);
    }

    int TestLauncher::RunAllTestsAndReport()
    {
        if (registeredTests.empty()) {
            std::cerr << "[TestLauncher] Aucun test enregistré!" << std::endl;
            return 1;
        }

        std::cout << "\n" << std::string(70, '=') << std::endl;
        std::cout << "TEST LAUNCHER - Exécution Centralisée des Tests" << std::endl;
        std::cout << std::string(70, '=') << std::endl;

        int totalTests = registeredTests.size();
        int passedTests = 0;

        for (size_t i = 0; i < registeredTests.size(); ++i) {
            auto& testInfo = registeredTests[i];

            std::cout << "\n[" << (i + 1) << "/" << totalTests << "] "
                      << "Lancement: " << testInfo.testName
                      << " (Projet: " << testInfo.projectName << ")" << std::endl;
            std::cout << "  Chemin: " << testInfo.executablePath << std::endl;

            // Exécuter le test
            testInfo.exitCode = std::system(testInfo.executablePath.c_str());
            testInfo.executed = true;

            if (testInfo.exitCode == 0) {
                std::cout << "  ✓ PASSED" << std::endl;
                passedTests++;
            } else {
                std::cout << "  ✗ FAILED (exit code: " << testInfo.exitCode << ")" << std::endl;
            }
        }

        // Affichage final (CENTRALISÉ)
        std::cout << "\n" << std::string(70, '=') << std::endl;
        std::cout << "RÉSUMÉ GLOBAL" << std::endl;
        std::cout << std::string(70, '=') << std::endl;

        for (const auto& testInfo : registeredTests) {
            std::string status = (testInfo.exitCode == 0) ? "✓ PASSED" : "✗ FAILED";
            std::cout << std::setw(30) << std::left << testInfo.testName
                      << " : " << status << std::endl;
        }

        std::cout << "\n" << std::string(70, '-') << std::endl;
        std::cout << "Total: " << passedTests << "/" << totalTests << " projets réussis";

        if (passedTests == totalTests) {
            std::cout << " ✓ SUCCÈS COMPLET" << std::endl;
        } else {
            std::cout << " ✗ ÉCHECS DÉTECTÉS" << std::endl;
        }

        std::cout << std::string(70, '=') << "\n" << std::endl;

        // Retourner 0 si tous passed, >0 sinon
        return (passedTests == totalTests) ? 0 : 1;
    }

    int TestLauncher::RunSpecificTest(const std::string& testName)
    {
        for (auto& testInfo : registeredTests) {
            if (testInfo.testName == testName) {
                std::cout << "Lancement du test: " << testName << std::endl;
                testInfo.exitCode = std::system(testInfo.executablePath.c_str());
                testInfo.executed = true;
                return testInfo.exitCode;
            }
        }

        std::cerr << "Test non trouvé: " << testName << std::endl;
        return 1;
    }

    size_t TestLauncher::GetTestCount() const
    {
        return registeredTests.size();
    }

} // namespace test
} // namespace nkentseu
