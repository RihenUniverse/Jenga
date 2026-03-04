# Cours 14 — Intelligence Artificielle from scratch
**Prérequis :** Cours 01 (mathématiques), C++ avancé  
**Durée estimée :** 16 semaines  
**Objectif :** Implémenter tous les algorithmes d'IA en C++ pur, des réseaux de neurones fondamentaux aux architectures modernes (transformers, diffusion), en partant des mathématiques.

---

## Unité 1 — Algèbre linéaire numérique from scratch (2 semaines)

### Semaine 1
- Tenseurs : généralisation des vecteurs/matrices — implémentation C++ `Tensor<T, N>`
- Opérations tensorielles : contraction, broadcasting
- Implémentation d'un `Tensor` ND avec strides, vues, reshape sans copie
- Différentiation numérique : différences finies, limites de précision
- **TP :** Bibliothèque tensor from scratch avec benchmark vs Eigen

### Semaine 2
- Gradient descent from scratch : descente de gradient, learning rate
- Stochastic Gradient Descent (SGD) et mini-batches
- Momentum, Nesterov Accelerated Gradient
- Optimiseurs adaptatifs : AdaGrad, RMSProp, Adam (calcul complet des moments)
- Learning rate scheduling : step decay, cosine annealing, warmup
- **TP :** Régression linéaire + logistique optimisées avec Adam, visualisation convergence

---

## Unité 2 — Réseaux de neurones dense (2 semaines)

### Semaine 3
- Neurone artificiel : entrées, poids, biais, activation
- Fonctions d'activation : sigmoid, tanh, ReLU, Leaky ReLU, ELU, GELU, Swish
- Multi-Layer Perceptron (MLP) : couches denses, forward pass
- Backpropagation : calcul du gradient par la règle de la chaîne
- Implémentation C++ : `Layer`, `Linear`, `Activation`, `Network`
- **TP :** MLP pour classification MNIST, implémentation from scratch, accuracy > 97%

### Semaine 4
- Calcul automatique du gradient (autograd) : tape-based differentiation
- Implémentation d'un autograd from scratch : `Value` class avec backward()
- Fonctions de perte : MSE, Cross-Entropy, BCELoss, Huber
- Régularisation : L1, L2 (weight decay), dropout
- Batch normalization : normalisation, gamma/beta learnable, running stats
- **TP :** Autograd engine from scratch (inspiré de micrograd), réseau XOR, debug des gradients

---

## Unité 3 — Réseaux de neurones convolutifs (CNN) (2 semaines)

### Semaine 5
- Convolution 2D : fenêtre glissante, padding, stride, groupes
- Implémentation C++ d'une couche de convolution (im2col + GEMM)
- Pooling : max pooling, average pooling, global average pooling
- Architectures CNN classiques : LeNet-5, AlexNet (simplifié)
- **TP :** CNN sur CIFAR-10 from scratch, > 75% accuracy

### Semaine 6
- ResNet : skip connections, bottleneck blocks — implémentation
- Depthwise separable convolutions (MobileNet)
- Attention spatiale, squeeze-and-excitation
- Data augmentation : flip, crop, color jitter, cutout
- Transfer learning concept : feature extraction vs fine-tuning
- **TP :** ResNet-18 from scratch sur CIFAR-100, comparaison avec et sans augmentation

---

## Unité 4 — Réseaux récurrents et temporels (2 semaines)

### Semaine 7
- RNN (Recurrent Neural Networks) : problème de vanishing gradient
- LSTM (Long Short-Term Memory) : forget gate, input gate, output gate — dérivation complète
- GRU (Gated Recurrent Unit) : version simplifiée, comparaison LSTM
- Backpropagation Through Time (BPTT)
- Sequence modeling : prédiction de séries temporelles
- **TP :** LSTM from scratch pour prédiction de série temporelle (sin bruité, texte simple)

### Semaine 8
- WaveNet simplifié : dilated causal convolutions
- Temporal Convolutional Networks (TCN)
- Sequence-to-sequence avec encoder-decoder RNN
- Mécanisme d'attention de Bahdanau : query, key, value — dérivation
- **TP :** Traducteur simple avec seq2seq + attention, dataset jouet

---

## Unité 5 — Transformers (2 semaines)

### Semaine 9
- Self-attention : `Attention(Q,K,V) = softmax(QK^T/√d)V` — dérivation et implémentation
- Multi-head attention : projections, concaténation
- Positional encoding : sinusoïdal et appris
- Transformer block : attention + FFN + LayerNorm + skip connections
- Implémentation C++ du Transformer complet
- **TP :** Transformer from scratch pour classification de texte

### Semaine 10
- GPT-style (causal decoder-only) : masquage causal, génération auto-régressive
- Tokenization : BPE (Byte Pair Encoding) from scratch
- Mini-GPT : architecture, entraînement sur un dataset texte petit
- Vision Transformer (ViT) : patchification d'images
- Flash Attention concept : optimisation mémoire
- **TP :** Mini-GPT (10M params) entraîné sur Shakespeare ou code source

---

## Unité 6 — Rendu et IA (2 semaines)

### Semaine 11
- NeRF (Neural Radiance Fields) : représentation de scène par MLP
- Ray marching dans un NeRF : volume rendering integral
- Positional encoding pour NeRF (Fourier features)
- Entraînement d'un mini-NeRF sur un objet simple
- Gaussian Splatting concept : 3D Gaussians + rasterisation différentiable

### Semaine 12
- Diffusion models : forward process (ajout de bruit), reverse process (débruitage)
- DDPM (Denoising Diffusion Probabilistic Models) : dérivation du ELBO
- U-Net pour la prédiction du bruit
- Mini-diffusion model from scratch : génération d'images 32×32
- CLIP concept : contrastive learning, embeddings image+texte
- **TP :** Mini DDPM from scratch, génération de chiffres MNIST

---

## Unité 7 — Reinforcement Learning (2 semaines)

### Semaine 13
- MDP (Markov Decision Process) : états, actions, récompenses, politique
- Q-Learning : table Q, algorithme de mise à jour
- Deep Q-Network (DQN) : réseau Q, experience replay, target network
- Policy gradient : REINFORCE algorithm
- **TP :** DQN from scratch sur CartPole et un mini jeu

### Semaine 14
- Proximal Policy Optimization (PPO) : clipping du ratio, advantage estimation
- Actor-Critic : A2C/A3C
- Curiosity-driven exploration : intrinsic motivation
- RL pour les jeux : entraînement d'un agent pour un jeu custom du cours 11
- Self-play et MCTS (Monte Carlo Tree Search) simplifié
- **TP :** Agent PPO autonome pour un niveau du mini-jeu du cours 11

---

## Unité 8 — Déploiement et inférence (2 semaines)

### Semaine 15
- Quantization : INT8, FP16, mixed precision
- Pruning : élagage de poids, structured vs unstructured
- Knowledge distillation : modèle enseignant → élève
- ONNX : format d'échange, export depuis notre framework

### Semaine 16
- Inférence CPU optimisée : SIMD pour les matrix multiplications
- Inférence GPU via compute shaders (OpenGL/Vulkan)
- Runtime d'inférence from scratch : chargement d'un modèle ONNX, exécution
- Intégration dans le moteur de jeu : NPC avec réseau de neurones embarqué
- **TP :** Inférence d'un MLP/CNN en temps réel dans le moteur (< 1ms par frame)

---

## Projet Final

**Framework d'IA complet** :
- Autograd engine avec tenseurs ND
- Couches : Linear, Conv2D, LSTM, MultiHeadAttention, BatchNorm, Dropout
- Optimiseurs : SGD, Adam, LR scheduler
- Un modèle entraîné et déployé dans le moteur de jeu (cours 11) :
  - Option A : IA ennemie par RL (PPO)
  - Option B : génération de terrain par mini-diffusion
  - Option C : reconnaissance de gestes joueur par CNN

**Évaluation :** Exactitude du gradient (vérification numérique), performance d'entraînement, intégration temps réel.
