#include "TestAssert.h"

namespace nkentseu
{
    namespace test
    {
        // Définition des variables statiques
        TestCase* TestAssert::sCurrentTest = nullptr;
        bool TestAssert::sStopOnFailure = false;
    } // namespace test
    
} // namespace nkentseu
