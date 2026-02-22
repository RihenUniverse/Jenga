#include <iostream>
#include "XboxStaticMath.h"
#include "XboxSharedMath.h"

int main() {
    const int add = XboxStaticAdd(2, 3);
    const int mul = XboxStaticMul(4, 5);
    const int sub = XboxSharedSub(10, 3);
    const int div2 = XboxSharedDiv2(8);

    std::cout << "XboxConsoleApp" << std::endl;
    std::cout << "add=" << add << " mul=" << mul << " sub=" << sub << " div2=" << div2 << std::endl;
    return 0;
}
