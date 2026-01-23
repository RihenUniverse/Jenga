#include "TestReporter.h"
#include <iostream>
#include <chrono>
#include <iomanip>
#include <sstream>
#include <vector>
#include <ctime>

#ifdef _WIN32
    #include <windows.h>
#endif

namespace nkentseu {
    namespace test {

        ConsoleReporter::ConsoleReporter() 
            : mUseColors(true), mShowProgress(true), mVerbose(false),
              mShowSourceLinks(true), mCurrentTest(0), mTotalTests(0),
              mStartTime(std::chrono::steady_clock::now()) {
            
#ifdef _WIN32
            if (mUseColors) {
                HANDLE hConsole = GetStdHandle(STD_OUTPUT_HANDLE);
                if (hConsole != INVALID_HANDLE_VALUE) {
                    DWORD mode = 0;
                    if (GetConsoleMode(hConsole, &mode)) {
                        mode |= ENABLE_VIRTUAL_TERMINAL_PROCESSING;
                        SetConsoleMode(hConsole, mode);
                    }
                }
            }
#endif
        }
        
        ConsoleReporter::ConsoleReporter(bool useColors, bool showProgress, bool verbose)
            : mUseColors(useColors), mShowProgress(showProgress), mVerbose(verbose),
              mShowSourceLinks(true), mCurrentTest(0), mTotalTests(0),
              mStartTime(std::chrono::steady_clock::now()) {
            
#ifdef _WIN32
            if (mUseColors) {
                HANDLE hConsole = GetStdHandle(STD_OUTPUT_HANDLE);
                if (hConsole != INVALID_HANDLE_VALUE) {
                    DWORD mode = 0;
                    if (GetConsoleMode(hConsole, &mode)) {
                        mode |= ENABLE_VIRTUAL_TERMINAL_PROCESSING;
                        SetConsoleMode(hConsole, mode);
                    }
                }
            }
#endif
        }
        
        void ConsoleReporter::OnTestRunStart(size_t totalTests) {
            mTotalTests = totalTests;
            mCurrentTest = 0;
            mStartTime = std::chrono::steady_clock::now();
            
            // Afficher le banner UNITEST
            PrintUnitTestBanner();
            
            std::cout << "\n";
            
            if (mShowProgress) {
                std::cout << Colorize("Progression :\n", "33");
            }
        }
        
        void ConsoleReporter::PrintUnitTestBanner() {
            std::string cyan = "36";
            std::string blue = "34";
            std::string magenta = "35";
            std::string white = "37";
            std::string green = "32";
            std::string yellow = "33";
            
            // Définir la largeur du cadre
            const int frameWidth = 70;
            
            // Fonction helper pour centrer du texte
            auto CenterText = [frameWidth](const std::string& text) -> std::string {
                if (text.length() >= frameWidth) {
                    return text.substr(0, frameWidth);
                }
                int padding = (frameWidth - text.length() - 4) / 2;
                int leftPadding = padding;
                // int rightPadding = frameWidth - text.length() - leftPadding;
                int rightPadding = padding;
                
                // Assurer que les padding ne soient pas négatifs
                if (leftPadding < 0) leftPadding = 0;
                if (rightPadding < 0) rightPadding = 0;
                
                return std::string(leftPadding, ' ') + text + std::string(rightPadding, ' ');
            };
            
            // Ligne supérieure du cadre
            std::cout << Colorize("╔" + std::string(frameWidth, '=') + "╗\n", cyan);
            
            // Ligne vide
            std::cout << Colorize("║" + std::string(frameWidth, ' ') + "║\n", cyan);
            
            // Logo UNITEST en ASCII art
            std::vector<std::string> logo = {
                "     ██╗   ██╗███╗   ██╗██╗████████╗███████╗███████╗████████╗       ",
                "     ██║   ██║████╗  ██║██║╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝       ",
                "     ██║   ██║██╔██╗ ██║██║   ██║   █████╗  ███████╗   ██║          ",
                "     ██║   ██║██║╚██╗██║██║   ██║   ██╔══╝  ╚════██║   ██║          ",
                "     ╚██████╔╝██║ ╚████║██║   ██║   ███████╗███████║   ██║          ",
                "      ╚═════╝ ╚═╝  ╚═══╝╚═╝   ╚═╝   ╚══════╝╚══════╝   ╚═╝          "
            };
            
            // Afficher chaque ligne du logo centrée
            for (const auto& line : logo) {
                // std::string centeredLine = CenterText(line);
                std::string centeredLine = line;
                std::cout << Colorize("║ ", cyan);
                std::cout << Colorize(centeredLine, magenta);
                std::cout << Colorize(" ║\n", cyan);
            }
            
            // Ligne vide
            std::cout << Colorize("║" + std::string(frameWidth, ' ') + "║\n", cyan);
            
            // Version
            std::string version = "C++ Unit Testing Framework v1.0.0";
            std::cout << Colorize("║", cyan);
            std::cout << Colorize(CenterText(version), blue + ";1");
            std::cout << Colorize("     ║\n", cyan);
            
            // Description
            std::string description = "Fast, Reliable, and Developer-Friendly";
            std::cout << Colorize("║", cyan);
            std::cout << Colorize(CenterText(description), white);
            std::cout << Colorize("    ║\n", cyan);
            
            // Ligne vide
            std::cout << Colorize("║" + std::string(frameWidth, ' ') + "║\n", cyan);
            
            // Informations de configuration
            std::vector<std::string> configLines;
            
            if (mTotalTests > 0) {
                configLines.push_back("Number of tests: " + std::to_string(mTotalTests));
            }
            
            configLines.push_back("Verbose mode: " + std::string(mVerbose ? "enabled" : "disabled"));
            configLines.push_back("Colors: " + std::string(mUseColors ? "enabled" : "disabled"));
            configLines.push_back("Progress bar: " + std::string(mShowProgress ? "enabled" : "disabled"));
            
            // Afficher chaque ligne de configuration
            for (const auto& configLine : configLines) {
                std::cout << Colorize("║", cyan);
                
                // Ajouter un petit décalage à gauche pour l'esthétique
                std::string paddedLine = "  " + configLine;
                if (paddedLine.length() < frameWidth) {
                    paddedLine += std::string(frameWidth - paddedLine.length(), ' ');
                }
                
                std::cout << Colorize(paddedLine, green);
                std::cout << Colorize("║\n", cyan);
            }
            
            // Ligne vide
            std::cout << Colorize("║" + std::string(frameWidth, ' ') + "║\n", cyan);
            
            // Informations de session
            auto now = std::chrono::system_clock::now();
            std::time_t now_time = std::chrono::system_clock::to_time_t(now);
            std::tm* now_tm = std::localtime(&now_time);
            
            char timeBuffer[100];
            std::strftime(timeBuffer, sizeof(timeBuffer), "%Y-%m-%d %H:%M:%S", now_tm);
            std::string timeStr = "Session started: " + std::string(timeBuffer);
            
            std::cout << Colorize("║", cyan);
            std::cout << Colorize(CenterText(timeStr), "90");  // Gris clair
            std::cout << Colorize("    ║\n", cyan);
            
            // Ligne vide
            std::cout << Colorize("║" + std::string(frameWidth, ' ') + "║\n", cyan);
            
            // Ligne inférieure du cadre
            std::cout << Colorize("╚" + std::string(frameWidth, '=') + "╝\n", cyan);
        }
        
        void ConsoleReporter::OnTestCaseComplete(const UnitTestDataEntry& result) {
            mCurrentTest++;
            
            // Afficher immédiatement le résultat du test
            PrintLiveTestResult(result);
            
            // Mettre à jour la barre de progression
            if (mShowProgress) {
                UpdateProgressBar();
            }
        }
        
        void ConsoleReporter::OnTestRunComplete(const TestRunStatistics& statistics) {
            std::cout << "\n\n";
            PrintCleanSummary(statistics);
        }
        
        void ConsoleReporter::PrintLiveTestResult(const UnitTestDataEntry& result) {
            // Calculer le temps écoulé depuis le début
            auto now = std::chrono::steady_clock::now();
            auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(now - mStartTime).count();
            
            // Préparer l'indicateur de statut
            std::string statusSymbol, statusText, statusColor;
            
            if (result.mSkipped) {
                statusSymbol = "⏸";
                statusText = "SKIP";
                statusColor = "33";  // Jaune
            } else if (result.mSuccess) {
                statusSymbol = "✓";
                statusText = "OK";
                statusColor = "32";  // Vert
            } else {
                statusSymbol = "✗";
                statusText = "ECHEC";
                statusColor = "31";  // Rouge
            }
            
            // Afficher la ligne principale en temps réel
            std::cout << Colorize(statusSymbol + " ", statusColor + ";1");
            std::cout << std::left << std::setw(45) << result.mTestName;
            std::cout << " [" << Colorize(statusText, statusColor) << "]";
            
            // Afficher les statistiques
            std::cout << "  " << result.mPassedAsserts << "/" << result.mTotalAsserts << " assertions";
            std::cout << "  (" << FormatDuration(result.mTotalDurationMs) << ")";
            std::cout << std::endl;
            
            // Afficher les détails seulement en cas d'échec ou en mode verbeux
            if (!result.mSuccess && !result.mFailedAssertMessages.empty()) {
                PrintConciseFailureDetails(result);
            } else if (mVerbose && result.mTotalAsserts > 0) {
                PrintVerboseSuccessDetails(result);
            }
        }
        
        void ConsoleReporter::PrintConciseFailureDetails(const UnitTestDataEntry& result) {
            std::cout << Colorize("  → Premier échec : ", "31");
            
            if (!result.mFailedAssertMessages.empty()) {
                // Prendre seulement le premier message d'échec pour la concision
                std::string firstFailure = result.mFailedAssertMessages[0];
                
                // Nettoyer et afficher le message
                std::istringstream iss(firstFailure);
                std::string line;
                bool firstLine = true;
                
                while (std::getline(iss, line)) {
                    if (firstLine) {
                        // Afficher la première ligne (le message principal)
                        size_t newlinePos = line.find('\n');
                        if (newlinePos != std::string::npos) {
                            line = line.substr(0, newlinePos);
                        }
                        
                        // Tronquer si trop long
                        if (line.length() > 60) {
                            line = line.substr(0, 57) + "...";
                        }
                        
                        std::cout << Colorize(line, "37;1");
                        firstLine = false;
                    }
                }
                
                std::cout << std::endl;
                
                // Afficher le lien source si disponible
                if (mShowSourceLinks) {
                    // Essayer d'extraire la localisation
                    std::string location;
                    size_t locPos = firstFailure.find("Location: ");
                    if (locPos != std::string::npos) {
                        location = firstFailure.substr(locPos + 10);
                        size_t endPos = location.find('\n');
                        if (endPos != std::string::npos) {
                            location = location.substr(0, endPos);
                        }
                        
                        std::cout << Colorize("  📍 ", "36") << FormatClickableLink(location) << std::endl;
                    }
                }
            }
            
            if (result.mFailedAssertMessages.size() > 1) {
                std::cout << Colorize("  → " + std::to_string(result.mFailedAssertMessages.size() - 1) 
                                    + " autre(s) échec(s) masqué(s)", "90") << std::endl;
            }
        }
        
        void ConsoleReporter::PrintVerboseSuccessDetails(const UnitTestDataEntry& result) {
            if (result.mTotalAsserts > 0) {
                double avgTime = result.mTotalAsserts > 0 ? 
                    result.mTotalDurationMs / result.mTotalAsserts : 0;
                
                std::cout << Colorize("  ✓ ", "32") 
                         << result.mTotalAsserts << " assertion(s) réussie(s)";
                std::cout << Colorize(" (moy: " + FormatDuration(avgTime) + "/assert)", "90");
                std::cout << std::endl;
            }
        }
        
        void ConsoleReporter::UpdateProgressBar() {
            if (mTotalTests == 0) return;
            
            float progress = static_cast<float>(mCurrentTest) / mTotalTests;
            int barWidth = 30;
            int pos = static_cast<int>(barWidth * progress);
            
            std::cout << "\r";
            std::cout << Colorize("  [", "36");
            
            // Barre de progression
            for (int i = 0; i < barWidth; ++i) {
                if (i < pos) {
                    std::cout << Colorize("█", "32");
                } else if (i == pos) {
                    std::cout << Colorize("▶", "33");
                } else {
                    std::cout << "░";
                }
            }
            
            std::cout << Colorize("]", "36");
            
            // Pourcentage et compteur
            std::cout << " " << std::setw(3) << static_cast<int>(progress * 100) << "%";
            std::cout << " (" << mCurrentTest << "/" << mTotalTests << ")";
            
            // Temps écoulé et ETA
            auto now = std::chrono::steady_clock::now();
            auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(now - mStartTime).count();
            
            std::cout << Colorize(" Temps: " + FormatDuration(elapsed), "90");
            
            if (mCurrentTest > 0 && mCurrentTest < mTotalTests) {
                double timePerTest = static_cast<double>(elapsed) / mCurrentTest;
                double remainingTime = timePerTest * (mTotalTests - mCurrentTest);
                
                std::cout << Colorize(" Restant: ~" + FormatDuration(remainingTime), "90");
            }
            
            std::cout << std::flush;
            
            // Nouvelle ligne quand terminé
            if (mCurrentTest == mTotalTests) {
                std::cout << "\n";
            }
        }
        
        void ConsoleReporter::PrintCleanSummary(const TestRunStatistics& statistics) {
            // Calcul des taux de succès
            double testSuccessRate = (statistics.mTotalTestCases - statistics.mSkippedTestCases) > 0 ?
                (static_cast<double>(statistics.mPassedTestCases) / 
                 (statistics.mTotalTestCases - statistics.mSkippedTestCases)) * 100.0 : 100.0;
            
            double assertSuccessRate = statistics.mTotalAssertions > 0 ?
                (static_cast<double>(statistics.mPassedAssertions) / 
                 statistics.mTotalAssertions) * 100.0 : 100.0;
            
            // En-tête du résumé
            std::cout << Colorize("┌────────────────────── RÉSULTATS DES TESTS ──────────────────────┐\n", "36");
            
            // Ligne 1 : Résumé global
            std::string overallStatus;
            std::string overallColor;
            
            if (statistics.mFailedTestCases == 0) {
                overallStatus = "SUCCÈS";
                overallColor = "32;1";  // Vert brillant
            } else {
                overallStatus = "ÉCHEC";
                overallColor = "31;1";  // Rouge brillant
            }
            
            std::cout << Colorize("│ ", "36") 
                     << Colorize(overallStatus, overallColor)
                     << std::string(52 - overallStatus.length(), ' ') 
                     << Colorize("             │\n", "36");
            
            // Séparateur
            std::cout << Colorize("├─────────────────────────────────────────────────────────────────┤\n", "36");
            
            // Statistiques détaillées
            std::cout << Colorize("│ Tests :      ", "36");
            std::cout << Colorize(std::to_string(statistics.mPassedTestCases), "32") << " réussis, ";
            
            if (statistics.mFailedTestCases > 0) {
                std::cout << Colorize(std::to_string(statistics.mFailedAssertions), "31") << " échoués, ";
            }
            
            if (statistics.mSkippedTestCases > 0) {
                std::cout << Colorize(std::to_string(statistics.mSkippedTestCases), "33") << " ignorés, ";
            }
            
            std::cout << statistics.mTotalTestCases << " au total";
            std::cout << std::string(10, ' ') << Colorize("│\n", "36");
            
            std::cout << Colorize("│ Assertions : ", "36");
            std::cout << Colorize(std::to_string(statistics.mPassedAssertions), "32") << " réussies, ";
            
            if (statistics.mFailedAssertions > 0) {
                std::cout << Colorize(std::to_string(statistics.mFailedAssertions), "31") << " échouées, ";
            }
            
            std::cout << statistics.mTotalAssertions << " au total";
            std::cout << std::string(9, ' ') << Colorize("│\n", "36");
            
            std::cout << Colorize("│ Taux succès : ", "36");
            std::cout << "Tests: " << std::fixed << std::setprecision(1) << testSuccessRate << "%, ";
            std::cout << "Assertions: " << assertSuccessRate << "%";
            std::cout << std::string(8, ' ') << Colorize("│\n", "36");
            
            std::cout << Colorize("│ Temps total : ", "36");
            std::cout << FormatDuration(statistics.mTotalExecutionTimeMs);
            std::cout << " (" << FormatDuration(statistics.mAverageTestTimeMs) << "/test)";
            std::cout << std::string(5, ' ') << Colorize("│\n", "36");
            
            // Pied de tableau
            std::cout << Colorize("└──────────────────────────────────────────────────────────────┘\n", "36");
            
            // Messages supplémentaires
            if (statistics.mFailedTestCases > 0) {
                std::cout << "\n" << Colorize("🔍 Pour déboguer :\n", "33;1");
                std::cout << Colorize("  • Voir les détails des échecs ci-dessus\n", "37");
                std::cout << Colorize("  • Lancer un test spécifique : ./tests --filter=NOM_DU_TEST\n", "37");
                std::cout << Colorize("  • Activer le mode détaillé : ./tests --verbose\n", "37");
            } else if (statistics.mTotalTestCases > 0) {
                std::cout << "\n" << Colorize("✅ Tous les tests sont réussis !\n", "32;1");
            }
            
            std::cout << std::endl;
        }
        
        std::string ConsoleReporter::FormatClickableLink(const std::string& location) const {
            if (!mUseColors || !mShowSourceLinks) {
                return location;
            }
            
            std::ostringstream oss;
            oss << "\033]8;;file://" << location << "\033\\";
            oss << Colorize(location, "94;4");
            oss << "\033]8;;\033\\";
            return oss.str();
        }
        
        std::string ConsoleReporter::Colorize(const std::string& text, const std::string& colorCode) const {
            if (!mUseColors) return text;
            
            std::ostringstream oss;
            oss << "\033[" << colorCode << "m" << text << "\033[0m";
            return oss.str();
        }
        
        std::string ConsoleReporter::FormatDuration(double ms) const {
            if (ms < 1.0) {
                return "< 1ms";
            } else if (ms < 1000.0) {
                return std::to_string(static_cast<int>(ms)) + "ms";
            } else {
                double seconds = ms / 1000.0;
                if (seconds < 60.0) {
                    return std::to_string(static_cast<int>(seconds * 10) / 10.0) + "s";
                } else {
                    int minutes = static_cast<int>(seconds / 60.0);
                    int secs = static_cast<int>(seconds) % 60;
                    return std::to_string(minutes) + "m " + std::to_string(secs) + "s";
                }
            }
        }
    }
}