// Profiler.cpp
#include "Profiler.h"
#include <algorithm>

namespace nkentseu {
    namespace profiler {
        
        ProfileStatistics::ProfileStatistics() 
            : mCallCount(0), mTotalTimeMs(0.0), mMinTimeMs(0.0),
              mMaxTimeMs(0.0), mAverageTimeMs(0.0), mPercentageOfTotal(0.0) {}
        
        Profiler& Profiler::GetInstance() {
            static Profiler sInstance;
            return sInstance;
        }
        
        Profiler::Profiler() : mIsActive(false) {}
        
        void Profiler::StartSession(const std::string& name) {
            std::lock_guard<std::mutex> lock(mMutex);
            mSessionName = name;
            mIsActive = true;
            mRootSample = ProfileSample();
            mRootSample.mName = "Root";
            mRootSample.mStartTime = std::chrono::high_resolution_clock::now();
            mRootSample.mParent = nullptr;
            mSampleStack.push(&mRootSample);
            mMainThreadId = std::this_thread::get_id();
        }
        
        void Profiler::EndSession() {
            std::lock_guard<std::mutex> lock(mMutex);
            if (!mIsActive) return;
            
            mRootSample.mEndTime = std::chrono::high_resolution_clock::now();
            mIsActive = false;
            mSampleStack = std::stack<ProfileSample*>();
        }
        
        void Profiler::BeginSample(const std::string& name) {
            std::lock_guard<std::mutex> lock(mMutex);
            if (!mIsActive) return;
            
            ProfileSample sample;
            sample.mName = name;
            sample.mThreadId = std::this_thread::get_id();
            sample.mStartTime = std::chrono::high_resolution_clock::now();
            sample.mParent = mSampleStack.top();
            
            mSampleStack.top()->mChildren.push_back(sample);
            mSampleStack.push(&mSampleStack.top()->mChildren.back());
        }
        
        void Profiler::EndSample() {
            std::lock_guard<std::mutex> lock(mMutex);
            if (!mIsActive || mSampleStack.empty()) return;
            
            mSampleStack.top()->mEndTime = std::chrono::high_resolution_clock::now();
            mSampleStack.pop();
        }
        
        const ProfileSample& Profiler::GetRootSample() const { 
            return mRootSample; 
        }
        
        std::vector<ProfileStatistics> Profiler::GetStatistics() const {
            std::lock_guard<std::mutex> lock(mMutex);
            std::map<std::string, ProfileStatistics> statsMap;
            
            double totalTime = mRootSample.DurationMs();
            CollectStatistics(mRootSample, statsMap);
            
            std::vector<ProfileStatistics> result;
            for (auto& pair : statsMap) {
                pair.second.mAverageTimeMs = pair.second.mTotalTimeMs / pair.second.mCallCount;
                pair.second.mPercentageOfTotal = (pair.second.mTotalTimeMs / totalTime) * 100.0;
                result.push_back(pair.second);
            }
            
            // Trier par temps total décroissant
            std::sort(result.begin(), result.end(),
                [](const ProfileStatistics& a, const ProfileStatistics& b) {
                    return a.mTotalTimeMs > b.mTotalTimeMs;
                });
            
            return result;
        }
        
        void Profiler::GenerateFlameGraph(const std::string& outputFile) {
            auto stats = GetStatistics();
            std::ofstream file(outputFile);
            if (!file.is_open()) return;
            
            file << "{\n";
            file << "  \"flamegraph\": {\n";
            file << "    \"name\": \"" << mSessionName << "\",\n";
            file << "    \"value\": " << mRootSample.DurationMs() << ",\n";
            file << "    \"children\": [\n";
            GenerateFlameGraphJSON(mRootSample, file, 1);
            file << "    ]\n";
            file << "  }\n";
            file << "}\n";
        }
        
        void Profiler::GenerateCallGraph(const std::string& outputFile) {
            auto stats = GetStatistics();
            std::ofstream file(outputFile);
            if (!file.is_open()) return;
            
            file << "digraph callgraph {\n";
            file << "  node [shape=box, style=filled, fillcolor=lightblue];\n";
            
            // Générer les nœuds
            for (const auto& stat : stats) {
                file << "  \"" << stat.mFunctionName << "\" [label=\""
                    << stat.mFunctionName << "\\n"
                    << std::fixed << std::setprecision(2)
                    << stat.mAverageTimeMs << "ms avg\\n"
                    << stat.mCallCount << " calls\"];\n";
            }
            
            // Générer les arêtes (simplifié)
            file << "  // Call relationships would be added here\n";
            file << "}\n";
        }
        
        void Profiler::CollectStatistics(const ProfileSample& sample,
                                       std::map<std::string, ProfileStatistics>& statsMap) const {
            auto it = statsMap.find(sample.mName);
            if (it == statsMap.end()) {
                ProfileStatistics stat;
                stat.mFunctionName = sample.mName;
                stat.mCallCount = 1;
                stat.mTotalTimeMs = sample.DurationMs();
                stat.mMinTimeMs = sample.DurationMs();
                stat.mMaxTimeMs = sample.DurationMs();
                statsMap[sample.mName] = stat;
            } else {
                it->second.mCallCount++;
                it->second.mTotalTimeMs += sample.DurationMs();
                it->second.mMinTimeMs = std::min(it->second.mMinTimeMs, sample.DurationMs());
                it->second.mMaxTimeMs = std::max(it->second.mMaxTimeMs, sample.DurationMs());
            }
            
            for (const auto& child : sample.mChildren) {
                CollectStatistics(child, statsMap);
            }
        }
        
        void Profiler::GenerateFlameGraphJSON(const ProfileSample& sample, 
                                            std::ofstream& file, 
                                            int depth) const {
            file << "      {\n";
            file << "        \"name\": \"" << sample.mName << "\",\n";
            file << "        \"value\": " << sample.DurationMs() << ",\n";
            
            if (!sample.mChildren.empty()) {
                file << "        \"children\": [\n";
                for (size_t i = 0; i < sample.mChildren.size(); ++i) {
                    GenerateFlameGraphJSON(sample.mChildren[i], file, depth + 1);
                    if (i < sample.mChildren.size() - 1) {
                        file << ",\n";
                    }
                }
                file << "        ]\n";
            } else {
                file << "        \"children\": []\n";
            }
            
            file << "      }";
        }
    }
}