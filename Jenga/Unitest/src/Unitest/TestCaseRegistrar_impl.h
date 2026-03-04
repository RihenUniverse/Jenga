#pragma once
// This file must be included AFTER both TestCase.h and TestRunner.h are fully defined

namespace nkentseu {
    namespace test {
        namespace detail {
            // Implementation of TestCaseRegistrar::RegisterTestCase
            // This must be a separate template to avoid circular dependency
            template<typename T>
            void TestCaseRegistrar<T>::RegisterTestCase() {
                // Use fully qualified name to access TestRunner from parent namespace
                nkentseu::test::TestRunner::GetInstance().AddTestCase(mTestName, []() {
                    return std::make_unique<T>();
                });
            }

            // RegisterAll implementation is in TestCase.cpp to ensure it's compiled
        }
    }
}
