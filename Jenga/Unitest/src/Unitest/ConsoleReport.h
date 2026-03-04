#pragma once

#include "TestReporter.h"
#include <string>
#include <vector>
#include <memory>

namespace nkentseu {
    namespace test {
        /**
         * ConsoleReport - Facade for reporting test results to console
         * Used by Python TestManager.py via CLI interface
         * 
         * Provides clean API for:
         * - Test run initialization
         * - Per-test result reporting  
         * - Summary statistics output
         * - Colored/formatted console output
         */
        class ConsoleReport {
        public:
            /**
             * Initialize console reporting system
             * @param useColors Enable ANSI color codes
             * @param showProgress Show progress bar
             * @param verbose Enable verbose output
             */
            ConsoleReport(bool useColors = true, bool showProgress = true, bool verbose = false);
            
            ~ConsoleReport();
            
            /**
             * Start a test run session
             * @param totalTests Total number of tests to run
             */
            void StartTestRun(size_t totalTests);
            
            /**
             * Report a single test result
             * @param testName Name of the test (e.g., "ClassName::TestName")
             * @param passed Whether the test passed
             * @param passedAsserts Number of passed assertions
             * @param totalAsserts Total number of assertions
             * @param durationMs Test execution time in milliseconds
             * @param failureMessages Optional vector of failure messages
             */
            void ReportTestResult(
                const std::string& testName,
                bool passed,
                size_t passedAsserts = 1,
                size_t totalAsserts = 1,
                double durationMs = 0.0,
                const std::vector<std::string>& failureMessages = {}
            );
            
            /**
             * Report test skipped
             * @param testName Name of the skipped test
             * @param reason Reason for skipping
             */
            void ReportTestSkipped(
                const std::string& testName,
                const std::string& reason = ""
            );
            
            /**
             * Complete the test run and display summary
             * @param passedTests Number of passed tests
             * @param failedTests Number of failed tests
             * @param skippedTests Number of skipped tests
             * @param passedAsserts Total passed assertions
             * @param failedAsserts Total failed assertions
             * @param totalDurationMs Total execution time
             */
            void CompleteTestRun(
                size_t passedTests,
                size_t failedTests,
                size_t skippedTests,
                size_t passedAsserts,
                size_t failedAsserts,
                double totalDurationMs
            );
            
            /**
             * Set verbosity level
             */
            void SetVerbose(bool verbose);
            
            /**
             * Set color support
             */
            void SetUseColors(bool useColors);
            
            /**
             * Set progress bar display
             */
            void SetShowProgress(bool showProgress);
            
            /**
             * Set source link display
             */
            void SetShowSourceLinks(bool showSourceLinks);
            
            /**
             * Set show all assertions detail (even on pass)
             */
            void SetShowAllAssertions(bool showAll);
            
        private:
            std::unique_ptr<ConsoleReporter> mReporter;
            std::vector<UnitTestDataEntry> mTestResults;
            size_t mCurrentTest = 0;
            size_t mTotalTests = 0;
            
            void ConvertToUnitTestEntry(
                const std::string& testName,
                bool passed,
                size_t passedAsserts,
                size_t totalAsserts,
                double durationMs,
                const std::vector<std::string>& failureMessages,
                bool skipped = false
            );
        };
    }
}
