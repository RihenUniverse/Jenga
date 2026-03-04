// Central Test Launcher & Result Aggregator
// Responsible for displaying all test results from all projects
// Unitest libraries are pre-compiled static libraries, linked to test executables

#pragma once

#include <vector>
#include <string>
#include <memory>
#include <map>
#include "UnitTestData.h"

namespace nkentseu {
    namespace test {
        
        // Interface for test executables to report results
        struct TestExecutableResult {
            std::string executable_name;
            std::string project_name;
            int exit_code;
            std::vector<UnitTestDataEntry> test_results;
            TestRunStatistics statistics;
            double duration_ms;
        };
        
        // Central aggregator for all test results
        class TestAggregator {
        public:
            static TestAggregator& GetInstance();
            
            // Register a test executable
            void RegisterTestExecutable(const std::string& name, 
                                       const std::string& path,
                                       const std::string& project_name);
            
            // Run all registered test executables
            bool RunAllTests();
            
            // Run specific test executable
            bool RunTestExecutable(const std::string& name);
            
            // Get aggregated results
            const std::vector<TestExecutableResult>& GetAllResults() const;
            TestRunStatistics GetAggregatedStatistics() const;
            
            // Display results (only Unitest does this)
            void DisplayResults();
            
        private:
            TestAggregator() = default;
            ~TestAggregator() = default;
            
            struct TestExecutable {
                std::string name;
                std::string path;
                std::string project_name;
            };
            
            std::vector<TestExecutable> mExecutables;
            std::vector<TestExecutableResult> mResults;
        };
        
    } // namespace test
} // namespace nkentseu
