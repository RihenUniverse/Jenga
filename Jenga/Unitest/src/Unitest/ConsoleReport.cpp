#include "ConsoleReport.h"
#include <algorithm>
#include <chrono>
#include <cmath>

namespace nkentseu {
    namespace test {
        ConsoleReport::ConsoleReport(bool useColors, bool showProgress, bool verbose)
            : mCurrentTest(0), mTotalTests(0) {
            mReporter = std::make_unique<ConsoleReporter>(useColors, showProgress, verbose);
        }
        
        ConsoleReport::~ConsoleReport() = default;
        
        void ConsoleReport::StartTestRun(size_t totalTests) {
            mTotalTests = totalTests;
            mCurrentTest = 0;
            mTestResults.clear();
            mReporter->OnTestRunStart(totalTests);
        }
        
        void ConsoleReport::ReportTestResult(
            const std::string& testName,
            bool passed,
            size_t passedAsserts,
            size_t totalAsserts,
            double durationMs,
            const std::vector<std::string>& failureMessages) {
            
            ConvertToUnitTestEntry(testName, passed, passedAsserts, totalAsserts, 
                                  durationMs, failureMessages, false);
        }
        
        void ConsoleReport::ReportTestSkipped(
            const std::string& testName,
            const std::string& reason) {
            
            std::vector<std::string> messages;
            if (!reason.empty()) {
                messages.push_back(reason);
            }
            ConvertToUnitTestEntry(testName, true, 0, 0, 0.0, messages, true);
        }
        
        void ConsoleReport::CompleteTestRun(
            size_t passedTests,
            size_t failedTests,
            size_t skippedTests,
            size_t passedAsserts,
            size_t failedAsserts,
            double totalDurationMs) {
            
            // Build statistics struct
            TestRunStatistics stats;
            stats.mTotalTestCases = passedTests + failedTests + skippedTests;
            stats.mPassedTestCases = passedTests;
            stats.mFailedTestCases = failedTests;
            stats.mSkippedTestCases = skippedTests;
            stats.mTotalAssertions = passedAsserts + failedAsserts;
            stats.mPassedAssertions = passedAsserts;
            stats.mFailedAssertions = failedAsserts;
            stats.mTotalExecutionTimeMs = totalDurationMs;
            
            if (stats.mTotalTestCases > skippedTests && stats.mTotalTestCases > 0) {
                stats.mAverageTestTimeMs = totalDurationMs / (stats.mTotalTestCases - skippedTests);
            } else {
                stats.mAverageTestTimeMs = 0.0;
            }
            
            if (stats.mTotalAssertions > 0) {
                stats.mAverageAssertTimeMs = totalDurationMs / stats.mTotalAssertions;
            } else {
                stats.mAverageAssertTimeMs = 0.0;
            }
            
            mReporter->OnTestRunComplete(stats);
        }
        
        void ConsoleReport::SetVerbose(bool verbose) {
            // Configuration will be applied at next report
            // Stored in initialization
        }
        
        void ConsoleReport::SetUseColors(bool useColors) {
            // Configuration will be applied at next report
            // Stored in initialization
        }
        
        void ConsoleReport::SetShowProgress(bool showProgress) {
            // Configuration will be applied at next report
            // Stored in initialization
        }
        
        void ConsoleReport::SetShowSourceLinks(bool showSourceLinks) {
            // Configuration will be applied at next report
            // Stored in initialization
        }
        
        void ConsoleReport::SetShowAllAssertions(bool showAll) {
            // Configuration will be applied at next report
            // Stored in initialization
        }
        
        void ConsoleReport::ConvertToUnitTestEntry(
            const std::string& testName,
            bool passed,
            size_t passedAsserts,
            size_t totalAsserts,
            double durationMs,
            const std::vector<std::string>& failureMessages,
            bool skipped) {
            
            UnitTestDataEntry entry;
            entry.mTestName = testName;
            entry.mSuccess = passed;
            entry.mSkipped = skipped;
            entry.mPassedAsserts = passedAsserts;
            entry.mTotalAsserts = totalAsserts;
            entry.mTotalDurationMs = durationMs;
            
            if (totalAsserts > 0 && durationMs > 0.0) {
                entry.mAverageAssertDurationMs = durationMs / totalAsserts;
            } else {
                entry.mAverageAssertDurationMs = 0.0;
            }
            
            entry.mFailedAssertMessages = failureMessages;
            
            // Generate passed assertions expressions (simplified)
            if (passed && totalAsserts > 0) {
                for (size_t i = 0; i < passedAsserts; ++i) {
                    entry.mPassedAssertExpressions.push_back("Assertion " + std::to_string(i + 1));
                }
            }
            
            mTestResults.push_back(entry);
            mCurrentTest++;
            
            mReporter->OnTestCaseComplete(entry);
        }
    }
}
