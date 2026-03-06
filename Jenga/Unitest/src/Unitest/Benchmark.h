// Benchmark.h
#pragma once
#include <chrono>
#include <vector>
#include <string>
#include <functional>
#include <map>
#include <algorithm>
#include <numeric>
#include <cmath>
#include <random>

namespace nkentseu {
    namespace benchmark {

        struct BenchmarkOptions {
            size_t mIterations;
            size_t mWarmup;
            size_t mOperationsPerIteration;
            bool mStableMode;
            bool mEnableOutlierFilter;
            double mOutlierIqrMultiplier;

            BenchmarkOptions()
                : mIterations(1000),
                  mWarmup(100),
                  mOperationsPerIteration(1),
                  mStableMode(false),
                  mEnableOutlierFilter(false),
                  mOutlierIqrMultiplier(1.5) {}
        };
        
        struct BenchmarkResult {
            std::string mName;
            double mMinTimeMs;
            double mMaxTimeMs;
            double mMeanTimeMs;
            double mMedianTimeMs;
            double mP95TimeMs;
            double mP99TimeMs;
            double mStdDevMs;
            double mCvPercent;
            size_t mIterations;
            size_t mEffectiveSamples;
            size_t mOperationsPerIteration;
            size_t mOutliersRemoved;
            bool mOutlierFilteringApplied;
            std::string mMode;
            std::vector<double> mSamples;
            
            BenchmarkResult();
        };
        
        class BenchmarkRunner {
            public:
                static BenchmarkResult Run(const std::string& name,
                                        std::function<void()> function,
                                        size_t iterations = 1000,
                                        size_t warmup = 100,
                                        size_t operationsPerIteration = 1);
                
                static BenchmarkResult RunWithSetup(const std::string& name,
                                                std::function<void()> setup,
                                                std::function<void()> function,
                                                std::function<void()> teardown,
                                                size_t iterations = 1000,
                                                size_t warmup = 100);

                static BenchmarkResult RunWithOptions(const std::string& name,
                                                    std::function<void()> function,
                                                    const BenchmarkOptions& options);

                static BenchmarkResult RunWithSetupOptions(const std::string& name,
                                                        std::function<void()> setup,
                                                        std::function<void()> function,
                                                        std::function<void()> teardown,
                                                        const BenchmarkOptions& options);
                
                template<typename Func>
                static BenchmarkResult Run(const std::string& name, Func func, size_t iterations = 1000) {
                    return Run(name, std::function<void()>(func), iterations);
                }

                template<typename Func>
                static BenchmarkResult RunWithOptions(const std::string& name, Func func, const BenchmarkOptions& options) {
                    return RunWithOptions(name, std::function<void()>(func), options);
                }
                
            private:
                static BenchmarkOptions ResolveOptions(const BenchmarkOptions& options);
                static size_t ResolveEnvSizeT(const char* name, size_t defaultValue);
                static bool ResolveEnvBool(const char* name, bool defaultValue);
                static double ResolveEnvDouble(const char* name, double defaultValue);
                static double Percentile(const std::vector<double>& sorted, double percentile);
                static void ApplyOutlierFilter(BenchmarkResult& result, double iqrMultiplier);
                static void CalculateStatistics(BenchmarkResult& result);
        };
        
        // Comparateur de benchmarks
        class BenchmarkComparator {
            public:
                struct ComparisonResult {
                    std::string mBenchmarkA;
                    std::string mBenchmarkB;
                    double mSpeedup;  // >1 si A plus rapide, <1 si B plus rapide
                    double mConfidence; // 0-1
                    bool mSignificant; // Différence statistiquement significative
                    
                    ComparisonResult();
                };
                
                static ComparisonResult Compare(const BenchmarkResult& a, const BenchmarkResult& b);
                
            private:
                static double CalculateOverlap(const std::vector<double>& a, const std::vector<double>& b);
        };
    }
}
