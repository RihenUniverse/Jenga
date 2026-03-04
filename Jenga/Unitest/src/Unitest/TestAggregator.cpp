// Implementation of Central Test Launcher & Result Aggregator
// ONLY Unitest is responsible for displaying test results

#include "TestAggregator.h"
#include "TestReporter.h"
#include "ConsoleReport.h"
#include <iostream>
#include <cstdlib>
#include <chrono>
#include <algorithm>

namespace nkentseu {
    namespace test {
        
        TestAggregator& TestAggregator::GetInstance() {
            static TestAggregator instance;
            return instance;
        }
        
        void TestAggregator::RegisterTestExecutable(const std::string& name,
                                                    const std::string& path,
                                                    const std::string& project_name) {
            mExecutables.push_back({name, path, project_name});
        }
        
        bool TestAggregator::RunAllTests() {
            bool all_passed = true;
            
            for (const auto& exe : mExecutables) {
                if (!RunTestExecutable(exe.name)) {
                    all_passed = false;
                }
            }
            
            // Display aggregated results
            DisplayResults();
            
            return all_passed;
        }
        
        bool TestAggregator::RunTestExecutable(const std::string& name) {
            auto it = std::find_if(mExecutables.begin(), mExecutables.end(),
                [&name](const TestExecutable& exe) { return exe.name == name; });
            
            if (it == mExecutables.end()) {
                std::cerr << "Test executable not found: " << name << std::endl;
                return false;
            }
            
            auto start = std::chrono::high_resolution_clock::now();
            
            // Execute the test executable
            int ret = std::system(it->path.c_str());
            
            auto end = std::chrono::high_resolution_clock::now();
            auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
            
            TestExecutableResult result;
            result.executable_name = name;
            result.project_name = it->project_name;
            result.exit_code = ret;
            result.duration_ms = duration.count();
            
            mResults.push_back(result);
            
            return ret == 0;
        }
        
        const std::vector<TestExecutableResult>& TestAggregator::GetAllResults() const {
            return mResults;
        }
        
        TestRunStatistics TestAggregator::GetAggregatedStatistics() const {
            TestRunStatistics stats;
            
            for (const auto& result : mResults) {
                stats.mTotalTestCases += result.statistics.mTotalTestCases;
                stats.mPassedTestCases += result.statistics.mPassedTestCases;
                stats.mFailedTestCases += result.statistics.mFailedTestCases;
                stats.mSkippedTestCases += result.statistics.mSkippedTestCases;
                stats.mTotalAssertions += result.statistics.mTotalAssertions;
                stats.mPassedAssertions += result.statistics.mPassedAssertions;
                stats.mFailedAssertions += result.statistics.mFailedAssertions;
                stats.mTotalExecutionTimeMs += result.duration_ms;
            }
            
            return stats;
        }
        
        void TestAggregator::DisplayResults() {
            std::cout << "\n" << std::string(80, '=') << std::endl;
            std::cout << "UNIT TEST EXECUTION SUMMARY" << std::endl;
            std::cout << std::string(80, '=') << std::endl;
            
            for (const auto& result : mResults) {
                std::cout << "\nProject: " << result.project_name << std::endl;
                std::cout << "Executable: " << result.executable_name << std::endl;
                std::cout << "Exit Code: " << result.exit_code << std::endl;
                std::cout << "Duration: " << result.duration_ms << "ms" << std::endl;
                
                if (!result.test_results.empty()) {
                    std::cout << "Test Results:" << std::endl;
                    for (const auto& test : result.test_results) {
                        std::string status = test.mSuccess ? "✓ PASS" : "✗ FAIL";
                        std::cout << "  " << status << " - " << test.mTestName 
                                  << " (" << test.mTotalDurationMs << "ms)" << std::endl;
                    }
                }
            }
            
            auto aggregated = GetAggregatedStatistics();
            
            std::cout << "\n" << std::string(80, '=') << std::endl;
            std::cout << "AGGREGATED RESULTS" << std::endl;
            std::cout << std::string(80, '=') << std::endl;
            std::cout << "Total Test Cases: " << aggregated.mTotalTestCases << std::endl;
            std::cout << "Passed: " << aggregated.mPassedTestCases << std::endl;
            std::cout << "Failed: " << aggregated.mFailedTestCases << std::endl;
            std::cout << "Skipped: " << aggregated.mSkippedTestCases << std::endl;
            std::cout << "Total Assertions: " << aggregated.mTotalAssertions << std::endl;
            std::cout << "Passed Assertions: " << aggregated.mPassedAssertions << std::endl;
            std::cout << "Failed Assertions: " << aggregated.mFailedAssertions << std::endl;
            std::cout << "Total Duration: " << aggregated.mTotalExecutionTimeMs << "ms" << std::endl;
            std::cout << std::string(80, '=') << std::endl;
        }
        
    } // namespace test
} // namespace nkentseu
