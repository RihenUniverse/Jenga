# Cours 10 — Audio Programming from scratch
**Prérequis :** Cours 01, C++ intermédiaire  
**Durée estimée :** 6 semaines  
**Objectif :** Implémenter un moteur audio complet en C++, de la synthèse de sons à l'audio 3D spatialisé, sans bibliothèque audio externe (sauf l'API OS bas niveau).

---

## Unité 1 — Fondamentaux du son numérique (1 semaine)

### Semaine 1
- Physique du son : ondes, fréquence, amplitude, phase
- Numérisation : échantillonnage (Nyquist), quantification, résolution (8/16/24 bits)
- Formats audio : PCM, float32, interleaved vs planar, mono/stéréo/5.1
- Sample rate : 44100Hz, 48000Hz, 96000Hz
- Buffer audio : callback model (pull) vs push model
- API audio OS bas niveau : Win32 WASAPI (exclusif et partagé), portaudio en fallback
- **TP :** Ouvrir un stream audio WASAPI, générer un sinus 440Hz, l'envoyer au DAC

---

## Unité 2 — Synthèse sonore (1 semaine)

### Semaine 2
- Oscillateurs : sinus, carré, triangle, dent de scie — implémentation sans branchements
- Enveloppes ADSR (Attack, Decay, Sustain, Release)
- Modulation FM (Frequency Modulation) : Yamaha DX7 simplifié
- Synthèse additive : somme d'harmoniques, série de Fourier
- Synthèse soustractive : filtre passe-bas sur signal riche en harmoniques
- Bruit : bruit blanc, bruit rose, bruit brun — génération
- **TP :** Synthétiseur polyphonique 4 voix avec ADSR, clavier MIDI-like sur clavier PC

---

## Unité 3 — Traitement du signal audio (DSP) (2 semaines)

### Semaine 3
- Filtres numériques : IIR (Butterworth, Biquad) et FIR
- Filtre biquad : passe-bas, passe-haut, passe-bande, notch, peak, shelf
- Implémentation des coefficients RBJ (Robert Bristow-Johnson)
- Convolution temporelle et fréquentielle (FFT)
- Reverb algorithmique : Schroeder reverberator, algorithme de Freeverb
- **TP :** Chaîne de traitement : oscillateur → filtre biquad animé → reverb

### Semaine 4
- Delay et écho : circular buffer, feedback, modulation (flanger, chorus)
- Compresseur dynamique : détection d'enveloppe, calcul du gain, look-ahead
- Limiteur : protection des niveaux de sortie
- Égaliseur graphique multi-bandes
- FFT for analysis : visualisation du spectre en temps réel
- **TP :** Chain d'effets complète : EQ → compresseur → reverb → limiteur, visualisation spectrum

---

## Unité 4 — Chargement et décodage audio (1 semaine)

### Semaine 5
- Format WAV : parsing du header RIFF, lecture des samples PCM
- Format OGG/Vorbis : décodeur from scratch simplifié (ou intégration de stb_vorbis)
- Streaming audio : décodage par blocs, double buffering
- Resampling : conversion de sample rate (interpolation linéaire, Sinc)
- Mixage : somme de plusieurs flux audio avec gestion du clipping
- **TP :** Player audio complet : WAV + OGG, streaming, plusieurs pistes simultanées

---

## Unité 5 — Audio 3D et spatialisation (1 semaine)

### Semaine 6
- HRTF (Head-Related Transfer Function) : concept de spatialisation binaurale
- Atténuation par distance : modèles inverse, inverse square, linear
- Effet Doppler : variation de fréquence selon la vélocité relative
- Panning stéréo et surround (VBAP — Vector Base Amplitude Panning)
- Occlusion et obstruction : matériaux absorbants, réflexion
- Intégration avec une scène 3D : listener + sources, mise à jour des positions
- **TP :** Scène 3D avec audio spatialisé : sources qui se déplacent, effet Doppler, occlusion

---

## Projet Final

**Moteur audio complet** :
- Synthèse polyphonique (8 voix)
- Chargement WAV/OGG avec streaming
- Mixeur multi-bus (master, music, sfx, voice)
- Effets : reverb, delay, compresseur, EQ
- Audio 3D avec HRTF simplifié
- Intégration avec la scène 3D du cours 11
- Visualiseur de spectre en temps réel

**Critère :** Latence < 20ms, zéro clic/pop, 32 sources simultanées à 48kHz.
