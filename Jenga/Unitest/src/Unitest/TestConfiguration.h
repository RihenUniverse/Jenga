#pragma once
#include <vector>
#include <string>

namespace nkentseu {
    namespace test {
        
        struct TestConfiguration {
            bool mStopOnFirstFailure;
            bool mRunInParallel;
            bool mMeasurePerformance;
            bool mVerboseOutput;
            bool mShowProgressBar;
            bool mUseColors;
            bool mDebugMode;
            std::vector<std::string> mTestFilters;
            std::vector<std::string> mTestExclusions;
            std::string mOutputFormat;
            std::string mReportFile;
            int mThreadCount;
            int mRepeatCount;
            
            TestConfiguration() 
                : mStopOnFirstFailure(false), mRunInParallel(false),
                  mMeasurePerformance(true), mVerboseOutput(true),
                  mShowProgressBar(false), mUseColors(true), mDebugMode(false),
                  mOutputFormat("console"), mThreadCount(1), mRepeatCount(1) {}
        };
    }
}