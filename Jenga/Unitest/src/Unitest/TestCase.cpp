#include "TestCase.h"
#include "TestAssert.h"

namespace nkentseu {
    namespace test {
        namespace detail {
            // Implementation of TestCaseAutoRegistrar::RegisterAll
            void TestCaseAutoRegistrar::RegisterAll() {
                for (auto* registrar : mRegistrars) {
                    registrar->RegisterTestCase();
                }
            }
        }
        
        TestCase::TestCase(const std::string& testName)
            : mTestName(testName), mFailed(false), mStopOnFailure(false) {
            TestAssert::sCurrentTest = this;
        }
        
        void TestCase::AddSuccess(const std::string& expression, double durationMs,
                                const std::string& file, int line) {
            mAssertResults.emplace_back(true, expression, "", file, line, durationMs);
            UpdatePerformanceData(durationMs);
        }
        
        void TestCase::AddFailure(const std::string& message, const std::string& file,
                                int line, const std::string& expression, double durationMs) {
            mAssertResults.emplace_back(false, expression, message, file, line, durationMs);
            UpdatePerformanceData(durationMs);
            mFailed = true;
            
            if (mStopOnFailure || TestAssert::sStopOnFailure) {
                throw std::runtime_error("Test stopped due to failure");
            }
        }
        
        void TestCase::UpdatePerformanceData(double durationMs) {
            mPerformanceData.mTotalDurationMs += durationMs;
            mPerformanceData.mAssertCount++;
            
            if (mPerformanceData.mAssertCount == 1) {
                mPerformanceData.mMinAssertDurationMs = durationMs;
                mPerformanceData.mMaxAssertDurationMs = durationMs;
            } else {
                mPerformanceData.mMinAssertDurationMs = 
                    std::min(mPerformanceData.mMinAssertDurationMs, durationMs);
                mPerformanceData.mMaxAssertDurationMs = 
                    std::max(mPerformanceData.mMaxAssertDurationMs, durationMs);
            }
        }
    }
}