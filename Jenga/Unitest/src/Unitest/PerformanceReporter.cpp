// PerformanceReporter.cpp
#include "PerformanceReporter.h"
#include <sstream>
#include <algorithm>
#include <cmath>

namespace nkentseu {
    namespace test {
        void PerformanceReporter::OnBenchmarkComplete(const benchmark::BenchmarkResult& result) {
            PerformanceTestEntry entry;
            entry.mTestName = result.mName;
            entry.mBenchmarkResult = result;
            
            // Vérifier les régressions si une baseline existe
            auto it = mBaselineData.find(result.mName);
            if (it != mBaselineData.end()) {
                auto comparison = benchmark::BenchmarkComparator::Compare(result, it->second);
                entry.mPerformanceRegression = (comparison.mSpeedup > 1.1); // 10% plus lent
                entry.mRegressionPercentage = (comparison.mSpeedup - 1.0) * 100.0;
            }
            
            mPerformanceData.push_back(entry);
            mCurrentTestName = result.mName;
        }
        
        void PerformanceReporter::OnProfileComplete(const std::vector<profiler::ProfileStatistics>& stats) {
            if (!mCurrentTestName.empty()) {
                for (auto& entry : mPerformanceData) {
                    if (entry.mTestName == mCurrentTestName) {
                        entry.mProfileData = stats;
                        break;
                    }
                }
            }
        }
        
        void PerformanceReporter::GeneratePerformanceReport(const std::string& filename) {
            std::ofstream file(filename);
            if (!file.is_open()) {
                return;
            }
            
            // Générer un rapport JSON
            file << "{\n";
            file << "  \"performance_report\": {\n";
            file << "    \"benchmarks\": [\n";
            
            for (size_t i = 0; i < mPerformanceData.size(); ++i) {
                const auto& entry = mPerformanceData[i];
                file << "      {\n";
                file << "        \"name\": \"" << entry.mTestName << "\",\n";
                file << "        \"mean_time_ms\": " << entry.mBenchmarkResult.mMeanTimeMs << ",\n";
                file << "        \"min_time_ms\": " << entry.mBenchmarkResult.mMinTimeMs << ",\n";
                file << "        \"max_time_ms\": " << entry.mBenchmarkResult.mMaxTimeMs << ",\n";
                file << "        \"std_dev_ms\": " << entry.mBenchmarkResult.mStdDevMs << ",\n";
                file << "        \"iterations\": " << entry.mBenchmarkResult.mIterations << ",\n";
                file << "        \"performance_regression\": " 
                     << (entry.mPerformanceRegression ? "true" : "false") << ",\n";
                file << "        \"regression_percentage\": " << entry.mRegressionPercentage << "\n";
                file << "      }";
                
                if (i < mPerformanceData.size() - 1) {
                    file << ",";
                }
                file << "\n";
            }
            
            file << "    ]\n";
            file << "  }\n";
            file << "}\n";
            
            file.close();
        }
        
        void PerformanceReporter::SetBaseline(const std::string& testName, 
                                            const benchmark::BenchmarkResult& baseline) {
            mBaselineData[testName] = baseline;
        }
        
        bool PerformanceReporter::HasRegression(const benchmark::BenchmarkResult& current) const {
            auto it = mBaselineData.find(current.mName);
            if (it == mBaselineData.end()) {
                return false;
            }
            
            auto comparison = benchmark::BenchmarkComparator::Compare(current, it->second);
            return (comparison.mSpeedup > 1.1); // 10% plus lent
        }
    }
}