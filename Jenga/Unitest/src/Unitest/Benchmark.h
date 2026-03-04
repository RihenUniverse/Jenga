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
        
        struct BenchmarkResult {
            std::string mName;
            double mMinTimeMs;
            double mMaxTimeMs;
            double mMeanTimeMs;
            double mMedianTimeMs;
            double mStdDevMs;
            size_t mIterations;
            size_t mOperationsPerIteration;
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
                
                template<typename Func>
                static BenchmarkResult Run(const std::string& name, Func func, size_t iterations = 1000) {
                    return Run(name, std::function<void()>(func), iterations);
                }
                
            private:
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