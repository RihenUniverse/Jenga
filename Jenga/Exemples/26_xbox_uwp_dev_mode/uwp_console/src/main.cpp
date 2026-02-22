#include <iostream>
#include "UwpStaticMath.h"
#include "UwpSharedMath.h"

int main() {
    const int add = UwpStaticAdd(2, 3);
    const int mul = UwpStaticMul(4, 5);
    const int sub = UwpSharedSub(10, 3);
    const int div2 = UwpSharedDiv2(8);

    std::cout << "UwpConsoleApp" << std::endl;
    std::cout << "add=" << add << " mul=" << mul << " sub=" << sub << " div2=" << div2 << std::endl;
    return 0;
}
