#include "TestRunner.h"
#include "TestCase.h"
#include "TestReporter.h"
#include "TestAssert.h"
#include <iostream>
#include <algorithm>
#include <thread>
#include <future>
#include <fstream>

#ifdef _WIN32
    #pragma execution_character_set("utf-8")
    #include <windows.h>

    namespace nkentseu {
        namespace console {
            void InitUtf8() {
                SetConsoleOutputCP(CP_UTF8);
                SetConsoleCP(CP_UTF8);
            }
        }
    }

#else
    #include <clocale>
    #include <cstdlib>

    namespace nkentseu {
        namespace console {
            void InitUtf8() {
                // Active locale UTF-8 du système
                std::setlocale(LC_ALL, "");

                // Optionnel mais utile
                setenv("LANG", "en_US.UTF-8", 0);
                setenv("LC_ALL", "en_US.UTF-8", 0);
            }
        }
    }
#endif


namespace nkentseu {
    namespace test {
        TestRunner& TestRunner::GetInstance() {
            static TestRunner sInstance;
            return sInstance;
        }
        
        TestRunner::TestRunner() 
            : mTestTimeoutMs(30000.0), mCompletedTests(0) {
            mStatistics = TestRunStatistics();
        }
        
        void TestRunner::Configure(const TestConfiguration& config) {
            mConfig = config;
            TestAssert::SetStopOnFailure(config.mStopOnFirstFailure);
        }
        
        void TestRunner::AddTestCase(const std::string& name,
                                   std::function<std::unique_ptr<TestCase>()> factory) {
            mTestFactories[name] = std::move(factory);
        }
        
        bool TestRunner::RunAllTests() {
            std::vector<std::string> testNames;
            for (const auto& pair : mTestFactories) {
                testNames.push_back(pair.first);
            }
            return RunTests(testNames);
        }
        
        bool TestRunner::RunTests(const std::vector<std::string>& testNames) {
            Reset();
            
            mStatistics.mTotalTestCases = 0;
            for (const auto& testName : testNames) {
                if (ShouldRunTest(testName)) {
                    mStatistics.mTotalTestCases++;
                }
            }
            
            // Notifier le début des tests
            for (auto& reporter : mReporters) {
                reporter->OnTestRunStart(mStatistics.mTotalTestCases);
            }
            
            std::vector<UnitTestDataEntry> results;
            
            if (mConfig.mRunInParallel && mConfig.mThreadCount > 1) {
                // Exécution parallèle
                std::vector<std::future<UnitTestDataEntry>> futures;
                std::mutex resultsMutex;
                
                for (const auto& testName : testNames) {
                    if (!ShouldRunTest(testName)) {
                        continue;
                    }
                    
                    auto it = mTestFactories.find(testName);
                    if (it == mTestFactories.end()) {
                        continue;
                    }
                    
                    futures.emplace_back(std::async(std::launch::async, 
                        [this, &testName, &it, &resultsMutex]() {
                            auto result = RunSingleTest(testName, it->second);
                            
                            std::lock_guard<std::mutex> lock(resultsMutex);
                            mCompletedTests++;
                            for (auto& reporter : mReporters) {
                                reporter->OnTestCaseComplete(result);
                            }
                            return result;
                        }));
                }
                
                for (auto& future : futures) {
                    results.push_back(future.get());
                }
            } else {
                // Exécution séquentielle
                for (const auto& testName : testNames) {
                    if (!ShouldRunTest(testName)) {
                        UnitTestDataEntry skippedResult;
                        skippedResult.mTestName = testName;
                        skippedResult.mSkipped = true;
                        skippedResult.mSkipReason = "Filtered out";
                        skippedResult.mSuccess = true;
                        mStatistics.mSkippedTestCases++;
                        continue;
                    }
                    
                    auto it = mTestFactories.find(testName);
                    if (it != mTestFactories.end()) {
                        auto result = RunSingleTest(testName, it->second);
                        results.push_back(result);
                        
                        mCompletedTests++;
                        for (auto& reporter : mReporters) {
                            reporter->OnTestCaseComplete(result);
                        }
                        
                        if (mConfig.mStopOnFirstFailure && !result.mSuccess) {
                            break;
                        }
                    }
                }
            }
            
            mResults = results;
            
            // Calculer les statistiques finales
            CalculateAverages();
            
            // Notifier la fin des tests
            for (auto& reporter : mReporters) {
                reporter->OnTestRunComplete(mStatistics);
            }
            
            return mStatistics.mFailedTestCases == 0;
        }
        
        bool TestRunner::ShouldRunTest(const std::string& testName) const {
            // Vérifier les exclusions
            for (const auto& exclusion : mConfig.mTestExclusions) {
                if (testName.find(exclusion) != std::string::npos) {
                    return false;
                }
            }
            
            // Vérifier les filtres
            if (mConfig.mTestFilters.empty()) {
                return true;
            }
            
            for (const auto& filter : mConfig.mTestFilters) {
                if (testName.find(filter) != std::string::npos) {
                    return true;
                }
            }
            return false;
        }
        
        UnitTestDataEntry TestRunner::RunSingleTest(
            const std::string& name,
            std::function<std::unique_ptr<TestCase>()>& factory) {
            
            UnitTestDataEntry entry;
            entry.mTestName = name;
            
            try {
                auto start = std::chrono::high_resolution_clock::now();
                
                // Créer et exécuter le test
                auto testCase = factory();
                if (mConfig.mDebugMode) {
                    testCase->SetStopOnFailure(true);
                }
                
                TestAssert::sCurrentTest = testCase.get();
                testCase->Run();
                
                auto end = std::chrono::high_resolution_clock::now();
                entry.mTotalDurationMs = 
                    std::chrono::duration<double, std::milli>(end - start).count();
                
                // Collecter les résultats
                const auto& assertResults = testCase->GetAssertResults();
                entry.mTotalAsserts = assertResults.size();
                
                for (const auto& result : assertResults) {
                    if (result.mSuccess) {
                        entry.mPassedAsserts++;  // Incrémenter le compteur
                        entry.mPassedAssertExpressions.push_back(result.mExpression);
                    } else {
                        entry.mFailedAsserts++;  // Incrémenter le compteur
                        std::string failureMsg = result.mMessage;
                        if (!result.mExpression.empty()) {
                            failureMsg += "\n  Expression: " + result.mExpression;
                        }
                        failureMsg += " (" + result.mFile + ":" + 
                                    std::to_string(result.mLine) + ")";
                        entry.mFailedAssertMessages.push_back(failureMsg);
                    }
                }
                
                entry.mSuccess = (entry.mFailedAsserts == 0);
                
                // Calculer la durée moyenne par assertion
                if (entry.mTotalAsserts > 0) {
                    entry.mAverageAssertDurationMs = entry.mTotalDurationMs / entry.mTotalAsserts;
                }
                
                // Mettre à jour les statistiques
                UpdateStatistics(entry);
                
            } catch (const std::exception& e) {
                entry.mSuccess = false;
                entry.mFailedAsserts++;  // Incrémenter le compteur
                entry.mFailedAssertMessages.push_back(std::string("Unhandled exception: ") + e.what());
                UpdateStatistics(entry);
            } catch (...) {
                entry.mSuccess = false;
                entry.mFailedAsserts++;  // Incrémenter le compteur
                entry.mFailedAssertMessages.push_back("Unknown exception");
                UpdateStatistics(entry);
            }
            
            return entry;
        }
        
        void TestRunner::UpdateStatistics(const UnitTestDataEntry& result) {
            std::lock_guard<std::mutex> lock(mMutex);
            
            if (result.mSkipped) {
                mStatistics.mSkippedTestCases++;
                return;
            }
            
            mStatistics.mTotalAssertions += result.mTotalAsserts;
            mStatistics.mPassedAssertions += result.mPassedAsserts;  // Utiliser le compteur
            mStatistics.mFailedAssertions += result.mFailedAsserts;  // Utiliser le compteur
            mStatistics.mTotalExecutionTimeMs += result.mTotalDurationMs;
            
            if (result.mSuccess) {
                mStatistics.mPassedTestCases++;
            } else {
                mStatistics.mFailedTestCases++;
            }
        }
        
        void TestRunner::CalculateAverages() {
            if (mStatistics.mTotalTestCases > 0) {
                mStatistics.mAverageTestTimeMs = 
                    mStatistics.mTotalExecutionTimeMs / mStatistics.mTotalTestCases;
            }
            
            if (mStatistics.mTotalAssertions > 0) {
                mStatistics.mAverageAssertTimeMs = 
                    mStatistics.mTotalExecutionTimeMs / mStatistics.mTotalAssertions;
            }
        }
        
        void TestRunner::AddReporter(std::shared_ptr<ITestReporter> reporter) {
            mReporters.push_back(reporter);
        }
        
        void TestRunner::RemoveAllReporters() {
            mReporters.clear();
        }
        
        void TestRunner::SetDefaultReporters() {
            RemoveAllReporters();
            
            auto consoleReporter = std::make_shared<ConsoleReporter>();
            consoleReporter->SetUseColors(mConfig.mUseColors);
            consoleReporter->SetShowProgress(mConfig.mShowProgressBar);
            consoleReporter->SetVerbose(mConfig.mVerboseOutput);
            
            mReporters.push_back(consoleReporter);
            
            if (!mConfig.mReportFile.empty()) {
                // Pourrait ajouter un FileReporter ici
            }
        }
        
        void TestRunner::Reset() {
            mResults.clear();
            mStatistics = TestRunStatistics();
            mCompletedTests = 0;
        }

        void TestRunner::EnablePerformanceTracking(bool enable) { 
            mTrackPerformance = enable; 
            if (enable && !mPerformanceReporter) {
                mPerformanceReporter = std::make_shared<PerformanceReporter>();
            }
        }
        
        std::shared_ptr<PerformanceReporter> TestRunner::GetPerformanceReporter() const { 
            return mPerformanceReporter; 
        }
        
        int RunUnitTests(int argc, char** argv) {
            nkentseu::console::InitUtf8();

            TestConfiguration config;
            
            // Parser les arguments de ligne de commande
            if (argc > 0 && argv != nullptr) {
                for (int i = 1; i < argc; ++i) {
                    std::string arg = argv[i];
                    
                    if (arg == "--help" || arg == "-h") {
                        std::cout << "Unit Test Runner Usage:\n";
                        std::cout << "  --help, -h              Show this help\n";
                        std::cout << "  --verbose, -v           Verbose output\n";
                        std::cout << "  --quiet, -q             Quiet output\n";
                        std::cout << "  --stop-on-failure, -f   Stop on first failure\n";
                        std::cout << "  --no-colors             Disable colored output\n";
                        std::cout << "  --no-progress           Disable progress bar\n";
                        std::cout << "  --debug                 Enable debug mode\n";
                        std::cout << "  --filter=PATTERN        Run tests matching pattern\n";
                        std::cout << "  --exclude=PATTERN       Exclude tests matching pattern\n";
                        std::cout << "  --parallel[=N]          Run tests in parallel (N threads)\n";
                        std::cout << "  --repeat=N              Repeat tests N times\n";
                        std::cout << "  --report=FILE           Generate report file\n";
                        return 0;
                    } else if (arg == "--verbose" || arg == "-v") {
                        config.mVerboseOutput = true;
                    } else if (arg == "--quiet" || arg == "-q") {
                        config.mVerboseOutput = false;
                        config.mShowProgressBar = false;
                    } else if (arg == "--stop-on-failure" || arg == "-f") {
                        config.mStopOnFirstFailure = true;
                    } else if (arg == "--no-colors") {
                        config.mUseColors = false;
                    } else if (arg == "--no-progress") {
                        config.mShowProgressBar = false;
                    } else if (arg == "--debug") {
                        config.mDebugMode = true;
                    } else if (arg.find("--filter=") == 0) {
                        config.mTestFilters.push_back(arg.substr(9));
                    } else if (arg.find("--exclude=") == 0) {
                        config.mTestExclusions.push_back(arg.substr(10));
                    } else if (arg == "--parallel") {
                        config.mRunInParallel = true;
                        config.mThreadCount = std::thread::hardware_concurrency();
                    } else if (arg.find("--parallel=") == 0) {
                        config.mRunInParallel = true;
                        config.mThreadCount = std::stoi(arg.substr(11));
                    } else if (arg.find("--repeat=") == 0) {
                        config.mRepeatCount = std::stoi(arg.substr(9));
                    } else if (arg.find("--report=") == 0) {
                        config.mReportFile = arg.substr(9);
                    }
                }
            }
            
            return RunUnitTests(config);
        }
        
        int RunUnitTests(const TestConfiguration& config) {
            // Enregistrer tous les tests
            detail::TestCaseAutoRegistrar::GetInstance().RegisterAll();
            
            auto& runner = TestRunner::GetInstance();
            runner.Configure(config);
            runner.SetDefaultReporters();
            
            bool success = true;
            for (int i = 0; i < config.mRepeatCount; ++i) {
                if (config.mRepeatCount > 1) {
                    std::cout << "\n=== Run " << (i + 1) << " of " << config.mRepeatCount << " ===\n";
                }
                success = runner.RunAllTests() && success;
                
                if (config.mStopOnFirstFailure && !success) {
                    break;
                }
            }
            
            return success ? 0 : 1;
        }
    }
}