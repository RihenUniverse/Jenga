// -----------------------------------------------------------------------------
// FICHIER: Core\Nkentseu\src\Nkentseu\Time\NkProfiler.cpp
// DESCRIPTION: Performance profiling implementation
// AUTEUR: Rihen
// DATE: 2026-02-10
// -----------------------------------------------------------------------------

#include "NkProfiler.h"
#include <cstdio>
#include <limits>

namespace nkentseu {
    namespace entseu {
        
        // Static members
        core::NkHashMap<core::NkString, NkProfileResult> NkProfiler::sResults;
        core::NkHashMap<core::NkString, NkProfiler::ProfileSession> NkProfiler::sActiveSessions;
        bool NkProfiler::sIsEnabled = true;
        
        NkProfileResult::NkProfileResult()
            : Name()
            , Duration(NkDuration::Zero())
            , CallCount(0)
            , MinDuration(NkDuration::Max())
            , MaxDuration(NkDuration::Zero())
            , AvgDuration(NkDuration::Zero())
            , TotalDuration(NkDuration::Zero()) {
        }
        
        NkProfileResult::NkProfileResult(const char* name)
            : Name(name)
            , Duration(NkDuration::Zero())
            , CallCount(0)
            , MinDuration(NkDuration::Max())
            , MaxDuration(NkDuration::Zero())
            , AvgDuration(NkDuration::Zero())
            , TotalDuration(NkDuration::Zero()) {
        }
        
        void NkProfiler::Enable() {
            sIsEnabled = true;
        }
        
        void NkProfiler::Disable() {
            sIsEnabled = false;
        }
        
        bool NkProfiler::IsEnabled() {
            return sIsEnabled;
        }
        
        void NkProfiler::Clear() {
            sResults.Clear();
            sActiveSessions.Clear();
        }
        
        void NkProfiler::Reset() {
            Clear();
        }
        
        void NkProfiler::BeginProfile(const char* name) {
            if (!sIsEnabled) return;
            
            ProfileSession session(name);
            sActiveSessions[core::NkString(name)] = session;
        }
        
        void NkProfiler::EndProfile(const char* name) {
            if (!sIsEnabled) return;
            
            core::NkString key(name);
            ProfileSession* session = sActiveSessions.Find(key);
            
            if (!session) return;
            
            session->Stopwatch.Stop();
            NkDuration elapsed = session->Stopwatch.GetElapsed();
            
            // Update or create result
            NkProfileResult* result = sResults.Find(key);
            if (!result) {
                NkProfileResult newResult(name);
                sResults[key] = newResult;
                result = sResults.Find(key);
            }
            
            if (result) {
                result->CallCount++;
                result->TotalDuration += elapsed;
                
                if (elapsed < result->MinDuration) {
                    result->MinDuration = elapsed;
                }
                if (elapsed > result->MaxDuration) {
                    result->MaxDuration = elapsed;
                }
                
                result->AvgDuration = result->TotalDuration / static_cast<f64>(result->CallCount);
                result->Duration = elapsed;
            }
            
            sActiveSessions.Erase(key);
        }
        
        NkProfileResult NkProfiler::GetResult(const char* name) {
            NkProfileResult* result = sResults.Find(core::NkString(name));
            if (result) {
                return *result;
            }
            return NkProfileResult(name);
        }
        
        core::NkVector<NkProfileResult> NkProfiler::GetAllResults() {
            core::NkVector<NkProfileResult> results;
            
            // Note: This is simplified - proper iteration would need HashMap iterator
            // For now, return empty vector
            // In real implementation, iterate through sResults
            
            return results;
        }
        
        void NkProfiler::PrintResults() {
            printf("\n========== PROFILER RESULTS ==========\n");
            printf("%-30s %10s %10s %10s %10s %8s\n",
                   "Name", "Total", "Avg", "Min", "Max", "Calls");
            printf("--------------------------------------------------------------\n");
            
            // Note: Simplified - would need proper iteration
            // For demonstration, print a message
            printf("Total profiles: %zu\n", GetProfileCount());
            
            printf("======================================\n\n");
        }
        
        void NkProfiler::PrintResult(const char* name) {
            NkProfileResult result = GetResult(name);
            
            if (result.CallCount > 0) {
                printf("\nProfile: %s\n", name);
                printf("  Calls:   %zu\n", result.CallCount);
                printf("  Total:   %s\n", result.TotalDuration.ToString().CStr());
                printf("  Average: %s\n", result.AvgDuration.ToString().CStr());
                printf("  Min:     %s\n", result.MinDuration.ToString().CStr());
                printf("  Max:     %s\n", result.MaxDuration.ToString().CStr());
            } else {
                printf("\nNo profiling data for: %s\n", name);
            }
        }
        
        core::NkString NkProfiler::GetResultsString() {
            core::NkString result = "=== Profiler Results ===\n";
            
            char buffer[256];
            snprintf(buffer, sizeof(buffer), "Total profiles: %zu\n", GetProfileCount());
            result += buffer;
            
            snprintf(buffer, sizeof(buffer), "Total time: %s\n", GetTotalTime().ToString().CStr());
            result += buffer;
            
            return result;
        }
        
        usize NkProfiler::GetProfileCount() {
            return sResults.Size();
        }
        
        NkDuration NkProfiler::GetTotalTime() {
            NkDuration total = NkDuration::Zero();
            
            // Note: Would need proper iteration
            
            return total;
        }
        
        NkProfileResult NkProfiler::GetSlowest() {
            NkProfileResult slowest;
            NkDuration maxTime = NkDuration::Zero();
            
            // Note: Would need proper iteration to find slowest
            
            return slowest;
        }
        
        NkProfileResult NkProfiler::GetFastest() {
            NkProfileResult fastest;
            NkDuration minTime = NkDuration::Max();
            
            // Note: Would need proper iteration to find fastest
            
            return fastest;
        }
        
        // NkScopedProfiler
        NkScopedProfiler::NkScopedProfiler(const char* name)
            : mName(name) {
            NkProfiler::BeginProfile(name);
        }
        
        NkScopedProfiler::~NkScopedProfiler() {
            NkProfiler::EndProfile(mName.CStr());
        }
        
    } // namespace entseu
} // namespace nkentseu

// ============================================================
// Copyright © 2024-2026 Rihen. All rights reserved.
// Proprietary License - Free to use and modify
//
// Generated by Rihen on 2026-02-05 22:26:13
// Creation Date: 2026-02-05 22:26:13
// ============================================================