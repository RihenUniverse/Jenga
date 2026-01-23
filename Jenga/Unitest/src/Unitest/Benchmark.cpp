// Benchmark.cpp
#include "Benchmark.h"

namespace nkentseu {
    namespace benchmark {
        
        BenchmarkResult::BenchmarkResult() 
            : mMinTimeMs(0.0), mMaxTimeMs(0.0), mMeanTimeMs(0.0),
              mMedianTimeMs(0.0), mStdDevMs(0.0), mIterations(0),
              mOperationsPerIteration(1) {}
        
        BenchmarkResult BenchmarkRunner::Run(const std::string& name,
                                           std::function<void()> function,
                                           size_t iterations,
                                           size_t warmup,
                                           size_t operationsPerIteration) {
            
            BenchmarkResult result;
            result.mName = name;
            result.mIterations = iterations;
            result.mOperationsPerIteration = operationsPerIteration;
            result.mSamples.reserve(iterations);
            
            // Phase de warmup
            for (size_t i = 0; i < warmup; ++i) {
                function();
            }
            
            // Mesures réelles
            for (size_t i = 0; i < iterations; ++i) {
                auto start = std::chrono::high_resolution_clock::now();
                
                // Exécuter la fonction operationsPerIteration fois
                for (size_t op = 0; op < operationsPerIteration; ++op) {
                    function();
                }
                
                auto end = std::chrono::high_resolution_clock::now();
                double duration = std::chrono::duration<double, std::milli>(
                    end - start).count() / operationsPerIteration;
                
                result.mSamples.push_back(duration);
            }
            
            // Calcul des statistiques
            CalculateStatistics(result);
            
            return result;
        }
        
        BenchmarkResult BenchmarkRunner::RunWithSetup(const std::string& name,
                                                    std::function<void()> setup,
                                                    std::function<void()> function,
                                                    std::function<void()> teardown,
                                                    size_t iterations,
                                                    size_t warmup) {
            
            BenchmarkResult result;
            result.mName = name;
            result.mIterations = iterations;
            result.mSamples.reserve(iterations);
            
            // Phase de warmup
            for (size_t i = 0; i < warmup; ++i) {
                setup();
                function();
                teardown();
            }
            
            // Mesures réelles
            for (size_t i = 0; i < iterations; ++i) {
                setup();
                
                auto start = std::chrono::high_resolution_clock::now();
                function();
                auto end = std::chrono::high_resolution_clock::now();
                
                teardown();
                
                double duration = std::chrono::duration<double, std::milli>(
                    end - start).count();
                
                result.mSamples.push_back(duration);
            }
            
            // Calcul des statistiques
            CalculateStatistics(result);
            
            return result;
        }
        
        void BenchmarkRunner::CalculateStatistics(BenchmarkResult& result) {
            if (result.mSamples.empty()) return;
            
            // Tri pour le médian
            std::vector<double> sorted = result.mSamples;
            std::sort(sorted.begin(), sorted.end());
            
            // Min/Max
            result.mMinTimeMs = sorted.front();
            result.mMaxTimeMs = sorted.back();
            
            // Moyenne
            double sum = std::accumulate(sorted.begin(), sorted.end(), 0.0);
            result.mMeanTimeMs = sum / sorted.size();
            
            // Médiane
            size_t size = sorted.size();
            if (size % 2 == 0) {
                result.mMedianTimeMs = (sorted[size/2 - 1] + sorted[size/2]) / 2.0;
            } else {
                result.mMedianTimeMs = sorted[size/2];
            }
            
            // Écart-type
            double sq_sum = std::inner_product(sorted.begin(), sorted.end(), 
                                            sorted.begin(), 0.0);
            result.mStdDevMs = std::sqrt(sq_sum / sorted.size() - 
                                    result.mMeanTimeMs * result.mMeanTimeMs);
        }
        
        BenchmarkComparator::ComparisonResult::ComparisonResult() : mSpeedup(1.0), mConfidence(0.0), mSignificant(false) {}
        
        BenchmarkComparator::ComparisonResult BenchmarkComparator::Compare(const BenchmarkResult& a, const BenchmarkResult& b) {
            ComparisonResult result;
            result.mBenchmarkA = a.mName;
            result.mBenchmarkB = b.mName;
            
            // Calcul du speedup
            result.mSpeedup = b.mMeanTimeMs / a.mMeanTimeMs;
            
            // Test t simplifié pour vérifier la significativité
            if (a.mIterations >= 30 && b.mIterations >= 30) {
                double se = std::sqrt(
                    (a.mStdDevMs * a.mStdDevMs / a.mIterations) +
                    (b.mStdDevMs * b.mStdDevMs / b.mIterations)
                );
                
                double t_stat = std::abs(a.mMeanTimeMs - b.mMeanTimeMs) / se;
                
                // Pour un intervalle de confiance à 95% avec grands échantillons
                result.mSignificant = (t_stat > 1.96);
                result.mConfidence = 1.0 - 2.0 * std::erfc(t_stat / std::sqrt(2.0));
            } else {
                // Pour petits échantillons, utiliser une méthode plus simple
                double overlap = CalculateOverlap(a.mSamples, b.mSamples);
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
            double overlap_range = overlap_end - overlap_start;
            
            return (overlap_range / std::min(range_a, range_b));
        }
    }
}