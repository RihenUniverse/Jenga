# Jenga – Système de build cross‑plateforme

**Jenga** est un système de build complet, professionnel et extensible pour les projets C, C++, Objective‑C, Assembly, Rust, Zig, et plus encore.
Il supporte la compilation native, la cross‑compilation, le packaging, le déploiement, les tests unitaires, le profilage et les benchmarks.

---

## 🧱 Architecture

Le projet est organisé en plusieurs sous‑modules indépendants mais interconnectés :


| Dossier                                       | Description                                                                                |
| --------------------------------------------- | ------------------------------------------------------------------------------------------ |
| [`Commands/`](./Jenga/Commands/README.md)           | Commandes CLI (`build`, `run`, `test`, `package`, etc.)                                    |
| [`Core/`](./Jenga/Core/README.md)                   | Moteur de build : loader, cache, résolution de dépendances, builders…                   |
| [`Core/Builders/`](./Jenga/Core/Builders/README.md) | Implémentations spécifiques par plateforme (Windows, Linux, macOS, Android, iOS, Xbox…) |
| [`Unitest/`](./Jenga/Unitest/README.md)             | Framework de tests unitaires C++ intégré (macros, assertions, benchmarks)                |
| [`Utils/`](./Jenga/Utils/README.md)                 | Utilitaires généraux : console colorée, système de fichiers, processus…               |
| [`Api.py`](./Jenga/Core/Api.py)                          | DSL Python pour définir les workspaces et projets                                         |
| [`Jenga.py`](./Jenga/Jenga.py)                    | Point d’entrée de la CLI                                                                 |

---

## 🚀 Installation

```bash
pip install Jenga
```
