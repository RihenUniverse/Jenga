#pragma once

// =============================================================================
// NkDropEvents.h
// Données et classes d'événements Drag & Drop et système.
//
// Couvre :
//   NkDropEnterData         — objet entrant dans la fenêtre
//   NkDropOverData          — objet survolant la fenêtre
//   NkDropLeaveData         — objet quittant la fenêtre
//   NkDropFileData          — fichier(s) déposé(s)
//   NkDropTextData          — texte déposé
//   NkDropImageData         — image déposée
//   NkSystemPowerData       — événements alimentation
//   NkSystemLocaleData      — changement de locale
//   NkSystemDisplayData     — changement de configuration des moniteurs
//   NkSystemMemoryData      — pression mémoire (mobile)
//   NkCustomData            — événement utilisateur personnalisé
// =============================================================================

#include "NkEventTypes.h"
#include <string>
#include <vector>
#include <cstring>

/**
 * @brief Namespace nkentseu.
 */
namespace nkentseu {

// ===========================================================================
// NkDropEnterData — objet glissé entrant dans la fenêtre
// ===========================================================================

struct NkDropEnterData {
	static constexpr NkEventType TYPE = NkEventType::NK_DROP_ENTER;

	NkI32 x = 0, y = 0; ///< Position du curseur dans la zone client
	NkDropType dropType = NkDropType::NK_DROP_TYPE_UNKNOWN;

	// Résumé de ce qui est proposé (avant l'acceptation)
	NkU32 numFiles = 0;	   ///< Nombre de fichiers (si NK_DROP_TYPE_FILE)
	bool hasText = false;  ///< Contient du texte
	bool hasImage = false; ///< Contient une image

	std::string ToString() const {
		std::string s = "DropEnter(at " + std::to_string(x) + "," + std::to_string(y);
		if (numFiles)
			s += " files=" + std::to_string(numFiles);
		if (hasText)
			s += " text";
		if (hasImage)
			s += " image";
		s += ")";
		return s;
	}
};

// ===========================================================================
// NkDropOverData — survol en cours
// ===========================================================================

struct NkDropOverData {
	static constexpr NkEventType TYPE = NkEventType::NK_DROP_OVER;

	NkI32 x = 0, y = 0;
	NkDropType dropType = NkDropType::NK_DROP_TYPE_UNKNOWN;

	std::string ToString() const {
		return "DropOver(" + std::to_string(x) + "," + std::to_string(y) + ")";
	}
};

// ===========================================================================
// NkDropLeaveData — objet qui quitte la fenêtre
// ===========================================================================

struct NkDropLeaveData {
	static constexpr NkEventType TYPE = NkEventType::NK_DROP_LEAVE;
	std::string ToString() const {
		return "DropLeave";
	}
};

// ===========================================================================
// NkDropFileData — fichier(s) déposé(s)
// ===========================================================================

// ---------------------------------------------------------------------------
// NkDropFilePath — un chemin de fichier déposé (max 512 chars, UTF-8)
// ---------------------------------------------------------------------------

struct NkDropFilePath {
	char path[512] = {};
	NkDropFilePath() = default;
	explicit NkDropFilePath(const char *p) {
		strncpy(path, p, sizeof(path) - 1);
	}
	std::string ToString() const {
		return std::string(path);
	}
};

/**
 * @brief Struct NkDropFileData.
 */
struct NkDropFileData {
	static constexpr NkEventType TYPE = NkEventType::NK_DROP_FILE;

	NkI32 x = 0, y = 0; ///< Position de dépose dans la zone client

	// Chemins des fichiers déposés
	std::vector<std::string> paths;

	NkDropFileData() = default;

	void AddPath(const std::string &p) {
		paths.push_back(p);
	}
	NkU32 Count() const {
		return static_cast<NkU32>(paths.size());
	}

	std::string ToString() const {
		return "DropFile(" + std::to_string(Count()) + " file(s) at " + std::to_string(x) + "," + std::to_string(y) +
			   ")";
	}
};

// ===========================================================================
// NkDropTextData — texte déposé
// ===========================================================================

struct NkDropTextData {
	static constexpr NkEventType TYPE = NkEventType::NK_DROP_TEXT;

	NkI32 x = 0, y = 0;
	std::string text;	  ///< Texte en UTF-8
	std::string mimeType; ///< MIME type (ex : "text/plain", "text/html")

	std::string ToString() const {
		std::string preview = text.substr(0, 40);
		return "DropText(\"" + preview + (text.size() > 40 ? "..." : "") + "\")";
	}
};

// ===========================================================================
// NkDropImageData — image déposée
// ===========================================================================

struct NkDropImageData {
	static constexpr NkEventType TYPE = NkEventType::NK_DROP_IMAGE;

	NkI32 x = 0, y = 0;
	std::string sourceUri; ///< URI de la source (peut être un chemin fichier ou data URI)
	std::string mimeType;  ///< "image/png", "image/jpeg"…
	NkU32 width = 0;
	NkU32 height = 0;

	// Données brutes (si disponibles) — RGBA8
	std::vector<NkU8> pixels;

	bool HasPixels() const {
		return !pixels.empty();
	}

	std::string ToString() const {
		return "DropImage(" + std::to_string(width) + "x" + std::to_string(height) + " " + mimeType + ")";
	}
};

// ===========================================================================
// NkSystemPowerData — alimentation / mise en veille
// ===========================================================================

struct NkSystemPowerData {
	static constexpr NkEventType TYPE = NkEventType::NK_SYSTEM_POWER_SUSPEND;

	NkPowerState state = NkPowerState::NK_POWER_NORMAL;
	float batteryLevel = -1.f; ///< [0,1] ou -1 si branché / inconnu
	bool pluggedIn = false;

	NkSystemPowerData() = default;
	explicit NkSystemPowerData(NkPowerState s, float bl = -1.f, bool pi = false)
		: state(s), batteryLevel(bl), pluggedIn(pi) {
	}

	std::string ToString() const {
		const char *names[] = {"NORMAL", "LOW_BATTERY", "CRITICAL_BATTERY", "PLUGGED_IN", "SUSPENDED", "RESUMED"};
		NkU32 idx = static_cast<NkU32>(state);
		const char *n = (idx < 6) ? names[idx] : "UNKNOWN";
		return std::string("SystemPower(") + n + ")";
	}
};

// ===========================================================================
// NkSystemLocaleData — changement de langue / région
// ===========================================================================

struct NkSystemLocaleData {
	static constexpr NkEventType TYPE = NkEventType::NK_SYSTEM_LOCALE_CHANGE;

	char locale[32] = {}; ///< Ex : "fr_FR", "en_US", "ja_JP"
	char prevLocale[32] = {};

	NkSystemLocaleData() = default;
	NkSystemLocaleData(const char *loc, const char *prev = "") {
		strncpy(locale, loc, sizeof(locale) - 1);
		strncpy(prevLocale, prev, sizeof(prevLocale) - 1);
	}

	std::string ToString() const {
		return std::string("SystemLocale(") + prevLocale + " -> " + locale + ")";
	}
};

// ===========================================================================
// NkSystemDisplayData — moniteur ajouté / retiré / résolution changée
// ===========================================================================

struct NkSystemDisplayData {
	static constexpr NkEventType TYPE = NkEventType::NK_SYSTEM_DISPLAY_CHANGE;

	/**
	 * @brief Enumeration Change.
	 */
	enum class Change : NkU32 {
		Added,
		Removed,
		ResolutionChanged,
		OrientationChanged,
		DpiChanged
	} change = Change::ResolutionChanged;

	NkU32 displayIndex = 0;
	NkU32 width = 0;
	NkU32 height = 0;
	NkU32 refreshRate = 60;
	float dpiScale = 1.f;

	std::string ToString() const {
		return "SystemDisplay(#" + std::to_string(displayIndex) + " " + std::to_string(width) + "x" +
			   std::to_string(height) + ")";
	}
};

// ===========================================================================
// NkSystemMemoryData — pression mémoire (Android / iOS)
// ===========================================================================

struct NkSystemMemoryData {
	static constexpr NkEventType TYPE = NkEventType::NK_SYSTEM_LOW_MEMORY;

	enum class Level : NkU32 { Low, Moderate, Critical } level = Level::Low;

	NkU64 availableBytes = 0; ///< Mémoire disponible restante (0 = inconnu)

	std::string ToString() const {
		const char *lvl[] = {"LOW", "MODERATE", "CRITICAL"};
		return std::string("SystemMemory(") + lvl[static_cast<NkU32>(level)] + ")";
	}
};

// ===========================================================================
// NkCustomData — événement utilisateur
// ===========================================================================

static constexpr NkU32 NK_CUSTOM_DATA_MAX_BYTES = 128;

/**
 * @brief Struct NkCustomData.
 */
struct NkCustomData {
	static constexpr NkEventType TYPE = NkEventType::NK_CUSTOM;

	NkU32 customType = 0; ///< Identifiant libre défini par l'application
	NkU32 dataSize = 0;	  ///< Taille utile dans payload
	NkU8 payload[NK_CUSTOM_DATA_MAX_BYTES] = {};

	// Helpers pour stocker un pointeur (attention à la durée de vie)
	void *userPtr = nullptr;

	NkCustomData() = default;
	explicit NkCustomData(NkU32 type) : customType(type) {
	}

	template <typename T> void SetPayload(const T &value) {
		static_assert(sizeof(T) <= NK_CUSTOM_DATA_MAX_BYTES, "NkCustomData payload trop petit");
		std::memcpy(payload, &value, sizeof(T));
		dataSize = sizeof(T);
	}

	template <typename T> bool GetPayload(T &out) const {
		if (dataSize < sizeof(T))
			return false;
		std::memcpy(&out, payload, sizeof(T));
		return true;
	}

	std::string ToString() const {
		return "CustomEvent(type=" + std::to_string(customType) + " size=" + std::to_string(dataSize) + ")";
	}
};

} // namespace nkentseu
