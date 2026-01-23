#pragma once
#include <vector>
#include <memory>
#include <functional>
#include <string>
#include <map>
#include <chrono>
#include <mutex>
#include <atomic>
#include "UnitTestData.h"
#include "Benchmark.h"
#include "Profiler.h"
#include "IPerformanceReporter.h"
#include "TestConfiguration.h"
#include "PerformanceReporter.h"

namespace nkentseu {
    namespace test {
        class TestCase;
        class ITestReporter;
        
        class TestRunner {
            public:
                static TestRunner& GetInstance();
                
                TestRunner(const TestRunner&) = delete;
                TestRunner& operator=(const TestRunner&) = delete;
                
                void Configure(const TestConfiguration& config);
                const TestConfiguration& GetConfiguration() const { return mConfig; }
                
                void AddTestCase(const std::string& name, 
                            std::function<std::unique_ptr<TestCase>()> factory);
                
                bool RunAllTests();
                bool RunTests(const std::vector<std::string>& testNames);
                
                void AddReporter(std::shared_ptr<ITestReporter> reporter);
                void RemoveAllReporters();
                void SetDefaultReporters();
                
                const std::vector<UnitTestDataEntry>& GetResults() const { return mResults; }
                const TestRunStatistics& GetStatistics() const { return mStatistics; }
                
                size_t GetTotalTests() const { return mStatistics.mTotalTestCases; }
                size_t GetPassedTests() const { return mStatistics.mPassedTestCases; }
                size_t GetFailedTests() const { return mStatistics.mFailedTestCases; }
                size_t GetSkippedTests() const { return mStatistics.mSkippedTestCases; }
                size_t GetTotalAsserts() const { return mStatistics.mTotalAssertions; }
                size_t GetPassedAsserts() const { return mStatistics.mPassedAssertions; }
                size_t GetFailedAsserts() const { return mStatistics.mFailedAssertions; }
                double GetTotalDurationMs() const { return mStatistics.mTotalExecutionTimeMs; }
                
                void SetTestTimeout(double timeoutMs) { mTestTimeoutMs = timeoutMs; }
                double GetTestTimeout() const { return mTestTimeoutMs; }
                
                void Reset();

                void EnablePerformanceTracking(bool enable = true);
                std::shared_ptr<PerformanceReporter> GetPerformanceReporter() const;
                
            private:
                TestRunner();
                ~TestRunner() = default;
                
                bool ShouldRunTest(const std::string& testName) const;
                UnitTestDataEntry RunSingleTest(const std::string& name, 
                                            std::function<std::unique_ptr<TestCase>()>& factory);
                
                void UpdateStatistics(const UnitTestDataEntry& result);
                void CalculateAverages();
                
                std::map<std::string, std::function<std::unique_ptr<TestCase>()>> mTestFactories;
                std::vector<std::shared_ptr<ITestReporter>> mReporters;
                std::vector<UnitTestDataEntry> mResults;
                TestConfiguration mConfig;
                TestRunStatistics mStatistics;
                double mTestTimeoutMs;
                std::mutex mMutex;
                std::atomic<size_t> mCompletedTests;

                bool mTrackPerformance;
                std::shared_ptr<PerformanceReporter> mPerformanceReporter;
        };

        // TestRunner.h (ajouts)
        struct PerformanceTestEntry {
            std::string mTestName;
            benchmark::BenchmarkResult mBenchmarkResult;
            std::vector<profiler::ProfileStatistics> mProfileData;
            bool mPerformanceRegression;
            double mRegressionPercentage;
            
            PerformanceTestEntry()
                : mPerformanceRegression(false), mRegressionPercentage(0.0) {}
        };
        
        int RunUnitTests(int argc = 0, char** argv = nullptr);
        int RunUnitTests(const TestConfiguration& config);
        
    }
}