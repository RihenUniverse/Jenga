#pragma once
#include <string>
#include <vector>
#include <memory>
#include <sstream>
#include <iomanip>
#include <chrono>
#include "UnitTestData.h"

namespace nkentseu {
    namespace test {
        class ITestReporter {
        public:
            virtual ~ITestReporter() = default;
            
            virtual void OnTestRunStart(size_t totalTests) = 0;
            virtual void OnTestCaseComplete(const UnitTestDataEntry& result) = 0;
            virtual void OnTestRunComplete(const TestRunStatistics& statistics) = 0;
            virtual std::string GetName() const = 0;
        };
        
        class ConsoleReporter : public ITestReporter {
        public:
            ConsoleReporter();
            explicit ConsoleReporter(bool useColors, bool showProgress = true, bool verbose = true);
            
            void OnTestRunStart(size_t totalTests) override;
            void OnTestCaseComplete(const UnitTestDataEntry& result) override;
            void OnTestRunComplete(const TestRunStatistics& statistics) override;
            std::string GetName() const override { return "ConsoleReporter"; }
            
            void SetUseColors(bool useColors) { mUseColors = useColors; }
            void SetShowProgress(bool showProgress) { mShowProgress = showProgress; }
            void SetVerbose(bool verbose) { mVerbose = verbose; }
            void SetShowAllAssertions(bool showAll) { mShowAllAssertions = showAll; }
            void SetShowSourceLinks(bool showLinks) { mShowSourceLinks = showLinks; }
            
        private:
            void PrintHeader();
            void PrintTestResult(const UnitTestDataEntry& result);
            void PrintSummary(const TestRunStatistics& statistics);
            void PrintProgressBar(size_t current, size_t total);
            void PrintFailureDetails(const UnitTestDataEntry& result, size_t index);
            void PrintSuccessDetails(const UnitTestDataEntry& result);
            
            std::string FormatClickableLink(const std::string& filePath, int lineNumber) const;
            std::string FormatIDELink(const std::string& filePath, int lineNumber) const;
            std::string FormatFileLink(const std::string& filePath, int lineNumber) const;
            std::string DetectIDE() const;
            
            std::string Colorize(const std::string& text, const std::string& colorCode) const;
            std::string GetTestStatusColor(bool success) const;
            std::string GetPercentageColor(double percentage) const;
            std::string GetSeverityColor(size_t failedCount) const;
            
            std::string FormatDuration(double ms) const;
            std::string FormatPercentage(size_t numerator, size_t denominator) const;
            std::string FormatCount(size_t count) const;
            std::string FormatTestName(const std::string& name) const;
            
            bool ExtractLocation(const std::string& message, 
                               std::string& filePath, int& lineNumber) const;
            void PrintLocationInfo(const std::string& filePath, int lineNumber) const;

            void PrintLiveTestResult(const UnitTestDataEntry& result);
            void PrintConciseFailureDetails(const UnitTestDataEntry& result);
            void PrintVerboseSuccessDetails(const UnitTestDataEntry& result);
            void UpdateProgressBar();
            void PrintCleanSummary(const TestRunStatistics& statistics);
            std::string FormatClickableLink(const std::string& location) const;
            void PrintUnitTestBanner();
            
            bool mUseColors;
            bool mShowProgress;
            bool mVerbose;
            bool mShowAllAssertions;
            bool mShowSourceLinks;
            size_t mCurrentTest;
            size_t mTotalTests;
            size_t mTotalWidth;
            std::chrono::steady_clock::time_point mStartTime;
        };
    }
}
