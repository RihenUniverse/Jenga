// Profiler.h
#pragma once
#include <chrono>
#include <string>
#include <map>
#include <vector>
#include <stack>
#include <memory>
#include <thread>
#include <mutex>
#include <fstream>
#include <iomanip>

namespace nkentseu {
    namespace profiler {
        
        struct ProfileSample {
            std::string mName;
            std::thread::id mThreadId;
            std::chrono::high_resolution_clock::time_point mStartTime;
            std::chrono::high_resolution_clock::time_point mEndTime;
            std::vector<ProfileSample> mChildren;
            ProfileSample* mParent;
            
            double DurationMs() const {
                return std::chrono::duration<double, std::milli>(
                    mEndTime - mStartTime).count();
            }
        };
        
        struct ProfileStatistics {
            std::string mFunctionName;
            size_t mCallCount;
            double mTotalTimeMs;
            double mMinTimeMs;
            double mMaxTimeMs;
            double mAverageTimeMs;
            double mPercentageOfTotal;
            
            ProfileStatistics();
        };
        
        class Profiler {
            public:
                static Profiler& GetInstance();
                
                void StartSession(const std::string& name = "Default");
                void EndSession();
                void BeginSample(const std::string& name);
                void EndSample();
                const ProfileSample& GetRootSample() const;
                std::vector<ProfileStatistics> GetStatistics() const;
                void GenerateFlameGraph(const std::string& outputFile);
                void GenerateCallGraph(const std::string& outputFile);
                
                // RAII wrapper (template-like structure doit rester dans .h)
                class ScopedProfile {
                    public:
                        ScopedProfile(const std::string& name) 
                            : mName(name) {
                            GetInstance().BeginSample(name);
                        }
                        
                        ~ScopedProfile() {
                            GetInstance().EndSample();
                        }
                        
                    private:
                        std::string mName;
                };
                
            private:
                Profiler();
                ~Profiler() = default;
                
                Profiler(const Profiler&) = delete;
                Profiler& operator=(const Profiler&) = delete;
                
                void CollectStatistics(const ProfileSample& sample,
                                    std::map<std::string, ProfileStatistics>& statsMap) const;
                
                void GenerateFlameGraphJSON(const ProfileSample& sample, 
                                        std::ofstream& file, 
                                        int depth) const;
                
                ProfileSample mRootSample;
                std::stack<ProfileSample*> mSampleStack;
                std::thread::id mMainThreadId;
                bool mIsActive;
                std::string mSessionName;
                mutable std::mutex mMutex;
        };
        
        // Macros pour profiling automatique (doivent rester dans .h)
        #define PROFILE_SCOPE(name) \
            nkentseu::profiler::Profiler::ScopedProfile __profile_scope__(name)
        
        #define PROFILE_FUNCTION() PROFILE_SCOPE(__FUNCTION__)
    }
}