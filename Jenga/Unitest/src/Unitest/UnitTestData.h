#pragma once
#include <string>
#include <vector>
#include <map>

namespace nkentseu {
    namespace test {
        struct TestRunStatistics {
            size_t mTotalTestCases;
            size_t mPassedTestCases;
            size_t mFailedTestCases;
            size_t mSkippedTestCases;
            size_t mTotalAssertions;
            size_t mPassedAssertions;
            size_t mFailedAssertions;
            double mTotalExecutionTimeMs;
            double mAverageTestTimeMs;
            double mAverageAssertTimeMs;
            
            TestRunStatistics()
                : mTotalTestCases(0), mPassedTestCases(0), mFailedTestCases(0),
                  mSkippedTestCases(0), mTotalAssertions(0), mPassedAssertions(0),
                  mFailedAssertions(0), mTotalExecutionTimeMs(0.0),
                  mAverageTestTimeMs(0.0), mAverageAssertTimeMs(0.0) {}
        };
        
        struct AssertionDetail {
            std::string mExpression;
            std::string mExpected;
            std::string mActual;
            std::string mMessage;
            std::string mFile;
            int mLine;
            double mExecutionTimeMs;
            bool mSuccess;
            
            AssertionDetail()
                : mLine(0), mExecutionTimeMs(0.0), mSuccess(false) {}
        };
        
        struct TestCaseResult {
            std::string mName;
            std::vector<AssertionDetail> mAssertions;
            TestRunStatistics mStatistics;
            bool mSuccess;
            bool mSkipped;
            std::string mSkipReason;
            double mExecutionTimeMs;
            
            TestCaseResult() 
                : mSuccess(false), mSkipped(false), mExecutionTimeMs(0.0) {}
        };
        
        struct UnitTestDataEntry {
            std::string mTestName;
            std::vector<std::string> mFailedAssertMessages;  // Messages des assertions échouées
            std::vector<std::string> mPassedAssertExpressions; // Expressions des assertions réussies
            size_t mTotalAsserts;      // Nombre total d'assertions
            size_t mPassedAsserts;     // Nombre d'assertions réussies (compteur)
            size_t mFailedAsserts;     // Nombre d'assertions échouées (compteur)
            double mTotalDurationMs;
            double mAverageAssertDurationMs;
            bool mSuccess;
            bool mSkipped;
            std::string mSkipReason;
            
            UnitTestDataEntry() 
                : mTotalAsserts(0), mPassedAsserts(0), mFailedAsserts(0),
                  mTotalDurationMs(0.0), mAverageAssertDurationMs(0.0),
                  mSuccess(true), mSkipped(false) {}
        };
    }
}