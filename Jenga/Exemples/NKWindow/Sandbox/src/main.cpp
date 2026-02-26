// ============================================================================
// Sandbox/src/main.cpp
// ============================================================================

#include "NKWindow/NkWindow.h"
#include "NKWindow/Core/NkMain.h"
#include "NKWindow/Time/NkClock.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <memory>

#ifndef NK_SANDBOX_RENDERER_API
#define NK_SANDBOX_RENDERER_API nkentseu::NkRendererApi::NK_SOFTWARE
#endif

/**
 * @brief Internal anonymous namespace.
 */
namespace {
using namespace nkentseu;

float ClampUnit(float v) {
	if (v < 0.f) {
		return 0.f;
	}
	if (v > 1.f) {
		return 1.f;
	}
	return v;
}

/// @brief Convert normalized RGB wave values to packed RGBA.
NkU32 PackWaveColor(float r, float g, float b) {
	return NkRenderer::PackColor(static_cast<NkU8>(ClampUnit(r) * 255.f), static_cast<NkU8>(ClampUnit(g) * 255.f),
								 static_cast<NkU8>(ClampUnit(b) * 255.f), 255);
}

/// @brief Draw a time-animated plasma effect directly via SetPixel.
void DrawPlasma(NkRenderer &renderer, NkU32 width, NkU32 height, float timeSeconds, const NkVec2f &phaseOffset,
				float saturationBoost) {
	if (width == 0 || height == 0) {
		return;
	}

	const NkU32 block = (width * height > 1280u * 720u) ? 2u : 1u;
	const float invW = 1.f / static_cast<float>(width);
	const float invH = 1.f / static_cast<float>(height);

	for (NkU32 y = 0; y < height; y += block) {
		const float fy = (static_cast<float>(y) * invH) - 0.5f;
		for (NkU32 x = 0; x < width; x += block) {
			const float fx = (static_cast<float>(x) * invW) - 0.5f;
			const float radial = std::sqrt((fx * fx) + (fy * fy));

			const float waveA = std::sin((fx + phaseOffset.x) * 13.5f + timeSeconds * 1.7f);
			const float waveB = std::sin((fy + phaseOffset.y) * 11.0f - timeSeconds * 1.3f);
			const float waveC = std::sin((radial * 24.0f) - timeSeconds * 2.1f);
			const float mix = (waveA + waveB + waveC) * 0.33333334f;

			float r = 0.5f + 0.5f * std::sin(6.2831853f * (mix + 0.00f));
			float g = 0.5f + 0.5f * std::sin(6.2831853f * (mix + 0.33f));
			float b = 0.5f + 0.5f * std::sin(6.2831853f * (mix + 0.66f));

			// Increase saturation slightly to make the demo more vivid.
			r = ClampUnit((r - 0.5f) * saturationBoost + 0.5f);
			g = ClampUnit((g - 0.5f) * saturationBoost + 0.5f);
			b = ClampUnit((b - 0.5f) * saturationBoost + 0.5f);

			const NkU32 color = PackWaveColor(r, g, b);
			for (NkU32 by = 0; by < block && (y + by) < height; ++by) {
				for (NkU32 bx = 0; bx < block && (x + bx) < width; ++bx) {
					renderer.SetPixel(static_cast<NkI32>(x + bx), static_cast<NkI32>(y + by), color);
				}
			}
		}
	}
}

} // namespace

/**
 * @brief Sandbox entry point demonstrating direct pixel rendering.
 *
 * The demo creates a window, optionally creates a renderer backend,
 * polls keyboard/gamepad events, and renders a procedural plasma frame.
 */
int nkmain(const nkentseu::NkEntryState & /*state*/) {
	using namespace nkentseu;

	NkAppData app;
	app.appName = "NkWindow Sandbox";
	app.preferredRenderer = NK_SANDBOX_RENDERER_API;

	if (!NkInitialise(app)) {
		return -1;
	}

	NkWindowConfig cfg;
	cfg.title = "NkWindow Sandbox";
	cfg.width = 1280;
	cfg.height = 720;
	cfg.centered = true;
	cfg.resizable = true;
	cfg.dropEnabled = true;

	nkentseu::Window window(cfg);
	if (!window.IsOpen()) {
		std::fprintf(stderr, "[Sandbox] Window creation failed: %s\n", window.GetLastError().ToString().c_str());
		NkClose();
		return -2;
	}

	NkRendererConfig rcfg;
	rcfg.api = NK_SANDBOX_RENDERER_API;
	rcfg.autoResizeFramebuffer = true;

	std::unique_ptr<NkRenderer> renderer;
	if (rcfg.api != NkRendererApi::NK_NONE) {
		renderer = std::make_unique<NkRenderer>();
		if (!renderer->Create(window, rcfg)) {
			NkClose();
			return -3;
		}
	}

	auto &eventSystem = EventSystem::Instance();
	auto &gamepads = NkGamepads();

	bool running = true;
	bool neonMode = false;
	float saturationBoost = 1.15f;
	NkVec2f phaseOffset{0.f, 0.f};
	float timeSeconds = 0.f;

	NkClock::TimePoint previousTick = NkClock::Now();

	while (running) {
		// Gamepad poll injects NK_GAMEPAD_* events into EventSystem.
		gamepads.PollGamepads();

		while (NkEvent *event = eventSystem.PollEvent()) {
			if (event->type == NkEventType::NK_WINDOW_CLOSE || event->type == NkEventType::NK_WINDOW_DESTROY) {
				window.Close();
				running = false;
				break;
			}

			if (auto *resize = event->As<NkWindowResizeEvent>()) {
				if (renderer) {
					renderer->Resize(resize->GetWidth(), resize->GetHeight());
				}
				continue;
			}

			if (auto *key = event->As<NkKeyEvent>()) {
				if (!key->IsPress()) {
					continue;
				}

				if (key->GetKey() == NkKey::NK_ESCAPE) {
					window.Close();
					running = false;
					break;
				}

				if (key->GetKey() == NkKey::NK_F11) {
					window.SetFullscreen(!window.GetConfig().fullscreen);
				}
				if (key->GetKey() == NkKey::NK_SPACE) {
					neonMode = !neonMode;
				}
			}

			if (auto *axisEvent = event->As<NkGamepadAxisEvent>()) {
				const float value = axisEvent->GetValue();
				switch (axisEvent->GetAxis()) {
					case NkGamepadAxis::NK_GP_AXIS_LX:
						phaseOffset.x += value * 0.02f;
						break;
					case NkGamepadAxis::NK_GP_AXIS_LY:
						phaseOffset.y += value * 0.02f;
						break;
					case NkGamepadAxis::NK_GP_AXIS_RT:
						saturationBoost = 1.0f + (ClampUnit(value) * 0.8f);
						break;
					default:
						break;
				}
			}

			if (auto *buttonEvent = event->As<NkGamepadButtonPressEvent>()) {
				if (buttonEvent->GetButton() == NkGamepadButton::NK_GP_SOUTH) {
					neonMode = !neonMode;
					gamepads.Rumble(buttonEvent->GetGamepadIndex(), 0.35f, 0.45f, 0.f, 0.f, 40);
				}
			}
		}

		if (!running || !window.IsOpen()) {
			break;
		}

		const NkClock::TimePoint frameStart = NkClock::Now();
		NkDuration delta = NkClock::ToNkDuration(frameStart - previousTick);
		previousTick = frameStart;

		float dt = static_cast<float>(delta.ToSeconds());
		if (dt <= 0.f || dt > 0.25f) {
			dt = 1.f / 60.f;
		}

		timeSeconds += dt * (neonMode ? 1.8f : 1.0f);

		if (renderer) {
			renderer->BeginFrame(NkRenderer::PackColor(8, 10, 18, 255));

			const NkFramebufferInfo &fb = renderer->GetFramebufferInfo();
			const NkU32 width = fb.width ? fb.width : window.GetSize().x;
			const NkU32 height = fb.height ? fb.height : window.GetSize().y;

			DrawPlasma(*renderer, width, height, timeSeconds, phaseOffset, saturationBoost);

			renderer->EndFrame();
			renderer->Present();
		}

		const NkDuration frameBudget = NkDuration::FromMilliseconds(static_cast<NkI64>(16));
		const NkDuration elapsed = NkClock::ElapsedSince(frameStart);
		if (elapsed < frameBudget) {
			NkClock::Sleep(frameBudget - elapsed);
		} else {
			NkClock::YieldThread();
		}
	}

	if (renderer) {
		renderer->Shutdown();
	}

	NkClose();
	return 0;
}
