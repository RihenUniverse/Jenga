#pragma once
#include <string>
#include <vector>
#include <functional>
#include <memory>
#include <stdexcept>

namespace nkentseu {
    namespace test {
        namespace detail {
            class ITestCaseRegistrar {
                public:
                    virtual ~ITestCaseRegistrar() = default;
                    virtual void RegisterTestCase() = 0;
            };

            class TestCaseAutoRegistrar {
                public:
                    static TestCaseAutoRegistrar& GetInstance();
                    
                    void AddRegistrar(ITestCaseRegistrar* registrar) {
                        mRegistrars.push_back(registrar);
                    }
                    
                    void RegisterAll();  // Deferred implementation
                    
                private:
                    TestCaseAutoRegistrar() = default;
                    std::vector<ITestCaseRegistrar*> mRegistrars;
                    friend void RegisterAllTestCases();
            };

            // Forward declarations
            class TestRunner;

            template<typename T>
            class TestCaseRegistrar : public ITestCaseRegistrar {
                public:
                    TestCaseRegistrar(const std::string& testName) : mTestName(testName) {
                        // Deferred registration - just store the registrar
                        TestCaseAutoRegistrar::GetInstance().AddRegistrar(this);
                    }
                    
                    void RegisterTestCase() override;
                    
                private:
                    std::string mTestName;
                    template<typename U> friend class TestCaseRegistrar;
            };
        }

        // Forward declarations
        class TestRunner;
        
        struct AssertResult {
            bool mSuccess;
            std::string mExpression;
            std::string mMessage;
            std::string mFile;
            int mLine;
            double mDurationMs;
            
            AssertResult(bool success, const std::string& expression, 
                        const std::string& message, const std::string& file, 
                        int line, double durationMs)
                : mSuccess(success), mExpression(expression), mMessage(message),
                  mFile(file), mLine(line), mDurationMs(durationMs) {}
        };

        struct TestPerformanceData {
            double mTotalDurationMs;
            double mMinAssertDurationMs;
            double mMaxAssertDurationMs;
            size_t mAssertCount;
            
            TestPerformanceData() 
                : mTotalDurationMs(0.0), mMinAssertDurationMs(0.0),
                  mMaxAssertDurationMs(0.0), mAssertCount(0) {}
        };

        class TestCase {
            public:
                explicit TestCase(const std::string& testName);
                virtual ~TestCase() = default;
                
                virtual void Run() = 0;
                
                const std::string& GetName() const { return mTestName; }
                const std::vector<AssertResult>& GetAssertResults() const { return mAssertResults; }
                const TestPerformanceData& GetPerformanceData() const { return mPerformanceData; }
                bool HasFailed() const { return mFailed; }
                
                void AddSuccess(const std::string& expression, double durationMs,
                            const std::string& file, int line);
                void AddFailure(const std::string& message, const std::string& file,
                            int line, const std::string& expression, double durationMs);
                
                void SetStopOnFailure(bool stop) { mStopOnFailure = stop; }
                bool GetStopOnFailure() const { return mStopOnFailure; }
                
            protected:
                std::string mTestName;
                std::vector<AssertResult> mAssertResults;
                TestPerformanceData mPerformanceData;
                bool mFailed;
                bool mStopOnFailure;
                
            private:
                void UpdatePerformanceData(double durationMs);
        };
    }
}