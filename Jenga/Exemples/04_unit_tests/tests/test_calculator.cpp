#include <Unitest/Unitest.h>
#include <Unitest/TestMacro.h>
#include "calculator.h"

TEST_CASE(Calculator, Add) {
    ASSERT_EQUAL(5, add(2, 3));
}

TEST_CASE(Calculator, Sub) {
    ASSERT_EQUAL(1, sub(3, 2));
}
