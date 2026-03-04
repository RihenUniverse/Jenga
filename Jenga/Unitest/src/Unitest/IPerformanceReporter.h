// IPerformanceReporter.h
#pragma once
#include <string>
#include <vector>
#include "Benchmark.h"
#include "Profiler.h"

namespace nkentseu {
    namespace test {
        class IPerformanceReporter {
        public:
            virtual ~IPerformanceReporter() = default;
            
            virtual void OnBenchmarkComplete(const benchmark::BenchmarkResult& result) = 0;
            virtual void OnProfileComplete(const std::vector<profiler::ProfileStatistics>& stats) = 0;
            virtual void GeneratePerformanceReport(const std::string& filename) = 0;
        };
    }
}