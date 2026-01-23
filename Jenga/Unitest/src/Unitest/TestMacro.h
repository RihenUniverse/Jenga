#pragma once

#include <chrono>
#include <sstream>
#include <iomanip>
#include <string>

// Macros pour créer des tests
#define TEST_CASE(ClassName, TestName) \
class ClassName##TestName##TestCase : public nkentseu::test::TestCase { \
public: \
    ClassName##TestName##TestCase() : TestCase(#ClassName "_" #TestName) {} \
    void Run() override; \
}; \
static nkentseu::test::detail::TestCaseRegistrar<ClassName##TestName##TestCase> \
    gRegistrar_##ClassName##_##TestName##TestCase(#ClassName "_" #TestName); \
void ClassName##TestName##TestCase::Run()

#define TEST(TestName) TEST_CASE(Default, TestName)

#define TEST_FIXTURE(FixtureClass, TestName) \
class TestName##TestCase : public FixtureClass { \
public: \
    TestName##TestCase() : FixtureClass(#TestName) {} \
    void Run() override; \
}; \
static nkentseu::test::detail::TestCaseRegistrar<TestName##TestCase> \
    gRegistrar_##TestName##TestCase(#TestName); \
void TestName##TestCase::Run()

// Macros d'assertion de base
#define ASSERT_EQUAL(expected, actual) \
    nkentseu::test::TestAssert::Equal((expected), (actual), "", __FILE__, __LINE__, #expected " == " #actual)

#define ASSERT_NOT_EQUAL(expected, actual) \
    nkentseu::test::TestAssert::NotEqual((expected), (actual), "", __FILE__, __LINE__, #expected " != " #actual)

#define ASSERT_TRUE(condition) \
    nkentseu::test::TestAssert::True((condition), "", __FILE__, __LINE__, #condition)

#define ASSERT_FALSE(condition) \
    nkentseu::test::TestAssert::False((condition), "", __FILE__, __LINE__, #condition)

// Macros d'assertion avec message
#define ASSERT_EQUAL_MSG(expected, actual, message) \
    nkentseu::test::TestAssert::Equal((expected), (actual), (message), __FILE__, __LINE__, #expected " == " #actual)

#define ASSERT_NOT_EQUAL_MSG(expected, actual, message) \
    nkentseu::test::TestAssert::NotEqual((expected), (actual), (message), __FILE__, __LINE__, #expected " != " #actual)

#define ASSERT_TRUE_MSG(condition, message) \
    nkentseu::test::TestAssert::True((condition), (message), __FILE__, __LINE__, #condition)

#define ASSERT_FALSE_MSG(condition, message) \
    nkentseu::test::TestAssert::False((condition), (message), __FILE__, __LINE__, #condition)

// Macros pour les pointeurs
#define ASSERT_NULL(ptr) \
    nkentseu::test::TestAssert::Null((ptr), "", __FILE__, __LINE__, #ptr " == nullptr")

#define ASSERT_NOT_NULL(ptr) \
    nkentseu::test::TestAssert::NotNull((ptr), "", __FILE__, __LINE__, #ptr " != nullptr")

#define ASSERT_NULL_MSG(ptr, message) \
    nkentseu::test::TestAssert::Null((ptr), (message), __FILE__, __LINE__, #ptr " == nullptr")

#define ASSERT_NOT_NULL_MSG(ptr, message) \
    nkentseu::test::TestAssert::NotNull((ptr), (message), __FILE__, __LINE__, #ptr " != nullptr")

// Macros de comparaison
#define ASSERT_LESS(left, right) \
    nkentseu::test::TestAssert::Less((left), (right), "", __FILE__, __LINE__, #left " < " #right)

#define ASSERT_LESS_EQUAL(left, right) \
    nkentseu::test::TestAssert::LessEqual((left), (right), "", __FILE__, __LINE__, #left " <= " #right)

#define ASSERT_GREATER(left, right) \
    nkentseu::test::TestAssert::Greater((left), (right), "", __FILE__, __LINE__, #left " > " #right)

#define ASSERT_GREATER_EQUAL(left, right) \
    nkentseu::test::TestAssert::GreaterEqual((left), (right), "", __FILE__, __LINE__, #left " >= " #right)

#define ASSERT_LESS_MSG(left, right, message) \
    nkentseu::test::TestAssert::Less((left), (right), (message), __FILE__, __LINE__, #left " < " #right)

#define ASSERT_GREATER_MSG(left, right, message) \
    nkentseu::test::TestAssert::Greater((left), (right), (message), __FILE__, __LINE__, #left " > " #right)

// Macros avec tolérance
#define ASSERT_NEAR(expected, actual, tolerance) \
    nkentseu::test::TestAssert::Near((expected), (actual), (tolerance), "", __FILE__, __LINE__, #actual " ≈ " #expected)

#define ASSERT_EQUAL_TOLERANCE(expected, actual, tolerance) \
    nkentseu::test::TestAssert::EqualWithTolerance((expected), (actual), (tolerance), "", __FILE__, __LINE__, #actual " ≈ " #expected)

#define ASSERT_NEAR_MSG(expected, actual, tolerance, message) \
    nkentseu::test::TestAssert::Near((expected), (actual), (tolerance), (message), __FILE__, __LINE__, #actual " ≈ " #expected)

// Macros d'exception
#define ASSERT_THROWS(exceptionType, expression) \
    nkentseu::test::TestAssert::Throws<exceptionType>([&]() { expression; }, "", __FILE__, __LINE__, #expression " throws " #exceptionType)

#define ASSERT_NO_THROW(expression) \
    nkentseu::test::TestAssert::NoThrow([&]() { expression; }, "", __FILE__, __LINE__, #expression " doesn't throw")

#define ASSERT_THROWS_MSG(exceptionType, expression, message) \
    nkentseu::test::TestAssert::Throws<exceptionType>([&]() { expression; }, (message), __FILE__, __LINE__, #expression " throws " #exceptionType)

#define ASSERT_NO_THROW_MSG(expression, message) \
    nkentseu::test::TestAssert::NoThrow([&]() { expression; }, (message), __FILE__, __LINE__, #expression " doesn't throw")

// Macros de performance (mesure simple)
#define ASSERT_EXECUTION_TIME_LESS_SIMPLE(maxTimeMs, expression) \
    nkentseu::test::TestAssert::ExecutionTimeLess([&]() { expression; }, (maxTimeMs), "", __FILE__, __LINE__, #expression " < " #maxTimeMs "ms")

#define ASSERT_EXECUTION_TIME_LESS_MSG(maxTimeMs, expression, message) \
    nkentseu::test::TestAssert::ExecutionTimeLess([&]() { expression; }, (maxTimeMs), (message), __FILE__, __LINE__, #expression " < " #maxTimeMs "ms")

// Macros de collections
#define ASSERT_CONTAINS(container, value) \
    nkentseu::test::TestAssert::Contains((container), (value), "", __FILE__, __LINE__, #container " contains " #value)

#define ASSERT_NOT_CONTAINS(container, value) \
    nkentseu::test::TestAssert::NotContains((container), (value), "", __FILE__, __LINE__, #container " doesn't contain " #value)

#define ASSERT_CONTAINS_MSG(container, value, message) \
    nkentseu::test::TestAssert::Contains((container), (value), (message), __FILE__, __LINE__, #container " contains " #value)

#define ASSERT_NOT_CONTAINS_MSG(container, value, message) \
    nkentseu::test::TestAssert::NotContains((container), (value), (message), __FILE__, __LINE__, #container " doesn't contain " #value)

// Macro pour arrêter sur échec
#define TEST_STOP_ON_FAILURE() \
    SetStopOnFailure(true)

// Macro pour mesurer le temps (legacy)
#define MEASURE_EXECUTION_TIME(func, iterations) \
    nkentseu::test::TestAssert::MeasureExecutionTime((func), (iterations))

// =====================================================================
// MACROS DE BENCHMARK ET PROFILING
// =====================================================================

// Note: Les classes benchmark::BenchmarkRunner, benchmark::BenchmarkComparator,
//       profiler::Profiler, etc. doivent être définies ailleurs

// Macro pour exécuter un benchmark
#define RUN_BENCHMARK(name, function, iterations) \
    nkentseu::benchmark::BenchmarkRunner::Run(name, function, iterations)

#define RUN_BENCHMARK_WITH_SETUP(name, setup, function, teardown, iterations) \
    nkentseu::benchmark::BenchmarkRunner::RunWithSetup(name, setup, function, teardown, iterations)

// Macro pour benchmark avec warmup personnalisé
#define BENCHMARK_CUSTOM(name, function, iterations, warmup) \
    nkentseu::benchmark::BenchmarkRunner::Run(name, function, iterations, warmup)

// ---------------------------------------------------------------------
// ASSERTIONS DE BENCHMARK
// ---------------------------------------------------------------------

// Version basique avec limite par défaut
#define ASSERT_BENCHMARK_FASTER(benchmarkA, benchmarkB) \
    ASSERT_BENCHMARK_FASTER_WITH_LIMIT(benchmarkA, benchmarkB, 1.1)

// Version avec limite personnalisée
#define ASSERT_BENCHMARK_FASTER_WITH_LIMIT(benchmarkA, benchmarkB, maxAllowedSlowdown) \
    do { \
        auto comparison = nkentseu::benchmark::BenchmarkComparator::Compare( \
            benchmarkA, benchmarkB); \
        if (comparison.mSpeedup > (maxAllowedSlowdown)) { \
            std::ostringstream oss; \
            oss << "Benchmark " << comparison.mBenchmarkA \
                << " is " << std::fixed << std::setprecision(2) \
                << comparison.mSpeedup << "x slower than " \
                << comparison.mBenchmarkB << " (max allowed: " \
                << (maxAllowedSlowdown) << "x)"; \
            nkentseu::test::TestAssert::sCurrentTest->AddFailure( \
                oss.str(), __FILE__, __LINE__, "", 0.0); \
        } \
    } while(0)

// Vérification de régression de performance
#define ASSERT_PERFORMANCE_REGRESSION(baseline, current) \
    ASSERT_PERFORMANCE_REGRESSION_WITH_LIMIT(baseline, current, 1.2)

#define ASSERT_PERFORMANCE_REGRESSION_WITH_LIMIT(baseline, current, maxRegression) \
    ASSERT_BENCHMARK_FASTER_WITH_LIMIT(current, baseline, maxRegression)

// Vérification de significativité statistique
#define ASSERT_BENCHMARK_SIGNIFICANTLY_FASTER(benchmarkA, benchmarkB) \
    do { \
        auto comparison = nkentseu::benchmark::BenchmarkComparator::Compare( \
            benchmarkA, benchmarkB); \
        if (!comparison.mSignificant) { \
            std::ostringstream oss; \
            oss << "Benchmark comparison not statistically significant: " \
                << comparison.mBenchmarkA << " vs " << comparison.mBenchmarkB \
                << " (confidence: " << std::fixed << std::setprecision(2) \
                << comparison.mConfidence * 100.0 << "%)"; \
            nkentseu::test::TestAssert::sCurrentTest->AddFailure( \
                oss.str(), __FILE__, __LINE__, "", 0.0); \
        } \
    } while(0)

// Combinaison : plus rapide ET significatif
#define ASSERT_BENCHMARK_FASTER_AND_SIGNIFICANT(benchmarkA, benchmarkB, maxAllowedSlowdown) \
    do { \
        ASSERT_BENCHMARK_SIGNIFICANTLY_FASTER(benchmarkA, benchmarkB); \
        ASSERT_BENCHMARK_FASTER_WITH_LIMIT(benchmarkA, benchmarkB, maxAllowedSlowdown); \
    } while(0)

// ---------------------------------------------------------------------
// MACROS POUR LES TESTS DE BENCHMARK
// ---------------------------------------------------------------------

// Version simple sans baseline
#define TEST_BENCHMARK_SIMPLE(testName, benchmarkName, function, iterations) \
    TEST_CASE(Benchmark, testName) { \
        auto result = RUN_BENCHMARK(benchmarkName, function, iterations); \
        /* Enregistrer le résultat pour reporting */ \
        if (auto reporter = nkentseu::test::TestRunner::GetInstance().GetPerformanceReporter()) { \
            reporter->OnBenchmarkComplete(result); \
        } \
    }

// Version avec baseline (objet, pas pointeur)
#define TEST_BENCHMARK_WITH_BASELINE(testName, benchmarkName, function, iterations, baseline) \
    TEST_CASE(Benchmark, testName) { \
        auto result = RUN_BENCHMARK(benchmarkName, function, iterations); \
        ASSERT_PERFORMANCE_REGRESSION_WITH_LIMIT(baseline, result, 1.1); \
        /* Enregistrer le résultat pour reporting */ \
        if (auto reporter = nkentseu::test::TestRunner::GetInstance().GetPerformanceReporter()) { \
            reporter->OnBenchmarkComplete(result); \
        } \
    }

// Version avec baseline optionnelle (pointeur, peut être nullptr)
#define TEST_BENCHMARK_OPTIONAL_BASELINE(testName, benchmarkName, function, iterations, baselinePtr) \
    TEST_CASE(Benchmark, testName) { \
        auto result = RUN_BENCHMARK(benchmarkName, function, iterations); \
        if ((baselinePtr) != nullptr) { \
            ASSERT_PERFORMANCE_REGRESSION_WITH_LIMIT(*(baselinePtr), result, 1.1); \
        } \
        /* Enregistrer le résultat pour reporting */ \
        if (auto reporter = nkentseu::test::TestRunner::GetInstance().GetPerformanceReporter()) { \
            reporter->OnBenchmarkComplete(result); \
        } \
    }

// Comparaison directe de deux implémentations
#define COMPARE_BENCHMARKS(testName, nameA, funcA, nameB, funcB, iterations, maxSlowdown) \
    TEST_CASE(BenchmarkCompare, testName) { \
        auto resultA = RUN_BENCHMARK(nameA, funcA, iterations); \
        auto resultB = RUN_BENCHMARK(nameB, funcB, iterations); \
        ASSERT_BENCHMARK_FASTER_WITH_LIMIT(resultA, resultB, maxSlowdown); \
        /* Enregistrer les résultats */ \
        if (auto reporter = nkentseu::test::TestRunner::GetInstance().GetPerformanceReporter()) { \
            reporter->OnBenchmarkComplete(resultA); \
            reporter->OnBenchmarkComplete(resultB); \
        } \
    }

// Benchmark avec setup/teardown
#define BENCHMARK_WITH_SETUP(testName, benchmarkName, setupFunc, function, teardownFunc, iterations) \
    TEST_CASE(Benchmark, testName) { \
        auto result = RUN_BENCHMARK_WITH_SETUP( \
            benchmarkName, setupFunc, function, teardownFunc, iterations); \
        if (auto reporter = nkentseu::test::TestRunner::GetInstance().GetPerformanceReporter()) { \
            reporter->OnBenchmarkComplete(result); \
        } \
    }

// ---------------------------------------------------------------------
// MACROS POUR LE PROFILING
// ---------------------------------------------------------------------

// Macros pour le profiling - Version corrigée

// Macro pour démarrer un test avec profiling
#define BEGIN_PROFILING_SESSION(sessionName) \
    nkentseu::profiler::Profiler::GetInstance().StartSession(sessionName)

// Macro pour terminer le profiling et générer les rapports
#define END_PROFILING_SESSION_AND_REPORT(sessionName) \
    do { \
        nkentseu::profiler::Profiler::GetInstance().EndSession(); \
        /* Générer les rapports */ \
        nkentseu::profiler::Profiler::GetInstance().GenerateFlameGraph( \
            std::string(sessionName) + "_flamegraph.json"); \
        /* Envoyer les statistiques au reporter */ \
        if (auto reporter = nkentseu::test::TestRunner::GetInstance().GetPerformanceReporter()) { \
            reporter->OnProfileComplete( \
                nkentseu::profiler::Profiler::GetInstance().GetStatistics()); \
        } \
    } while(0)

// Macro complète pour test avec profiling (doit être utilisée en paire)
#define TEST_WITH_PROFILING_BEGIN(testName) \
    TEST_CASE(Profile, testName) { \
        BEGIN_PROFILING_SESSION(#testName);

#define TEST_WITH_PROFILING_END(testName) \
        END_PROFILING_SESSION_AND_REPORT(#testName); \
    }

// Version simplifiée pour usage commun (tout en une macro)
#define PROFILE_TEST_SCOPE(testName, ...) \
    TEST_CASE(Profile, testName) { \
        BEGIN_PROFILING_SESSION(#testName); \
        __VA_ARGS__ \
        END_PROFILING_SESSION_AND_REPORT(#testName); \
    }

// Macro pour profiling d'une fonction spécifique
#define PROFILE_FUNCTION_TEST(testName, functionToProfile) \
    TEST_CASE(Profile, testName) { \
        BEGIN_PROFILING_SESSION(#testName); \
        { \
            PROFILE_SCOPE(#functionToProfile); \
            functionToProfile(); \
        } \
        END_PROFILING_SESSION_AND_REPORT(#testName); \
    }

// ---------------------------------------------------------------------
// MACROS UTILITAIRES DE MESURE DE TEMPS
// ---------------------------------------------------------------------

// Macro pour mesurer le temps d'une expression
#define MEASURE_TIME(expression) \
    [&]() -> double { \
        auto start = std::chrono::high_resolution_clock::now(); \
        expression; \
        auto end = std::chrono::high_resolution_clock::now(); \
        return std::chrono::duration<double, std::milli>(end - start).count(); \
    }()

// Assertion sur le temps d'exécution (version améliorée)
#define ASSERT_EXECUTION_TIME_LESS(expression, maxTimeMs) \
    do { \
        double duration = MEASURE_TIME(expression); \
        if (duration > (maxTimeMs)) { \
            std::ostringstream oss; \
            oss << "Execution time exceeded: " << std::fixed << std::setprecision(2) \
                << duration << "ms > " << (maxTimeMs) << "ms"; \
            nkentseu::test::TestAssert::sCurrentTest->AddFailure( \
                oss.str(), __FILE__, __LINE__, #expression, duration); \
        } else { \
            nkentseu::test::TestAssert::sCurrentTest->AddSuccess( \
                #expression, duration, __FILE__, __LINE__); \
        } \
    } while(0)

#define ASSERT_EXECUTION_TIME_BETWEEN(expression, minTimeMs, maxTimeMs) \
    do { \
        double duration = MEASURE_TIME(expression); \
        if (duration < (minTimeMs) || duration > (maxTimeMs)) { \
            std::ostringstream oss; \
            oss << "Execution time out of range: " \
                << std::fixed << std::setprecision(2) << duration << "ms not in [" \
                << (minTimeMs) << "ms, " << (maxTimeMs) << "ms]"; \
            nkentseu::test::TestAssert::sCurrentTest->AddFailure( \
                oss.str(), __FILE__, __LINE__, #expression, duration); \
        } else { \
            nkentseu::test::TestAssert::sCurrentTest->AddSuccess( \
                #expression, duration, __FILE__, __LINE__); \
        } \
    } while(0)

// Macro pour exécuter et mesurer une fonction avec assertion simple
#define MEASURE_AND_ASSERT(testName, function, maxTimeMs) \
    TEST_CASE(Performance, testName) { \
        auto start = std::chrono::high_resolution_clock::now(); \
        function(); \
        auto end = std::chrono::high_resolution_clock::now(); \
        double duration = std::chrono::duration<double, std::milli>(end - start).count(); \
        if (duration > (maxTimeMs)) { \
            std::ostringstream oss; \
            oss << "Execution time exceeded: " << std::fixed << std::setprecision(2) \
                << duration << "ms > " << (maxTimeMs) << "ms"; \
            nkentseu::test::TestAssert::sCurrentTest->AddFailure( \
                oss.str(), __FILE__, __LINE__, #function, duration); \
        } \
    }

// ---------------------------------------------------------------------
// MACROS DE BENCHMARK AUTOMATIQUE (legacy - optionnel)
// ---------------------------------------------------------------------

// Note: Ces macros nécessitent un système d'enregistrement de benchmark
// qui doit être implémenté séparément

/*
#define BENCHMARK(name, iterations) \
class Benchmark##name##Case { \
public: \
    static nkentseu::benchmark::BenchmarkResult RunBenchmark(); \
}; \
static nkentseu::benchmark::BenchmarkRegistrar<Benchmark##name##Case> \
    gBenchmarkRegistrar_##name(#name, iterations); \
nkentseu::benchmark::BenchmarkResult Benchmark##name##Case::RunBenchmark()

#define BENCHMARK_FUNCTION(name, iterations) \
BENCHMARK(name, iterations) { \
    name(); \
}

// Version RAII automatique pour profiling
#define PROFILE_TEST(testName) \
    class ProfileTest##testName : public nkentseu::test::TestCase { \
    public: \
        ProfileTest##testName() : TestCase(#testName) {} \
        void Run() override; \
    }; \
    static nkentseu::test::detail::TestCaseRegistrar<ProfileTest##testName> \
        gRegistrar_ProfileTest_##testName(#testName); \
    void ProfileTest##testName::Run()
*/

// =====================================================================
// MACROS RACCOURCI POUR UN USAGE SIMPLIFIÉ
// =====================================================================

#ifdef UNIT_TEST_SHORT_MACROS

#define TC(class, name) TEST_CASE(class, name)
#define T(name) TEST(name)
#define TF(fixture, name) TEST_FIXTURE(fixture, name)

#define EQ(expected, actual) ASSERT_EQUAL(expected, actual)
#define NE(expected, actual) ASSERT_NOT_EQUAL(expected, actual)
#define TRUE_(condition) ASSERT_TRUE(condition)
#define FALSE_(condition) ASSERT_FALSE(condition)
#define NULL_(ptr) ASSERT_NULL(ptr)
#define NOT_NULL_(ptr) ASSERT_NOT_NULL(ptr)

#define LT(left, right) ASSERT_LESS(left, right)
#define LE(left, right) ASSERT_LESS_EQUAL(left, right)
#define GT(left, right) ASSERT_GREATER(left, right)
#define GE(left, right) ASSERT_GREATER_EQUAL(left, right)

#define THROWS(type, expr) ASSERT_THROWS(type, expr)
#define NO_THROW(expr) ASSERT_NO_THROW(expr)

#define CONTAINS(container, value) ASSERT_CONTAINS(container, value)
#define NOT_CONTAINS(container, value) ASSERT_NOT_CONTAINS(container, value)

// Benchmarks courts
#define BENCH(name, func, iter) TEST_BENCHMARK_SIMPLE(name, #name, func, iter)
#define BENCH_COMPARE(name, nameA, funcA, nameB, funcB, iter, limit) \
    COMPARE_BENCHMARKS(name, nameA, funcA, nameB, funcB, iter, limit)
#define PROF_SCOPE(name, ...) PROFILE_TEST_SCOPE(name, __VA_ARGS__)

#endif // UNIT_TEST_SHORT_MACROS