// Benchmark.cpp
#include "Benchmark.h"
#include <cstdlib>
#include <limits>

namespace nkentseu {
    namespace benchmark {

        namespace {
            using NkBenchClock = std::chrono::steady_clock;

            double Clamp01(double value) {
                if (value < 0.0) return 0.0;
                if (value > 1.0) return 1.0;
                return value;
            }

            bool IsTrueValue(const std::string& value) {
                return value == "1" || value == "true" || value == "TRUE" ||
                       value == "yes" || value == "YES" || value == "on" || value == "ON";
            }

            bool IsFalseValue(const std::string& value) {
                return value == "0" || value == "false" || value == "FALSE" ||
                       value == "no" || value == "NO" || value == "off" || value == "OFF";
            }
        }
        
        BenchmarkResult::BenchmarkResult() 
            : mMinTimeMs(0.0), mMaxTimeMs(0.0), mMeanTimeMs(0.0),
              mMedianTimeMs(0.0), mP95TimeMs(0.0), mP99TimeMs(0.0),
              mStdDevMs(0.0), mCvPercent(0.0), mIterations(0),
              mEffectiveSamples(0), mOperationsPerIteration(1),
              mOutliersRemoved(0), mOutlierFilteringApplied(false),
              mMode("default") {}
        
        BenchmarkResult BenchmarkRunner::Run(const std::string& name,
                                           std::function<void()> function,
                                           size_t iterations,
                                           size_t warmup,
                                           size_t operationsPerIteration) {
            BenchmarkOptions options;
            options.mIterations = iterations;
            options.mWarmup = warmup;
            options.mOperationsPerIteration = operationsPerIteration;
            return RunWithOptions(name, function, options);
        }
        
        BenchmarkResult BenchmarkRunner::RunWithSetup(const std::string& name,
                                                    std::function<void()> setup,
                                                    std::function<void()> function,
                                                    std::function<void()> teardown,
                                                    size_t iterations,
                                                    size_t warmup) {
            BenchmarkOptions options;
            options.mIterations = iterations;
            options.mWarmup = warmup;
            options.mOperationsPerIteration = 1;
            return RunWithSetupOptions(name, setup, function, teardown, options);
        }

        BenchmarkResult BenchmarkRunner::RunWithOptions(const std::string& name,
                                                      std::function<void()> function,
                                                      const BenchmarkOptions& options) {
            const BenchmarkOptions resolved = ResolveOptions(options);

            BenchmarkResult result;
            result.mName = name;
            result.mIterations = resolved.mIterations;
            result.mOperationsPerIteration = resolved.mOperationsPerIteration;
            result.mMode = resolved.mStableMode ? "stable" : "default";
            result.mOutlierFilteringApplied = resolved.mEnableOutlierFilter;
            result.mSamples.reserve(resolved.mIterations);

            for (size_t i = 0; i < resolved.mWarmup; ++i) {
                function();
            }

            for (size_t i = 0; i < resolved.mIterations; ++i) {
                const auto start = NkBenchClock::now();

                for (size_t op = 0; op < resolved.mOperationsPerIteration; ++op) {
                    function();
                }

                const auto end = NkBenchClock::now();
                const double duration = std::chrono::duration<double, std::milli>(end - start).count() /
                                        static_cast<double>(resolved.mOperationsPerIteration);
                result.mSamples.push_back(duration);
            }

            if (resolved.mEnableOutlierFilter) {
                ApplyOutlierFilter(result, resolved.mOutlierIqrMultiplier);
            }

            CalculateStatistics(result);
            return result;
        }

        BenchmarkResult BenchmarkRunner::RunWithSetupOptions(const std::string& name,
                                                           std::function<void()> setup,
                                                           std::function<void()> function,
                                                           std::function<void()> teardown,
                                                           const BenchmarkOptions& options) {
            const BenchmarkOptions resolved = ResolveOptions(options);

            BenchmarkResult result;
            result.mName = name;
            result.mIterations = resolved.mIterations;
            result.mOperationsPerIteration = resolved.mOperationsPerIteration;
            result.mMode = resolved.mStableMode ? "stable" : "default";
            result.mOutlierFilteringApplied = resolved.mEnableOutlierFilter;
            result.mSamples.reserve(resolved.mIterations);

            for (size_t i = 0; i < resolved.mWarmup; ++i) {
                if (setup) {
                    setup();
                }
                for (size_t op = 0; op < resolved.mOperationsPerIteration; ++op) {
                    function();
                }
                if (teardown) {
                    teardown();
                }
            }

            for (size_t i = 0; i < resolved.mIterations; ++i) {
                if (setup) {
                    setup();
                }

                const auto start = NkBenchClock::now();
                for (size_t op = 0; op < resolved.mOperationsPerIteration; ++op) {
                    function();
                }
                const auto end = NkBenchClock::now();

                if (teardown) {
                    teardown();
                }

                const double duration = std::chrono::duration<double, std::milli>(end - start).count() /
                                        static_cast<double>(resolved.mOperationsPerIteration);
                result.mSamples.push_back(duration);
            }

            if (resolved.mEnableOutlierFilter) {
                ApplyOutlierFilter(result, resolved.mOutlierIqrMultiplier);
            }

            CalculateStatistics(result);
            return result;
        }

        BenchmarkOptions BenchmarkRunner::ResolveOptions(const BenchmarkOptions& options) {
            BenchmarkOptions resolved = options;

            resolved.mIterations = ResolveEnvSizeT("UNITEST_BENCH_ITERATIONS", resolved.mIterations);
            resolved.mWarmup = ResolveEnvSizeT("UNITEST_BENCH_WARMUP", resolved.mWarmup);
            resolved.mOperationsPerIteration = ResolveEnvSizeT(
                "UNITEST_BENCH_OPERATIONS_PER_ITERATION", resolved.mOperationsPerIteration);
            resolved.mStableMode = ResolveEnvBool("UNITEST_BENCH_STABLE", resolved.mStableMode);
            resolved.mEnableOutlierFilter = ResolveEnvBool(
                "UNITEST_BENCH_OUTLIER_FILTER", resolved.mEnableOutlierFilter);
            resolved.mOutlierIqrMultiplier = ResolveEnvDouble(
                "UNITEST_BENCH_OUTLIER_IQR_MULTIPLIER", resolved.mOutlierIqrMultiplier);

            if (resolved.mStableMode) {
                if (resolved.mIterations < 2000) {
                    resolved.mIterations = 2000;
                }
                if (resolved.mWarmup < 200) {
                    resolved.mWarmup = 200;
                }
                resolved.mEnableOutlierFilter = true;
            }

            if (resolved.mOperationsPerIteration == 0) {
                resolved.mOperationsPerIteration = 1;
            }
            if (resolved.mOutlierIqrMultiplier <= 0.0) {
                resolved.mOutlierIqrMultiplier = 1.5;
            }

            return resolved;
        }

        size_t BenchmarkRunner::ResolveEnvSizeT(const char* name, size_t defaultValue) {
            const char* raw = std::getenv(name);
            if (raw == nullptr || *raw == '\0') {
                return defaultValue;
            }

            char* end = nullptr;
            const unsigned long long value = std::strtoull(raw, &end, 10);
            if (end == raw || (end != nullptr && *end != '\0')) {
                return defaultValue;
            }

            return static_cast<size_t>(value);
        }

        bool BenchmarkRunner::ResolveEnvBool(const char* name, bool defaultValue) {
            const char* raw = std::getenv(name);
            if (raw == nullptr || *raw == '\0') {
                return defaultValue;
            }

            const std::string value(raw);
            if (IsTrueValue(value)) {
                return true;
            }
            if (IsFalseValue(value)) {
                return false;
            }
            return defaultValue;
        }

        double BenchmarkRunner::ResolveEnvDouble(const char* name, double defaultValue) {
            const char* raw = std::getenv(name);
            if (raw == nullptr || *raw == '\0') {
                return defaultValue;
            }

            char* end = nullptr;
            const double value = std::strtod(raw, &end);
            if (end == raw || (end != nullptr && *end != '\0')) {
                return defaultValue;
            }

            return value;
        }

        double BenchmarkRunner::Percentile(const std::vector<double>& sorted, double percentile) {
            if (sorted.empty()) {
                return 0.0;
            }
            if (percentile <= 0.0) {
                return sorted.front();
            }
            if (percentile >= 100.0) {
                return sorted.back();
            }

            const double position = (percentile / 100.0) * static_cast<double>(sorted.size() - 1);
            const size_t lowerIndex = static_cast<size_t>(position);
            const size_t upperIndex = std::min(lowerIndex + 1, sorted.size() - 1);
            const double weight = position - static_cast<double>(lowerIndex);
            return sorted[lowerIndex] * (1.0 - weight) + sorted[upperIndex] * weight;
        }

        void BenchmarkRunner::ApplyOutlierFilter(BenchmarkResult& result, double iqrMultiplier) {
            if (result.mSamples.size() < 4) {
                return;
            }

            std::vector<double> sorted = result.mSamples;
            std::sort(sorted.begin(), sorted.end());

            const double q1 = Percentile(sorted, 25.0);
            const double q3 = Percentile(sorted, 75.0);
            const double iqr = q3 - q1;

            if (iqr <= std::numeric_limits<double>::epsilon()) {
                return;
            }

            const double lowerBound = q1 - (iqrMultiplier * iqr);
            const double upperBound = q3 + (iqrMultiplier * iqr);

            std::vector<double> filtered;
            filtered.reserve(result.mSamples.size());

            for (double sample : result.mSamples) {
                if (sample >= lowerBound && sample <= upperBound) {
                    filtered.push_back(sample);
                }
            }

            if (filtered.empty()) {
                return;
            }

            result.mOutliersRemoved = result.mSamples.size() - filtered.size();
            result.mSamples.swap(filtered);
        }
        
        void BenchmarkRunner::CalculateStatistics(BenchmarkResult& result) {
            if (result.mSamples.empty()) {
                result.mEffectiveSamples = 0;
                return;
            }
            
            std::vector<double> sorted = result.mSamples;
            std::sort(sorted.begin(), sorted.end());
            result.mEffectiveSamples = sorted.size();
            
            result.mMinTimeMs = sorted.front();
            result.mMaxTimeMs = sorted.back();
            
            double sum = std::accumulate(sorted.begin(), sorted.end(), 0.0);
            result.mMeanTimeMs = sum / sorted.size();
            
            size_t size = sorted.size();
            if (size % 2 == 0) {
                result.mMedianTimeMs = (sorted[size/2 - 1] + sorted[size/2]) / 2.0;
            } else {
                result.mMedianTimeMs = sorted[size/2];
            }

            result.mP95TimeMs = Percentile(sorted, 95.0);
            result.mP99TimeMs = Percentile(sorted, 99.0);
            
            double sq_sum = std::inner_product(sorted.begin(), sorted.end(), 
                                            sorted.begin(), 0.0);
            double variance = sq_sum / sorted.size() - result.mMeanTimeMs * result.mMeanTimeMs;
            if (variance < 0.0) {
                variance = 0.0;
            }
            result.mStdDevMs = std::sqrt(variance);
            if (std::abs(result.mMeanTimeMs) <= std::numeric_limits<double>::epsilon()) {
                result.mCvPercent = 0.0;
            } else {
                result.mCvPercent = (result.mStdDevMs / std::abs(result.mMeanTimeMs)) * 100.0;
            }
        }
        
        BenchmarkComparator::ComparisonResult::ComparisonResult() : mSpeedup(1.0), mConfidence(0.0), mSignificant(false) {}
        
        BenchmarkComparator::ComparisonResult BenchmarkComparator::Compare(const BenchmarkResult& a, const BenchmarkResult& b) {
            ComparisonResult result;
            result.mBenchmarkA = a.mName;
            result.mBenchmarkB = b.mName;
            
            if (a.mMeanTimeMs <= std::numeric_limits<double>::epsilon()) {
                result.mSpeedup = 1.0;
            } else {
                result.mSpeedup = b.mMeanTimeMs / a.mMeanTimeMs;
            }
            
            const size_t samplesA = a.mSamples.empty() ? a.mIterations : a.mSamples.size();
            const size_t samplesB = b.mSamples.empty() ? b.mIterations : b.mSamples.size();

            if (samplesA >= 30 && samplesB >= 30) {
                double se = std::sqrt(
                    (a.mStdDevMs * a.mStdDevMs / static_cast<double>(samplesA)) +
                    (b.mStdDevMs * b.mStdDevMs / static_cast<double>(samplesB))
                );

                if (se <= std::numeric_limits<double>::epsilon()) {
                    result.mSignificant = std::abs(a.mMeanTimeMs - b.mMeanTimeMs) >
                                          std::numeric_limits<double>::epsilon();
                    result.mConfidence = result.mSignificant ? 1.0 : 0.0;
                } else {
                    const double tStat = std::abs(a.mMeanTimeMs - b.mMeanTimeMs) / se;
                    result.mSignificant = (tStat > 1.96);
                    result.mConfidence = Clamp01(1.0 - std::erfc(tStat / std::sqrt(2.0)));
                }
            } else {
                const double overlap = Clamp01(CalculateOverlap(a.mSamples, b.mSamples));
                result.mSignificant = (overlap < 0.1); // Moins de 10% de chevauchement
                result.mConfidence = 1.0 - overlap;
            }
            
            return result;
        }
        
        double BenchmarkComparator::CalculateOverlap(const std::vector<double>& a, const std::vector<double>& b) {
            if (a.empty() || b.empty()) return 1.0;
            
            double min_a = *std::min_element(a.begin(), a.end());
            double max_a = *std::max_element(a.begin(), a.end());
            double min_b = *std::min_element(b.begin(), b.end());
            double max_b = *std::max_element(b.begin(), b.end());
            
            double overlap_start = std::max(min_a, min_b);
            double overlap_end = std::min(max_a, max_b);
            
            if (overlap_start >= overlap_end) return 0.0;
            
            double range_a = max_a - min_a;
            double range_b = max_b - min_b;
            double minRange = std::min(range_a, range_b);
            if (minRange <= std::numeric_limits<double>::epsilon()) {
                return (std::abs(min_a - min_b) <= std::numeric_limits<double>::epsilon()) ? 1.0 : 0.0;
            }
            double overlap_range = overlap_end - overlap_start;
            
            return (overlap_range / minRange);
        }
    }
}
