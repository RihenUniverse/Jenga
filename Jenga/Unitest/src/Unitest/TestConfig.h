#pragma once
#include <cstddef>

// Configuration du framework de tests

namespace nkentseu {
    namespace test {
        // Constantes de configuration
        constexpr const char* FRAMEWORK_NAME = "UnitTest Framework";
        constexpr const char* FRAMEWORK_VERSION = "1.0.0";
        constexpr const char* FRAMEWORK_AUTHOR = "nkentseu";
        
        // Constantes de performance
        constexpr double DEFAULT_TEST_TIMEOUT_MS = 30000.0; // 30 secondes
        constexpr double WARNING_EXECUTION_TIME_MS = 1000.0; // 1 seconde
        constexpr double CRITICAL_EXECUTION_TIME_MS = 5000.0; // 5 secondes
        
        // Constantes d'affichage
        constexpr size_t MAX_TEST_NAME_LENGTH = 50;
        constexpr size_t PROGRESS_BAR_WIDTH = 40;
        constexpr size_t SUMMARY_WIDTH = 80;
        
        // Niveaux de verbosité
        enum class VerbosityLevel {
            QUIET = 0,      // Aucun output sauf les erreurs
            NORMAL = 1,     // Output normal (par défaut)
            VERBOSE = 2,    // Plus de détails
            DETAILED = 3    // Tous les détails, y compris internes
        };
        
        // Formats de sortie
        enum class OutputFormat {
            CONSOLE = 0,    // Format console avec couleurs
            PLAIN = 1,      // Format texte simple
            JSON = 2,       // Format JSON
            XML = 3,        // Format XML (JUnit)
            HTML = 4        // Format HTML
        };
        
        // Niveaux de sévérité
        enum class SeverityLevel {
            INFO = 0,
            WARNING = 1,
            ERROR = 2,
            CRITICAL = 3
        };
    }
}