#pragma once

#include <string>
#include <type_traits>
#include <memory>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <algorithm>
#include <vector>
#include <map>
#include <sstream>
#include <iomanip>
#include <functional>
#include "TestCase.h"

namespace nkentseu {
    namespace test
    {
        // Forward declaration pour l'amitié
        class TestCase;

        namespace detail {
            template<typename T, typename = void>
            struct HasToString : std::false_type {};
            
            template<typename T>
            struct HasToString<T, std::void_t<decltype(std::to_string(std::declval<T>()))>> : std::true_type {};
            
            // Helper pour formatage multiplateforme des pointeurs
            template<typename T>
            static std::string FormatPointer(T* ptr) {
                if (ptr == nullptr) return "nullptr";
                
                char buffer[32];
            #ifdef _WIN32
                // Utiliser sprintf_s sur Windows
                sprintf_s(buffer, sizeof(buffer), "%p", static_cast<const void*>(ptr));
            #else
                // Utiliser snprintf sur Unix/Linux
                snprintf(buffer, sizeof(buffer), "%p", static_cast<const void*>(ptr));
            #endif
                return std::string(buffer);
            }
            
            // Safe abs pour différents types
            template<typename T>
            static auto SafeAbs(const T& value) -> decltype(std::abs(value)) {
                return std::abs(value);
            }
        }

        // Template principal ToString
        template<typename T>
        struct ToStringFormatter {
            static std::string Format(const T& value) {
                if constexpr (std::is_pointer_v<T>) {
                    if (value == nullptr) {
                        return "nullptr";
                    }
                    return detail::FormatPointer(value);
                } else if constexpr (std::is_arithmetic_v<T>) {
                    if constexpr (std::is_same_v<T, bool>) {
                        return value ? "true" : "false";
                    } else if constexpr (std::is_integral_v<T>) {
                        return std::to_string(value);
                    } else if constexpr (std::is_floating_point_v<T>) {
                        double val = static_cast<double>(value);
                        if (val == 0.0) return "0.0";
                        
                        if (std::abs(val) < 1e-6 || std::abs(val) > 1e9) {
                            std::ostringstream oss;
                            oss << std::scientific << std::setprecision(6) << val;
                            return oss.str();
                        } else {
                            std::ostringstream oss;
                            oss << std::fixed << std::setprecision(6) << val;
                            std::string str = oss.str();
                            str.erase(str.find_last_not_of('0') + 1, std::string::npos);
                            if (str.back() == '.') str.push_back('0');
                            return str;
                        }
                    }
                } else if constexpr (std::is_same_v<T, std::string>) {
                    std::string result = "\"";
                    for (char c : value) {
                        switch (c) {
                            case '\n': result += "\\n"; break;
                            case '\t': result += "\\t"; break;
                            case '\r': result += "\\r"; break;
                            case '\"': result += "\\\""; break;
                            case '\\': result += "\\\\"; break;
                            default: result += c; break;
                        }
                    }
                    result += "\"";
                    return result;
                } else if constexpr (std::is_constructible_v<std::string, T>) {
                    return std::string(value);
                } else {
                    if constexpr (detail::HasToString<decltype(value)>::value) {
                        return std::to_string(value);
                    } else {
                        return "<object>";
                    }
                }
                return "";
            }
        };

        // Spécialisations pour les types courants
        template<>
        struct ToStringFormatter<const char*> {
            static std::string Format(const char* value) {
                if (value == nullptr) return "nullptr";
                return ToStringFormatter<std::string>::Format(std::string(value));
            }
        };

        template<>
        struct ToStringFormatter<char*> {
            static std::string Format(char* value) {
                if (value == nullptr) return "nullptr";
                return ToStringFormatter<std::string>::Format(std::string(value));
            }
        };

        template<>
        struct ToStringFormatter<std::nullptr_t> {
            static std::string Format(std::nullptr_t) {
                return "nullptr";
            }
        };

        template<>
        struct ToStringFormatter<void*> {
            static std::string Format(void* ptr) {
                return detail::FormatPointer(ptr);
            }
        };

        template<typename T>
        struct ToStringFormatter<std::vector<T>> {
            static std::string Format(const std::vector<T>& vec) {
                if (vec.empty()) return "[]";
                
                std::string result = "[";
                for (size_t i = 0; i < vec.size(); ++i) {
                    if (i > 0) result += ", ";
                    result += ToStringFormatter<T>::Format(vec[i]);
                }
                result += "]";
                return result;
            }
        };

        template<typename K, typename V>
        struct ToStringFormatter<std::map<K, V>> {
            static std::string Format(const std::map<K, V>& map) {
                if (map.empty()) return "{}";
                
                std::string result = "{";
                size_t count = 0;
                for (const auto& pair : map) {
                    if (count++ > 0) result += ", ";
                    result += ToStringFormatter<K>::Format(pair.first) + ": " + 
                             ToStringFormatter<V>::Format(pair.second);
                }
                result += "}";
                return result;
            }
        };

        template<typename T>
        struct ToStringFormatter<std::initializer_list<T>> {
            static std::string Format(const std::initializer_list<T>& list) {
                if (list.size() == 0) return "{}";
                
                std::string result = "{";
                size_t i = 0;
                for (const auto& item : list) {
                    if (i++ > 0) result += ", ";
                    result += ToStringFormatter<T>::Format(item);
                }
                result += "}";
                return result;
            }
        };

        // Fonction helper pour utiliser le formatter
        template<typename T>
        std::string ToString(const T& value) {
            return ToStringFormatter<T>::Format(value);
        }

        class TestAssert {
            public:
                static TestCase* sCurrentTest;
                static bool sStopOnFailure;
                
                struct Timer {
                    std::chrono::high_resolution_clock::time_point mStart;
                    
                    Timer() : mStart(std::chrono::high_resolution_clock::now()) {}
                    
                    double ElapsedMs() const {
                        auto end = std::chrono::high_resolution_clock::now();
                        return std::chrono::duration<double, std::milli>(end - mStart).count();
                    }
                };
                
                // ==================== ASSERTIONS FONDAMENTALES ====================
                
                template<typename T>
                static void Equal(const T& expected, const T& actual, 
                                const std::string& message = "", 
                                const std::string& file = "", 
                                int line = 0,
                                const std::string& expression = "") {
                    Timer timer;
                    bool success = (expected == actual);
                    double duration = timer.ElapsedMs();
                    
                    if (!success) {
                        std::string failureMsg = FormatFailure("Equal", message, 
                                                            expected, actual, 
                                                            expression, file, line);
                        sCurrentTest->AddFailure(failureMsg, file, line, expression, duration);
                    } else {
                        sCurrentTest->AddSuccess(expression, duration, file, line);
                    }
                }
                
                template<typename T>
                static void NotEqual(const T& expected, const T& actual, 
                                const std::string& message = "", 
                                const std::string& file = "", 
                                int line = 0,
                                const std::string& expression = "") {
                    Timer timer;
                    bool success = (expected != actual);
                    double duration = timer.ElapsedMs();
                    
                    if (!success) {
                        std::string failureMsg = "AssertNotEqual failed";
                        if (!message.empty()) failureMsg += ": " + message;
                        if (!expression.empty()) failureMsg += "\n  Expression: " + expression;
                        failureMsg += "\n  Values should not be equal: " + ToString(expected);
                        failureMsg += FormatLocation(file, line);
                        sCurrentTest->AddFailure(failureMsg, file, line, expression, duration);
                    } else {
                        sCurrentTest->AddSuccess(expression, duration, file, line);
                    }
                }
                
                static void True(bool condition, 
                            const std::string& message = "",
                            const std::string& file = "", 
                            int line = 0,
                            const std::string& expression = "") {
                    Timer timer;
                    bool success = condition;
                    double duration = timer.ElapsedMs();
                    
                    if (!success) {
                        std::string failureMsg = "AssertTrue failed";
                        if (!message.empty()) failureMsg += ": " + message;
                        if (!expression.empty()) {
                            failureMsg += "\n  Expression: " + expression;
                        } else {
                            failureMsg += "\n  Condition is false";
                        }
                        failureMsg += FormatLocation(file, line);
                        sCurrentTest->AddFailure(failureMsg, file, line, expression, duration);
                    } else {
                        sCurrentTest->AddSuccess(expression, duration, file, line);
                    }
                }
                
                static void False(bool condition, 
                                const std::string& message = "",
                                const std::string& file = "", 
                                int line = 0,
                                const std::string& expression = "") {
                    Timer timer;
                    bool success = !condition;
                    double duration = timer.ElapsedMs();
                    
                    if (!success) {
                        std::string failureMsg = "AssertFalse failed";
                        if (!message.empty()) failureMsg += ": " + message;
                        if (!expression.empty()) {
                            failureMsg += "\n  Expression: " + expression;
                        } else {
                            failureMsg += "\n  Condition is true";
                        }
                        failureMsg += FormatLocation(file, line);
                        sCurrentTest->AddFailure(failureMsg, file, line, expression, duration);
                    } else {
                        sCurrentTest->AddSuccess(expression, duration, file, line);
                    }
                }
                
                // ==================== ASSERTIONS DE POINTEURS ====================
                
                template<typename T>
                static void Null(T* ptr, 
                            const std::string& message = "",
                            const std::string& file = "", 
                            int line = 0,
                            const std::string& expression = "") {
                    Timer timer;
                    bool success = (ptr == nullptr);
                    double duration = timer.ElapsedMs();
                    
                    if (!success) {
                        std::string failureMsg = "AssertNull failed";
                        if (!message.empty()) failureMsg += ": " + message;
                        if (!expression.empty()) failureMsg += "\n  Expression: " + expression;
                        failureMsg += "\n  Pointer is not null: " + ToString(ptr);
                        failureMsg += FormatLocation(file, line);
                        sCurrentTest->AddFailure(failureMsg, file, line, expression, duration);
                    } else {
                        sCurrentTest->AddSuccess(expression, duration, file, line);
                    }
                }
                
                template<typename T>
                static void NotNull(T* ptr, 
                                const std::string& message = "",
                                const std::string& file = "", 
                                int line = 0,
                                const std::string& expression = "") {
                    Timer timer;
                    bool success = (ptr != nullptr);
                    double duration = timer.ElapsedMs();
                    
                    if (!success) {
                        std::string failureMsg = "AssertNotNull failed";
                        if (!message.empty()) failureMsg += ": " + message;
                        if (!expression.empty()) failureMsg += "\n  Expression: " + expression;
                        failureMsg += "\n  Pointer is null";
                        failureMsg += FormatLocation(file, line);
                        sCurrentTest->AddFailure(failureMsg, file, line, expression, duration);
                    } else {
                        sCurrentTest->AddSuccess(expression, duration, file, line);
                    }
                }
                
                // Smart pointers
                template<typename T>
                static void Null(const std::unique_ptr<T>& ptr, 
                            const std::string& message = "",
                            const std::string& file = "", 
                            int line = 0,
                            const std::string& expression = "") {
                    Timer timer;
                    bool success = (ptr == nullptr);
                    double duration = timer.ElapsedMs();
                    
                    if (!success) {
                        std::string failureMsg = "AssertNull failed";
                        if (!message.empty()) failureMsg += ": " + message;
                        if (!expression.empty()) failureMsg += "\n  Expression: " + expression;
                        failureMsg += "\n  Smart pointer is not null";
                        failureMsg += FormatLocation(file, line);
                        sCurrentTest->AddFailure(failureMsg, file, line, expression, duration);
                    } else {
                        sCurrentTest->AddSuccess(expression, duration, file, line);
                    }
                }
                
                template<typename T>
                static void NotNull(const std::unique_ptr<T>& ptr, 
                                const std::string& message = "",
                                const std::string& file = "", 
                                int line = 0,
                                const std::string& expression = "") {
                    Timer timer;
                    bool success = (ptr != nullptr);
                    double duration = timer.ElapsedMs();
                    
                    if (!success) {
                        std::string failureMsg = "AssertNotNull failed";
                        if (!message.empty()) failureMsg += ": " + message;
                        if (!expression.empty()) failureMsg += "\n  Expression: " + expression;
                        failureMsg += "\n  Smart pointer is null";
                        failureMsg += FormatLocation(file, line);
                        sCurrentTest->AddFailure(failureMsg, file, line, expression, duration);
                    } else {
                        sCurrentTest->AddSuccess(expression, duration, file, line);
                    }
                }
                
                template<typename T>
                static void Null(const std::shared_ptr<T>& ptr, 
                            const std::string& message = "",
                            const std::string& file = "", 
                            int line = 0,
                            const std::string& expression = "") {
                    Timer timer;
                    bool success = (ptr == nullptr);
                    double duration = timer.ElapsedMs();
                    
                    if (!success) {
                        std::string failureMsg = "AssertNull failed";
                        if (!message.empty()) failureMsg += ": " + message;
                        if (!expression.empty()) failureMsg += "\n  Expression: " + expression;
                        failureMsg += "\n  Shared pointer is not null";
                        failureMsg += FormatLocation(file, line);
                        sCurrentTest->AddFailure(failureMsg, file, line, expression, duration);
                    } else {
                        sCurrentTest->AddSuccess(expression, duration, file, line);
                    }
                }
                
                template<typename T>
                static void NotNull(const std::shared_ptr<T>& ptr, 
                                const std::string& message = "",
                                const std::string& file = "", 
                                int line = 0,
                                const std::string& expression = "") {
                    Timer timer;
                    bool success = (ptr != nullptr);
                    double duration = timer.ElapsedMs();
                    
                    if (!success) {
                        std::string failureMsg = "AssertNotNull failed";
                        if (!message.empty()) failureMsg += ": " + message;
                        if (!expression.empty()) failureMsg += "\n  Expression: " + expression;
                        failureMsg += "\n  Shared pointer is null";
                        failureMsg += FormatLocation(file, line);
                        sCurrentTest->AddFailure(failureMsg, file, line, expression, duration);
                    } else {
                        sCurrentTest->AddSuccess(expression, duration, file, line);
                    }
                }
                
                // ==================== ASSERTIONS DE COMPARAISON ====================
                
                template<typename T>
                static void Less(const T& left, const T& right, 
                            const std::string& message = "",
                            const std::string& file = "", 
                            int line = 0,
                            const std::string& expression = "") {
                    Timer timer;
                    bool success = (left < right);
                    double duration = timer.ElapsedMs();
                    
                    if (!success) {
                        std::string failureMsg = FormatComparisonFailure("Less", message, 
                                                                    left, right, "<", 
                                                                    expression, file, line);
                        sCurrentTest->AddFailure(failureMsg, file, line, expression, duration);
                    } else {
                        sCurrentTest->AddSuccess(expression, duration, file, line);
                    }
                }
                
                template<typename T>
                static void LessEqual(const T& left, const T& right, 
                                    const std::string& message = "",
                                    const std::string& file = "", 
                                    int line = 0,
                                    const std::string& expression = "") {
                    Timer timer;
                    bool success = (left <= right);
                    double duration = timer.ElapsedMs();
                    
                    if (!success) {
                        std::string failureMsg = FormatComparisonFailure("LessEqual", message, 
                                                                    left, right, "<=", 
                                                                    expression, file, line);
                        sCurrentTest->AddFailure(failureMsg, file, line, expression, duration);
                    } else {
                        sCurrentTest->AddSuccess(expression, duration, file, line);
                    }
                }
                
                template<typename T>
                static void Greater(const T& left, const T& right, 
                                const std::string& message = "",
                                const std::string& file = "", 
                                int line = 0,
                                const std::string& expression = "") {
                    Timer timer;
                    bool success = (left > right);
                    double duration = timer.ElapsedMs();
                    
                    if (!success) {
                        std::string failureMsg = FormatComparisonFailure("Greater", message, 
                                                                    left, right, ">", 
                                                                    expression, file, line);
                        sCurrentTest->AddFailure(failureMsg, file, line, expression, duration);
                    } else {
                        sCurrentTest->AddSuccess(expression, duration, file, line);
                    }
                }
                
                template<typename T>
                static void GreaterEqual(const T& left, const T& right, 
                                    const std::string& message = "",
                                    const std::string& file = "", 
                                    int line = 0,
                                    const std::string& expression = "") {
                    Timer timer;
                    bool success = (left >= right);
                    double duration = timer.ElapsedMs();
                    
                    if (!success) {
                        std::string failureMsg = FormatComparisonFailure("GreaterEqual", message, 
                                                                    left, right, ">=", 
                                                                    expression, file, line);
                        sCurrentTest->AddFailure(failureMsg, file, line, expression, duration);
                    } else {
                        sCurrentTest->AddSuccess(expression, duration, file, line);
                    }
                }
                
                // ==================== ASSERTIONS AVEC TOLÉRANCE ====================
                
                template<typename T>
                static void EqualWithTolerance(const T& expected, const T& actual, 
                                            const T& tolerance,
                                            const std::string& message = "", 
                                            const std::string& file = "", 
                                            int line = 0,
                                            const std::string& expression = "") {
                    Timer timer;
                    T difference = detail::SafeAbs(expected - actual);
                    bool success = (difference <= tolerance);
                    double duration = timer.ElapsedMs();
                    
                    if (!success) {
                        std::string failureMsg = "AssertEqualWithTolerance failed";
                        if (!message.empty()) failureMsg += ": " + message;
                        if (!expression.empty()) failureMsg += "\n  Expression: " + expression;
                        failureMsg += "\n  Expected: " + ToString(expected) + " ± " + ToString(tolerance);
                        failureMsg += "\n  Actual: " + ToString(actual);
                        failureMsg += "\n  Difference: " + ToString(difference) + " > " + ToString(tolerance);
                        failureMsg += FormatLocation(file, line);
                        sCurrentTest->AddFailure(failureMsg, file, line, expression, duration);
                    } else {
                        sCurrentTest->AddSuccess(expression, duration, file, line);
                    }
                }
                
                template<typename T>
                static void Near(const T& expected, const T& actual, 
                            const T& tolerance,
                            const std::string& message = "", 
                            const std::string& file = "", 
                            int line = 0,
                            const std::string& expression = "") {
                    EqualWithTolerance(expected, actual, tolerance, message, file, line, expression);
                }
                
                // ==================== ASSERTIONS D'EXCEPTIONS ====================
                
                template<typename ExceptionT, typename FunctionT>
                static void Throws(FunctionT func, 
                                const std::string& message = "",
                                const std::string& file = "", 
                                int line = 0,
                                const std::string& expression = "") {
                    Timer timer;
                    bool success = false;
                    std::string failureMsg;
                    
                    try {
                        func();
                        failureMsg = "AssertThrows failed: Expected exception was not thrown";
                        if (!message.empty()) failureMsg += ": " + message;
                        if (!expression.empty()) failureMsg += "\n  Expression: " + expression;
                    } catch (const ExceptionT& e) {
                        success = true;
                    } catch (const std::exception& e) {
                        failureMsg = "AssertThrows failed: Wrong exception type thrown: " + 
                                    std::string(e.what());
                        if (!message.empty()) failureMsg += ": " + message;
                        if (!expression.empty()) failureMsg += "\n  Expression: " + expression;
                    } catch (...) {
                        failureMsg = "AssertThrows failed: Unknown exception type thrown";
                        if (!message.empty()) failureMsg += ": " + message;
                        if (!expression.empty()) failureMsg += "\n  Expression: " + expression;
                    }
                    
                    double duration = timer.ElapsedMs();
                    
                    if (!success) {
                        failureMsg += FormatLocation(file, line);
                        sCurrentTest->AddFailure(failureMsg, file, line, expression, duration);
                    } else {
                        sCurrentTest->AddSuccess(expression, duration, file, line);
                    }
                }
                
                template<typename FunctionT>
                static void NoThrow(FunctionT func, 
                                const std::string& message = "",
                                const std::string& file = "", 
                                int line = 0,
                                const std::string& expression = "") {
                    Timer timer;
                    bool success = true;
                    std::string failureMsg;
                    
                    try {
                        func();
                    } catch (const std::exception& e) {
                        success = false;
                        failureMsg = "AssertNoThrow failed: Unexpected exception: " + 
                                    std::string(e.what());
                        if (!message.empty()) failureMsg += ": " + message;
                        if (!expression.empty()) failureMsg += "\n  Expression: " + expression;
                    } catch (...) {
                        success = false;
                        failureMsg = "AssertNoThrow failed: Unexpected unknown exception";
                        if (!message.empty()) failureMsg += ": " + message;
                        if (!expression.empty()) failureMsg += "\n  Expression: " + expression;
                    }
                    
                    double duration = timer.ElapsedMs();
                    
                    if (!success) {
                        failureMsg += FormatLocation(file, line);
                        sCurrentTest->AddFailure(failureMsg, file, line, expression, duration);
                    } else {
                        sCurrentTest->AddSuccess(expression, duration, file, line);
                    }
                }
                
                // ==================== PERFORMANCE ASSERTIONS ====================
                
                template<typename FunctionT>
                static void ExecutionTimeLess(FunctionT func, double maxTimeMs,
                                            const std::string& message = "",
                                            const std::string& file = "", 
                                            int line = 0,
                                            const std::string& expression = "") {
                    auto start = std::chrono::high_resolution_clock::now();
                    func();
                    auto end = std::chrono::high_resolution_clock::now();
                    double duration = std::chrono::duration<double, std::milli>(end - start).count();
                    
                    if (duration > maxTimeMs) {
                        std::string failureMsg = "AssertExecutionTimeLess failed";
                        if (!message.empty()) failureMsg += ": " + message;
                        if (!expression.empty()) failureMsg += "\n  Expression: " + expression;
                        failureMsg += "\n  Execution time: " + std::to_string(duration) + "ms";
                        failureMsg += "\n  Maximum allowed: " + std::to_string(maxTimeMs) + "ms";
                        failureMsg += FormatLocation(file, line);
                        sCurrentTest->AddFailure(failureMsg, file, line, expression, duration);
                    } else {
                        sCurrentTest->AddSuccess(expression, duration, file, line);
                    }
                }
                
                // ==================== ASSERTIONS DE COLLECTIONS ====================
                
                template<typename T>
                static void Contains(const std::vector<T>& container, const T& value,
                                const std::string& message = "",
                                const std::string& file = "", 
                                int line = 0,
                                const std::string& expression = "") {
                    Timer timer;
                    bool success = std::find(container.begin(), container.end(), value) != container.end();
                    double duration = timer.ElapsedMs();
                    
                    if (!success) {
                        std::string failureMsg = "AssertContains failed";
                        if (!message.empty()) failureMsg += ": " + message;
                        if (!expression.empty()) failureMsg += "\n  Expression: " + expression;
                        failureMsg += "\n  Value: " + ToString(value);
                        failureMsg += "\n  Container: " + ToString(container);
                        failureMsg += FormatLocation(file, line);
                        sCurrentTest->AddFailure(failureMsg, file, line, expression, duration);
                    } else {
                        sCurrentTest->AddSuccess(expression, duration, file, line);
                    }
                }
                
                template<typename T>
                static void NotContains(const std::vector<T>& container, const T& value,
                                    const std::string& message = "",
                                    const std::string& file = "", 
                                    int line = 0,
                                    const std::string& expression = "") {
                    Timer timer;
                    bool success = std::find(container.begin(), container.end(), value) == container.end();
                    double duration = timer.ElapsedMs();
                    
                    if (!success) {
                        std::string failureMsg = "AssertNotContains failed";
                        if (!message.empty()) failureMsg += ": " + message;
                        if (!expression.empty()) failureMsg += "\n  Expression: " + expression;
                        failureMsg += "\n  Value: " + ToString(value);
                        failureMsg += "\n  Container: " + ToString(container);
                        failureMsg += FormatLocation(file, line);
                        sCurrentTest->AddFailure(failureMsg, file, line, expression, duration);
                    } else {
                        sCurrentTest->AddSuccess(expression, duration, file, line);
                    }
                }
                
                // ==================== Surcharges pour les types communs ====================
                
                static void Equal(size_t expected, size_t actual, 
                                const std::string& message = "", 
                                const std::string& file = "", 
                                int line = 0,
                                const std::string& expression = "") {
                    Equal<size_t>(expected, actual, message, file, line, expression);
                }
                
                static void Equal(const char* expected, const std::string& actual, 
                                const std::string& message = "", 
                                const std::string& file = "", 
                                int line = 0,
                                const std::string& expression = "") {
                    Equal<std::string>(std::string(expected), actual, message, file, line, expression);
                }
                
                static void Equal(const std::string& expected, const char* actual, 
                                const std::string& message = "", 
                                const std::string& file = "", 
                                int line = 0,
                                const std::string& expression = "") {
                    Equal<std::string>(expected, std::string(actual), message, file, line, expression);
                }
                
                static void Equal(const char* expected, const char* actual, 
                                const std::string& message = "", 
                                const std::string& file = "", 
                                int line = 0,
                                const std::string& expression = "") {
                    Equal<std::string>(std::string(expected), std::string(actual), 
                                    message, file, line, expression);
                }
                
                // ==================== MÉTHODES DE PERFORMANCE ====================
                
                static double MeasureExecutionTime(std::function<void()> func, 
                                                int iterations = 1) {
                    auto start = std::chrono::high_resolution_clock::now();
                    for (int i = 0; i < iterations; ++i) {
                        func();
                    }
                    auto end = std::chrono::high_resolution_clock::now();
                    return std::chrono::duration<double, std::milli>(end - start).count() / iterations;
                }
                
                // ==================== MÉTHODES UTILITAIRES ====================
                
                static void SetStopOnFailure(bool stop) {
                    sStopOnFailure = stop;
                }
                
                static bool GetStopOnFailure() {
                    return sStopOnFailure;
                }
                
            private:
                template<typename T>
                static std::string FormatFailure(const std::string& assertion, 
                                            const std::string& message,
                                            const T& expected, const T& actual, 
                                            const std::string& expression,
                                            const std::string& file, int line) {
                    std::string result = "Assert" + assertion + " failed";
                    if (!message.empty()) {
                        result += ": " + message;
                    }
                    if (!expression.empty()) {
                        result += "\n  Expression: " + expression;
                    }
                    result += "\n  Expected: " + ToString(expected);
                    result += "\n  Actual:   " + ToString(actual);
                    result += ComputeDifference(expected, actual);
                    result += FormatLocation(file, line);
                    return result;
                }
                
                template<typename T>
                static std::string FormatComparisonFailure(const std::string& assertion, 
                                                        const std::string& message,
                                                        const T& left, const T& right,
                                                        const std::string& operatorStr,
                                                        const std::string& expression,
                                                        const std::string& file, int line) {
                    std::string result = "Assert" + assertion + " failed";
                    if (!message.empty()) {
                        result += ": " + message;
                    }
                    if (!expression.empty()) {
                        result += "\n  Expression: " + expression;
                    } else {
                        result += "\n  Expression: " + ToString(left) + " " + 
                                operatorStr + " " + ToString(right);
                    }
                    result += "\n  Left:  " + ToString(left);
                    result += "\n  Right: " + ToString(right);
                    result += FormatLocation(file, line);
                    return result;
                }
                
                template<typename T>
                static std::string ComputeDifference(const T& expected, const T& actual) {
                    if constexpr (std::is_arithmetic_v<T>) {
                        double diff = static_cast<double>(actual) - static_cast<double>(expected);
                        if (std::abs(diff) > 1e-10) {
                            std::ostringstream oss;
                            oss << "\n  Difference: " << std::scientific << std::setprecision(6) 
                                << diff << " (";
                            if (expected != 0) {
                                oss << std::fixed << std::setprecision(2) 
                                    << (diff / static_cast<double>(expected) * 100.0) << "%)";
                            } else {
                                oss << "N/A)";
                            }
                            return oss.str();
                        }
                    }
                    return "";
                }
                
                static std::string FormatLocation(const std::string& file, int line) {
                    if (!file.empty() && line > 0) {
                        return "\n  Location: " + file + ":" + std::to_string(line);
                    }
                    return "";
                }
        };

    } // namespace test
} // namespace nkentseu