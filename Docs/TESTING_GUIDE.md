# Unit Testing Guide - Nken Build System

## Overview

Nken provides integrated support for the **Unitest** testing framework with automatic main injection, test discovery, and command-line configuration.

## Table of Contents
1. [Basic Test Setup](#basic-test-setup)
2. [Test Configuration](#test-configuration)
3. [Test Command-Line Options](#test-command-line-options)
4. [Auto-Main Injection](#auto-main-injection)
5. [Complete Example](#complete-example)

---

## Basic Test Setup

### 1. Create Test Project

```python
with workspace("MyApp"):
    configurations(["Debug", "Release"])
    
    # Main application
    with project("MyApp"):
        consoleapp()
        language("C++")
        
        files(["src/**.cpp"])
        includedirs(["include"])
        
        # Your main file
        files(["src/main.cpp"])
    
    # Test project
    with test("MyAppTests"):
        language("C++")
        
        location(".")  # Default: workspace directory
        
        # Specify test files
        testfiles([
            "tests/**.cpp",
            "tests/**.h"
        ])
        
        # Exclude the application's main file
        testmainfile("src/main.cpp")
        
        # Include application sources (without main)
        files(["src/**.cpp"])
        excludefiles(["!src/main.cpp"])  # Exclude main
        
        includedirs([
            "include",
            "%{wks.location}/Unitest/src"  # Unitest headers
        ])
        
        dependson(["Unitest"])  # Link with test framework
```

### 2. Project Structure

```
MyApp/
├── src/
│   ├── main.cpp          # Application entry point
│   ├── Calculator.cpp
│   └── Calculator.h
├── tests/
│   ├── CalculatorTests.cpp
│   └── MathTests.cpp
├── include/
└── myapp.nken
```

---

## Test Configuration

### Test Options

Configure test runner behavior:

```python
with test("MyTests"):
    # Test configuration
    testoptions([
        "--verbose",           # Verbose output
        "--filter=Math*",      # Run tests matching pattern
        "--parallel",          # Run in parallel
        "--stop-on-failure"    # Stop on first failure
    ])
```

### Available Test Options

| Option | Description |
|--------|-------------|
| `--verbose`, `-v` | Verbose output |
| `--quiet`, `-q` | Quiet output |
| `--stop-on-failure`, `-f` | Stop on first failure |
| `--no-colors` | Disable colored output |
| `--no-progress` | Disable progress bar |
| `--debug` | Enable debug mode |
| `--filter=PATTERN` | Run tests matching pattern |
| `--exclude=PATTERN` | Exclude tests matching pattern |
| `--parallel[=N]` | Run tests in parallel (N threads) |
| `--repeat=N` | Repeat tests N times |
| `--report=FILE` | Generate report file |

---

## Auto-Main Injection

Nken automatically injects a test main file, so you don't need to write one.

### How It Works

1. **Specify Test Main Template** (Optional)

```python
with test("MyTests"):
    # Use built-in template (default)
    # testmaintemplate("")  # Uses Unitest/AutoMainTemplate/test_main.cpp
    
    # OR use custom template
    testmaintemplate("custom_test_main.cpp")
```

2. **Built-in Template** (`Unitest/AutoMainTemplate/test_main.cpp`)

```cpp
#include "Unitest/Unitest.h"

// Auto-main for unit tests
#define UNIT_TEST_AUTO_DEFINE_MAIN
#include "Unitest/AutoMain.h"
```

3. **AutoMain.h** expands to:

```cpp
int main(int argc, char** argv) {
    return nkentseu::test::RunUnitTests(argc, argv);
}
```

### Custom Test Main

If you need custom initialization:

```cpp
// custom_test_main.cpp
#include "Unitest/Unitest.h"

int main(int argc, char** argv) {
    // Custom initialization
    InitializeMyLibrary();
    
    // Configure tests
    nkentseu::test::TestConfiguration config;
    config.mVerboseOutput = true;
    config.mUseColors = true;
    
    // Run tests
    int result = nkentseu::test::RunUnitTests(config);
    
    // Cleanup
    ShutdownMyLibrary();
    
    return result;
}
```

Then use it:

```python
with test("MyTests"):
    testmaintemplate("custom_test_main.cpp")
```

---

## Complete Example

### Project Configuration (myapp.nken)

```python
with workspace("CalculatorApp"):
    configurations(["Debug", "Release"])
    platforms(["Windows", "Linux", "MacOS"])
    
    with toolchain("default", "g++"):
        pass
    
    # ========================================================================
    # Unitest Framework
    # ========================================================================
    with project("Unitest"):
        staticlib()
        language("C++")
        cppdialect("C++20")
        
        location(".")
        
        files([
            "Unitest/src/**.cpp",
            "Unitest/src/**.h"
        ])
        
        includedirs(["Unitest/src"])
        
        targetdir("%{wks.location}/Build/Lib/%{cfg.buildcfg}")
    
    # ========================================================================
    # Calculator Library
    # ========================================================================
    with project("Calculator"):
        staticlib()
        language("C++")
        cppdialect("C++20")
        
        location(".")
        
        files([
            "Calculator/src/**.cpp",
            "Calculator/src/**.h"
        ])
        
        includedirs(["Calculator/include"])
        
        targetdir("%{wks.location}/Build/Lib/%{cfg.buildcfg}")
        
        with filter("configurations:Debug"):
            defines(["DEBUG"])
            optimize("Off")
            symbols("On")
    
    # ========================================================================
    # Calculator Application (with main)
    # ========================================================================
    with project("CalculatorApp"):
        consoleapp()
        language("C++")
        cppdialect("C++20")
        
        location(".")
        
        files([
            "App/src/main.cpp",
            "App/src/**.cpp",
            "App/src/**.h"
        ])
        
        includedirs([
            "App/include",
            "%{Calculator.location}/Calculator/include"
        ])
        
        dependson(["Calculator"])
        
        targetdir("%{wks.location}/Build/Bin/%{cfg.buildcfg}")
    
    # ========================================================================
    # Calculator Tests
    # ========================================================================
    with test("CalculatorTests"):
        language("C++")
        cppdialect("C++20")
        
        location(".")
        
        # Test files
        testfiles([
            "Tests/**.cpp",
            "Tests/**.h"
        ])
        
        # Exclude app's main from test build
        testmainfile("App/src/main.cpp")
        
        # Include application sources (except main)
        files([
            "App/src/**.cpp",
            "App/src/**.h"
        ])
        excludefiles(["!App/src/main.cpp"])
        
        includedirs([
            "App/include",
            "%{Calculator.location}/Calculator/include",
            "%{Unitest.location}/Unitest/src"
        ])
        
        dependson(["Calculator", "Unitest"])
        
        targetdir("%{wks.location}/Build/Tests/%{cfg.buildcfg}")
        
        # Test configuration
        testoptions([
            "--verbose",
            "--parallel",
            "--report=test_results.xml"
        ])
        
        with filter("configurations:Debug"):
            defines(["DEBUG", "UNIT_TESTING"])
            optimize("Off")
            symbols("On")
```

### Test File (Tests/CalculatorTests.cpp)

```cpp
#include "Unitest/Unitest.h"
#include "Calculator/Calculator.h"

using namespace nkentseu::test;

TEST_CASE("Calculator", "Addition") {
    Calculator calc;
    ASSERT_EQUAL(calc.Add(2, 3), 5);
    ASSERT_EQUAL(calc.Add(-1, 1), 0);
    ASSERT_EQUAL(calc.Add(0, 0), 0);
}

TEST_CASE("Calculator", "Subtraction") {
    Calculator calc;
    ASSERT_EQUAL(calc.Subtract(5, 3), 2);
    ASSERT_EQUAL(calc.Subtract(1, 1), 0);
    ASSERT_EQUAL(calc.Subtract(0, 5), -5);
}

TEST_CASE("Calculator", "Multiplication") {
    Calculator calc;
    ASSERT_EQUAL(calc.Multiply(2, 3), 6);
    ASSERT_EQUAL(calc.Multiply(-2, 3), -6);
    ASSERT_EQUAL(calc.Multiply(0, 100), 0);
}

TEST_CASE("Calculator", "Division") {
    Calculator calc;
    ASSERT_EQUAL(calc.Divide(6, 3), 2);
    ASSERT_EQUAL(calc.Divide(5, 2), 2);
    ASSERT_THROWS(calc.Divide(1, 0), std::invalid_argument);
}
```

---

## Building and Running Tests

### Build Tests
```bash
# Build test project
nken build --project CalculatorTests

# Build all (including tests)
nken build
```

### Run Tests
```bash
# Run with default options
nken run --project CalculatorTests

# Run with specific options
nken run --project CalculatorTests -- --verbose --filter="Calculator*"

# Run in parallel
nken run --project CalculatorTests -- --parallel

# Generate report
nken run --project CalculatorTests -- --report=results.xml
```

### Output Example

```
╔══════════════════════════════════════════════════════════════════╗
║    ███╗   ██╗██╗  ██╗███████╗███╗   ██╗                            ║
║    Unit Test Runner                                                ║
╚══════════════════════════════════════════════════════════════════╝

Running 4 test(s) in parallel...

[============================] 100% (4/4)

✓ Calculator::Addition           (0.001s)
✓ Calculator::Subtraction        (0.001s)
✓ Calculator::Multiplication     (0.001s)
✓ Calculator::Division           (0.002s)

════════════════════════════════════════════════════════════════════
Test Results:
  Passed:  4
  Failed:  0
  Skipped: 0
  Total:   4
  Time:    0.004s
════════════════════════════════════════════════════════════════════

✓ All tests passed!
```

---

## Advanced Features

### 1. Test Fixtures

```cpp
class CalculatorFixture {
protected:
    Calculator calc;
    
    void SetUp() {
        // Setup before each test
        calc.Reset();
    }
    
    void TearDown() {
        // Cleanup after each test
    }
};

TEST_CASE_F(CalculatorFixture, "Calculator", "WithFixture") {
    ASSERT_EQUAL(calc.Add(1, 1), 2);
}
```

### 2. Parameterized Tests

```cpp
PARAMETERIZED_TEST("Calculator", "AddMany",
    (int, int, int),  // Parameter types
    {
        {1, 1, 2},
        {2, 3, 5},
        {-1, 1, 0},
        {0, 0, 0}
    })
{
    Calculator calc;
    auto [a, b, expected] = GetParam();
    ASSERT_EQUAL(calc.Add(a, b), expected);
}
```

### 3. Test Suites

```cpp
TEST_SUITE("MathOperations") {
    TEST_CASE("Addition") { /* ... */ }
    TEST_CASE("Subtraction") { /* ... */ }
}

TEST_SUITE("StringOperations") {
    TEST_CASE("Concatenation") { /* ... */ }
    TEST_CASE("Splitting") { /* ... */ }
}
```

---

## Best Practices

1. **Organize Tests**: Group related tests in test suites
2. **Use Fixtures**: Reuse setup/teardown code
3. **Test One Thing**: Each test should verify one behavior
4. **Descriptive Names**: Use clear, descriptive test names
5. **Fast Tests**: Keep tests fast (use mocking if needed)
6. **Parallel Safe**: Ensure tests can run in parallel
7. **Cleanup**: Always cleanup resources in teardown

---

## Integration with CI/CD

```bash
# Run tests and generate XML report
nken build --config Release
nken run --project Tests -- --report=junit.xml --no-colors

# Check exit code
if [ $? -eq 0 ]; then
    echo "Tests passed!"
else
    echo "Tests failed!"
    exit 1
fi
```

---

Happy Testing! 🧪
