// -----------------------------------------------------------------------------
// FICHIER: Core\Nkentseu\src\Nkentseu\Time\NkTimestamp.cpp
// DESCRIPTION: Timestamp implementation
// AUTEUR: Rihen
// DATE: 2026-02-10
// -----------------------------------------------------------------------------

#include "NkTimestamp.h"
#include <ctime>
#include <cstdio>
#include <cstring>

#ifdef _WIN32
    #include <windows.h>
#else
    #include <sys/time.h>
#endif

namespace nkentseu {
    namespace entseu {
        
        NkDateTime::NkDateTime()
            : Year(1970), Month(1), Day(1)
            , Hour(0), Minute(0), Second(0), Millisecond(0)
            , DayOfWeek(4) {  // Thursday (01/01/1970)
        }
        
        NkTimestamp::NkTimestamp() : mUnixTimestamp(0) {
        }
        
        NkTimestamp::NkTimestamp(i64 unixTimestamp) : mUnixTimestamp(unixTimestamp) {
        }
        
        NkTimestamp::NkTimestamp(const NkTimestamp& other) : mUnixTimestamp(other.mUnixTimestamp) {
        }
        
        NkTimestamp& NkTimestamp::operator=(const NkTimestamp& other) {
            mUnixTimestamp = other.mUnixTimestamp;
            return *this;
        }
        
        NkTimestamp NkTimestamp::Now() {
            #ifdef _WIN32
            FILETIME ft;
            GetSystemTimeAsFileTime(&ft);
            
            ULARGE_INTEGER ull;
            ull.LowPart = ft.dwLowDateTime;
            ull.HighPart = ft.dwHighDateTime;
            
            // Convert to milliseconds since Unix epoch
            i64 ms = (ull.QuadPart / 10000) - 11644473600000LL;
            return NkTimestamp(ms);
            #else
            struct timeval tv;
            gettimeofday(&tv, nullptr);
            i64 ms = static_cast<i64>(tv.tv_sec) * 1000 + tv.tv_usec / 1000;
            return NkTimestamp(ms);
            #endif
        }
        
        NkTimestamp NkTimestamp::FromUnixTimestamp(i64 milliseconds) {
            return NkTimestamp(milliseconds);
        }
        
        NkTimestamp NkTimestamp::FromDateTime(const NkDateTime& dt) {
            struct tm timeinfo = {0};
            timeinfo.tm_year = dt.Year - 1900;
            timeinfo.tm_mon = dt.Month - 1;
            timeinfo.tm_mday = dt.Day;
            timeinfo.tm_hour = dt.Hour;
            timeinfo.tm_min = dt.Minute;
            timeinfo.tm_sec = dt.Second;
            
            time_t t = mktime(&timeinfo);
            i64 ms = static_cast<i64>(t) * 1000 + dt.Millisecond;
            return NkTimestamp(ms);
        }
        
        NkTimestamp NkTimestamp::FromString(const char* str) {
            // Parse ISO 8601: "YYYY-MM-DD HH:MM:SS"
            NkDateTime dt;
            if (sscanf(str, "%d-%d-%d %d:%d:%d",
                      &dt.Year, &dt.Month, &dt.Day,
                      &dt.Hour, &dt.Minute, &dt.Second) == 6) {
                return FromDateTime(dt);
            }
            return NkTimestamp();
        }
        
        i64 NkTimestamp::ToUnixTimestamp() const {
            return mUnixTimestamp;
        }
        
        NkDateTime NkTimestamp::ToDateTime() const {
            NkDateTime dt;
            
            time_t seconds = static_cast<time_t>(mUnixTimestamp / 1000);
            dt.Millisecond = static_cast<i32>(mUnixTimestamp % 1000);
            
            #ifdef _WIN32
            struct tm timeinfo;
            localtime_s(&timeinfo, &seconds);
            #else
            struct tm timeinfo;
            localtime_r(&seconds, &timeinfo);
            #endif
            
            dt.Year = timeinfo.tm_year + 1900;
            dt.Month = timeinfo.tm_mon + 1;
            dt.Day = timeinfo.tm_mday;
            dt.Hour = timeinfo.tm_hour;
            dt.Minute = timeinfo.tm_min;
            dt.Second = timeinfo.tm_sec;
            dt.DayOfWeek = timeinfo.tm_wday;
            
            return dt;
        }
        
        core::NkString NkTimestamp::ToString() const {
            NkDateTime dt = ToDateTime();
            char buffer[64];
            snprintf(buffer, sizeof(buffer), "%04d-%02d-%02d %02d:%02d:%02d",
                    dt.Year, dt.Month, dt.Day, dt.Hour, dt.Minute, dt.Second);
            return core::NkString(buffer);
        }
        
        core::NkString NkTimestamp::ToStringISO() const {
            NkDateTime dt = ToDateTime();
            char buffer[64];
            snprintf(buffer, sizeof(buffer), "%04d-%02d-%02dT%02d:%02d:%02d.%03dZ",
                    dt.Year, dt.Month, dt.Day, dt.Hour, dt.Minute, dt.Second, dt.Millisecond);
            return core::NkString(buffer);
        }
        
        core::NkString NkTimestamp::ToStringDate() const {
            NkDateTime dt = ToDateTime();
            char buffer[32];
            snprintf(buffer, sizeof(buffer), "%04d-%02d-%02d",
                    dt.Year, dt.Month, dt.Day);
            return core::NkString(buffer);
        }
        
        core::NkString NkTimestamp::ToStringTime() const {
            NkDateTime dt = ToDateTime();
            char buffer[32];
            snprintf(buffer, sizeof(buffer), "%02d:%02d:%02d",
                    dt.Hour, dt.Minute, dt.Second);
            return core::NkString(buffer);
        }
        
        NkTimestamp NkTimestamp::operator+(const NkDuration& duration) const {
            return NkTimestamp(mUnixTimestamp + duration.ToMilliseconds());
        }
        
        NkTimestamp NkTimestamp::operator-(const NkDuration& duration) const {
            return NkTimestamp(mUnixTimestamp - duration.ToMilliseconds());
        }
        
        NkDuration NkTimestamp::operator-(const NkTimestamp& other) const {
            return NkDuration::FromMilliseconds(mUnixTimestamp - other.mUnixTimestamp);
        }
        
        NkTimestamp& NkTimestamp::operator+=(const NkDuration& duration) {
            mUnixTimestamp += duration.ToMilliseconds();
            return *this;
        }
        
        NkTimestamp& NkTimestamp::operator-=(const NkDuration& duration) {
            mUnixTimestamp -= duration.ToMilliseconds();
            return *this;
        }
        
        bool NkTimestamp::operator==(const NkTimestamp& other) const {
            return mUnixTimestamp == other.mUnixTimestamp;
        }
        
        bool NkTimestamp::operator!=(const NkTimestamp& other) const {
            return mUnixTimestamp != other.mUnixTimestamp;
        }
        
        bool NkTimestamp::operator<(const NkTimestamp& other) const {
            return mUnixTimestamp < other.mUnixTimestamp;
        }
        
        bool NkTimestamp::operator<=(const NkTimestamp& other) const {
            return mUnixTimestamp <= other.mUnixTimestamp;
        }
        
        bool NkTimestamp::operator>(const NkTimestamp& other) const {
            return mUnixTimestamp > other.mUnixTimestamp;
        }
        
        bool NkTimestamp::operator>=(const NkTimestamp& other) const {
            return mUnixTimestamp >= other.mUnixTimestamp;
        }
        
        bool NkTimestamp::IsValid() const {
            return mUnixTimestamp >= 0;
        }
        
        i32 NkTimestamp::GetYear() const {
            return ToDateTime().Year;
        }
        
        i32 NkTimestamp::GetMonth() const {
            return ToDateTime().Month;
        }
        
        i32 NkTimestamp::GetDay() const {
            return ToDateTime().Day;
        }
        
        i32 NkTimestamp::GetHour() const {
            return ToDateTime().Hour;
        }
        
        i32 NkTimestamp::GetMinute() const {
            return ToDateTime().Minute;
        }
        
        i32 NkTimestamp::GetSecond() const {
            return ToDateTime().Second;
        }
        
        i32 NkTimestamp::GetDayOfWeek() const {
            return ToDateTime().DayOfWeek;
        }
        
        NkTimestamp NkTimestamp::AddYears(i32 years) const {
            NkDateTime dt = ToDateTime();
            dt.Year += years;
            return FromDateTime(dt);
        }
        
        NkTimestamp NkTimestamp::AddMonths(i32 months) const {
            NkDateTime dt = ToDateTime();
            dt.Month += months;
            while (dt.Month > 12) {
                dt.Month -= 12;
                dt.Year++;
            }
            while (dt.Month < 1) {
                dt.Month += 12;
                dt.Year--;
            }
            return FromDateTime(dt);
        }
        
        NkTimestamp NkTimestamp::AddDays(i32 days) const {
            return *this + NkDuration::FromDays(days);
        }
        
        NkTimestamp NkTimestamp::AddHours(i32 hours) const {
            return *this + NkDuration::FromHours(hours);
        }
        
        NkTimestamp NkTimestamp::AddMinutes(i32 minutes) const {
            return *this + NkDuration::FromMinutes(minutes);
        }
        
        NkTimestamp NkTimestamp::AddSeconds(i32 seconds) const {
            return *this + NkDuration::FromSeconds(seconds);
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