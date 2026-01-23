#pragma once

// En-tête façade pour inclure facilement tout le framework

// Configuration
#include "Unitest/TestConfig.h"

// Données et structures
#include "Unitest/UnitTestData.h"

// Core du framework
#include "Unitest/TestCase.h"
#include "Unitest/TestAssert.h"
#include "Unitest/TestRunner.h"
#include "Unitest/TestReporter.h"
#include "Unitest/TestAggregator.h"
#include "Unitest/TestLauncher.h"

// Template implementation (must be after TestRunner is fully defined)
#include "Unitest/TestCaseRegistrar_impl.h"

// Macros pour les tests
#include "Unitest/TestMacro.h"