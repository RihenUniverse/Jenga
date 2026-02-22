#pragma once

// =============================================================================
// NkWindow.h — Header principal NkWindow v2
//
// Inclure uniquement ce fichier dans vos sources.
// NkMain.h uniquement dans le .cpp qui définit nkmain().
//
// Exemple d'usage complet :
//
//   #include <NKWindow/NkWindow.h>
//   #include <NKWindow/Core/NkMain.h>
//
//   int nkmain(const nkentseu::NkEntryState& state)
//   {
//       // 1. Init (crée EventImpl + GamepadSystem)
//       nkentseu::NkAppData app;
//       app.preferredRenderer = nkentseu::NkRendererApi::NK_SOFTWARE;
//       nkentseu::NkInitialise(app);
//
//       // 2. Fenêtre (pas d'EventImpl à passer)
//       nkentseu::NkWindowConfig cfg;
//       cfg.title = "Hello"; cfg.width = 800; cfg.height = 600;
//       nkentseu::Window window(cfg);
//
//       // 3. Safe Area (mobile : notch / home indicator)
//       auto insets = window.GetSafeAreaInsets();
//
//       // 4. Renderer
//       nkentseu::Renderer renderer(window);
//       renderer.SetBackgroundColor(0x1A1A2EFF);
//
//       // 5. Gamepad
//       auto& gp = nkentseu::NkGamepads();
//       gp.SetButtonCallback([](NkU32 idx, nkentseu::NkGamepadButton btn,
//                               nkentseu::NkButtonState st) { ... });
//
//       // 6. Boucle principale
//       auto& es = nkentseu::EventSystem::Instance();
//       while (window.IsOpen()) {
//           es.PollEvents();
//           gp.PollGamepads();
//
//           // Transformation 2D
//           nkentseu::NkTransform2D t;
//           t.position = {400, 300};
//           t.rotation += 1.f;
//           renderer.SetTransform(t);
//
//           renderer.BeginFrame();
//           renderer.FillRectTransformed({-50,-50}, 100, 100, 0xFF5733FF);
//           renderer.EndFrame();
//           renderer.Present();
//       }
//       nkentseu::NkClose();
//       return 0;
//   }
// =============================================================================

#include "Core/NkPlatformDetect.h"
#include "Core/NkTypes.h"
#include "Core/NkWindowConfig.h"
#include "Core/NkSurface.h"
#include "Core/NkSystem.h"
#include "Core/NkGamepadSystem.h"

#include "Core/Events/NkEventTypes.h"
#include "Core/Events/NkWindowEvents.h"
#include "Core/Events/NkKeyboardEvents.h"
#include "Core/Events/NkMouseEvents.h"
#include "Core/Events/NkTouchEvents.h"
#include "Core/Events/NkGamepadEvents.h"
#include "Core/Events/NkDropEvents.h"
#include "Core/Events/NkKeycodeMap.h"
#include "Core/NkEvent.h"
#include "Core/NkTypedEvents.h"

#include "Core/NkWindow.h"
#include "Core/NkEventSystem.h"
#include "Core/NkRenderer.h"
#include "Core/NkCamera2D.h"

// Système de capture caméra physique
#include "Core/Camera/NkCameraSystem.h"
#include "Core/Camera/NkCameraTypes.h"
#include "Core/NkDialogs.h"
#include "Core/NkEntry.h"
