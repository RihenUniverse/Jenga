#include <iostream>
#include <vector>
#include <algorithm>

// Fonction simple pour tester la compilation
int fibonacci(int n) {
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

int main() {
    std::cout << "==================================" << std::endl;
    std::cout << "Cross-compiled with Zig!" << std::endl;
    std::cout << "==================================" << std::endl;

    // Test STL
    std::vector<int> numbers = {5, 2, 8, 1, 9, 3, 7, 4, 6};
    std::sort(numbers.begin(), numbers.end());

    std::cout << "\nSorted numbers: ";
    for (int n : numbers) {
        std::cout << n << " ";
    }
    std::cout << std::endl;

    // Test récursion
    std::cout << "\nFibonacci sequence (first 10):" << std::endl;
    for (int i = 0; i < 10; i++) {
        std::cout << "F(" << i << ") = " << fibonacci(i) << std::endl;
    }

    std::cout << "\n==================================" << std::endl;
    std::cout << "All tests passed!" << std::endl;
    std::cout << "==================================" << std::endl;

    return 0;
}
