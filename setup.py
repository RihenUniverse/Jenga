from setuptools import setup, find_packages
import os

# Lire le README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Trouver automatiquement tous les packages
packages = find_packages(include=['Jenga', 'Jenga.*'])

# Lister tous les fichiers de données (scripts shell/batch)
data_files = []
if os.path.exists("jenga.sh"):
    data_files.append(("", ["jenga.sh"]))
if os.path.exists("jenga.bat"):
    data_files.append(("", ["jenga.bat"]))

# Trouver tous les fichiers dans le dossier Unitest
unitest_files = []
unitest_dir = os.path.join("Jenga", "Unitest")
if os.path.exists(unitest_dir):
    for root, dirs, files in os.walk(unitest_dir):
        for file in files:
            if file.endswith(('.cpp', '.h', '.txt', '.md')):
                full_path = os.path.join(root, file)
                # Garder le chemin relatif
                unitest_files.append(full_path)

setup(
    name="jenga-build-system",
    version="1.0.2",
    author="Rihen",
    author_email="rihen.universe@gmail.com",
    description="Modern multi-platform C/C++ build system with unified Python DSL",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/RihenUniverse/Jenga",
    
    # Packages à inclure
    packages=packages,
    
    # Fichiers de données
    data_files=data_files,
    
    # Inclure les fichiers Unitest comme données de package
    package_data={
        'Jenga': [
            '*.py',
            'Commands/*.py',
            'core/*.py',
            'utils/*.py',
            'Unitest/**/*.cpp',
            'Unitest/**/*.h',
            'Unitest/**/*.txt',
            'Unitest/**/*.md',
        ],
    },
    
    # Fichiers d'entrée (scripts)
    scripts=['jenga.sh', 'jenga.bat'] if os.path.exists('jenga.sh') and os.path.exists('jenga.bat') else [],
    
    # Points d'entrée console
    entry_points={
        "console_scripts": [
            "jenga=Jenga.jenga:main",  # jenga → Jenga/jenga.py:main()
        ],
    },
    
    classifiers=[
        # Niveau de développement
        "Development Status :: 5 - Production/Stable",
        
        # Public cible
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        
        # Licence
        "License :: OSI Approved :: MIT License",
        
        # Langages supportés
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        
        # Plateformes supportées
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: Microsoft :: Windows :: Windows 11",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        
        # Environnements
        "Environment :: Console",
        "Natural Language :: English",
        
        # Sujets
        "Topic :: Software Development :: Compilers",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Software Distribution",
    ],
    
    # Dépendances
    python_requires=">=3.7",
    install_requires=[
        # Aucune dépendance externe - pure Python!
    ],
    
    # Dépendances optionnelles pour le développement
    extras_require={
        "dev": [
            "pytest>=7.0",
            "black>=23.0",
            "flake8>=6.0",
            "mypy>=1.0",
            "twine>=4.0",
            "wheel>=0.40",
        ],
        "docs": [
            "sphinx>=7.0",
            "sphinx-rtd-theme>=1.0",
            "myst-parser>=2.0",
        ],
    },
    
    # Métadonnées supplémentaires
    keywords=[
        "build-system",
        "c++",
        "cmake",
        "make",
        "cross-platform",
        "android",
        "ios",
        "embedded",
        "testing",
        "ci-cd",
    ],
    
    # URLs du projet
    project_urls={
        "Documentation": "https://github.com/RihenUniverse/Jenga/tree/main/Docs",
        "Source Code": "https://github.com/RihenUniverse/Jenga",
        "Bug Tracker": "https://github.com/RihenUniverse/Jenga/issues",
        "Changelog": "https://github.com/RihenUniverse/Jenga/blob/main/Docs/CHANGELOG_v1.0.2.md",
    },
    
    # Options de build
    zip_safe=False,
    include_package_data=True,
)