// PerformanceReporter.h
#pragma once
#include "IPerformanceReporter.h"
#include "Benchmark.h"
#include "Profiler.h"
#include <vector>
#include <map>
#include <fstream>
#include <iomanip>

namespace nkentseu {
    namespace test {
        class PerformanceReporter : public IPerformanceReporter {
            public:
                struct PerformanceTestEntry {
                    std::string mTestName;
                    benchmark::BenchmarkResult mBenchmarkResult;
                    std::vector<profiler::ProfileStatistics> mProfileData;
                    bool mPerformanceRegression;
                    double mRegressionPercentage;
                    
                    PerformanceTestEntry()
                        : mPerformanceRegression(false), mRegressionPercentage(0.0) {}
                };
                
                PerformanceReporter() = default;
                ~PerformanceReporter() = default;
                
                void OnBenchmarkComplete(const benchmark::BenchmarkResult& result) override;
                void OnProfileComplete(const std::vector<profiler::ProfileStatistics>& stats) override;
                void GeneratePerformanceReport(const std::string& filename) override;
                
                void SetBaseline(const std::string& testName, const benchmark::BenchmarkResult& baseline);
                bool HasRegression(const benchmark::BenchmarkResult& current) const;
                
                const std::vector<PerformanceTestEntry>& GetPerformanceData() const { 
                    return mPerformanceData; 
                }
                
            private:
                std::vector<PerformanceTestEntry> mPerformanceData;
                std::map<std::string, benchmark::BenchmarkResult> mBaselineData;
                std::string mCurrentTestName;
        };
    }
}