#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga Documentation Command
Commande principale pour générer la documentation des projets
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict, Optional

# Ajouter le répertoire parent pour les imports
JENGA_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(JENGA_DIR))

from utils.display import Display
from core.loader import load_workspace

# Import des modules de documentation
sys.path.insert(0, str(JENGA_DIR / 'commands'))
from jenga_docs_parser import CppSignatureParser, DoxygenParser
from jenga_docs_extractor import DocumentationExtractor, ProjectDocumentation
from jenga_docs_markdown import MarkdownGenerator


# ============================================================================
# CONFIGURATION
# ============================================================================

VERSION = "2.0.0"
SUPPORTED_FORMATS = ['markdown', 'html', 'pdf', 'all']


# ============================================================================
# COMMANDE PRINCIPALE
# ============================================================================

def execute(args):
    """Point d'entrée principal de la commande docs"""
    
    parser = argparse.ArgumentParser(
        description='Génération de documentation pour les projets Jenga',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  jenga docs extract                          # Tous les projets
  jenga docs extract --project NKCore         # Projet spécifique
  jenga docs extract --format markdown        # Format spécifique
  jenga docs extract --include-private        # Inclure membres privés
  jenga docs stats                            # Statistiques
  jenga docs list                             # Lister projets
  jenga docs clean                            # Nettoyer documentation
  
Formats supportés:
  markdown  - Documentation Markdown avec liens fonctionnels (défaut)
  html      - Documentation HTML responsive avec CSS moderne
  pdf       - Documentation PDF professionnelle
  all       - Tous les formats
"""
    )
    
    # Sous-commandes
    subparsers = parser.add_subparsers(
        dest='subcommand',
        help='Opération de documentation'
    )
    
    # --- Extract ---
    extract_parser = subparsers.add_parser(
        'extract',
        help='Extraire la documentation depuis les sources'
    )
    
    extract_parser.add_argument(
        '--project',
        help='Projet spécifique (défaut: tous)'
    )
    
    extract_parser.add_argument(
        '--output',
        default='docs',
        help='Répertoire de sortie (défaut: docs/)'
    )
    
    extract_parser.add_argument(
        '--format',
        choices=SUPPORTED_FORMATS,
        default='markdown',
        help='Format de sortie (défaut: markdown)'
    )
    
    extract_parser.add_argument(
        '--include-private',
        action='store_true',
        help='Inclure les membres privés/protégés'
    )
    
    extract_parser.add_argument(
        '--exclude-projects',
        nargs='+',
        help='Projets à exclure'
    )
    
    extract_parser.add_argument(
        '--exclude-dirs',
        nargs='+',
        help='Répertoires à exclure (ex: tests, vendor)'
    )
    
    extract_parser.add_argument(
        '--verbose',
        action='store_true',
        help='Affichage détaillé'
    )
    
    # --- Stats ---
    stats_parser = subparsers.add_parser(
        'stats',
        help='Afficher les statistiques de documentation'
    )
    
    stats_parser.add_argument(
        '--project',
        help='Projet spécifique'
    )
    
    stats_parser.add_argument(
        '--json',
        action='store_true',
        help='Format JSON'
    )
    
    # --- List ---
    list_parser = subparsers.add_parser(
        'list',
        help='Lister les projets documentables'
    )
    
    # --- Clean ---
    clean_parser = subparsers.add_parser(
        'clean',
        help='Nettoyer la documentation générée'
    )
    
    clean_parser.add_argument(
        '--project',
        help='Projet spécifique'
    )
    
    clean_parser.add_argument(
        '--output',
        default='docs',
        help='Répertoire de sortie (défaut: docs/)'
    )
    
    # Parse
    if not args:
        parser.print_help()
        return 0
    
    try:
        parsed = parser.parse_args(args)
    except SystemExit:
        return 1
    
    # Router
    if parsed.subcommand == 'extract':
        return cmd_extract(parsed)
    elif parsed.subcommand == 'stats':
        return cmd_stats(parsed)
    elif parsed.subcommand == 'list':
        return cmd_list(parsed)
    elif parsed.subcommand == 'clean':
        return cmd_clean(parsed)
    elif not parsed.subcommand:
        parser.print_help()
        return 0
    
    return 1


def cmd_extract(args):
    """Commande extract"""
    workspace = load_workspace()
    if not workspace:
        Display.error("Aucun workspace trouvé")
        return 1
    
    Display.header(f"📚 Documentation - {workspace.name}")
    
    # Déterminer projets
    if args.project:
        if args.project not in workspace.projects:
            Display.error(f"Projet introuvable: {args.project}")
            return 1
        projects = [args.project]
    else:
        projects = list(workspace.projects.keys())
    
    if args.exclude_projects:
        projects = [p for p in projects if p not in args.exclude_projects]
    
    Display.info(f"📦 {len(projects)} projet(s)")
    print()
    
    stats = {'success': 0, 'failed': 0, 'skipped': 0}
    
    for project_name in projects:
        project = workspace.projects[project_name]
        project_dir = Path(project.location)
        if not project_dir.is_absolute():
            project_dir = workspace.location / project_dir
        
        try:
            project_dir.relative_to(workspace.location)
        except ValueError:
            Display.warning(f"⚠️  Externe: {project_name}")
            stats['skipped'] += 1
            continue
        
        result = extract_project(project_name, project, workspace.location, args)
        if result:
            stats['success'] += 1
        else:
            stats['failed'] += 1
        print()
    
    print_summary(stats, args.output)
    return 0 if stats['failed'] == 0 else 1


def extract_project(name, project, workspace_dir, args):
    """Extrait un projet"""
    Display.section(f"📦 {name}")
    
    sources = get_source_directories(project, workspace_dir)
    if not sources:
        Display.warning("  Pas de sources")
        return None
    
    try:
        extractor = DocumentationExtractor(
            project_name=name,
            project_path=workspace_dir / project.location,
            include_private=args.include_private,
            verbose=args.verbose
        )
        
        doc = extractor.extract(sources)
        
        if doc.stats.get('total_elements', 0) == 0:
            Display.warning("  Aucun élément")
            return None
        
        output = workspace_dir / args.output / name
        
        if args.format in ['markdown', 'all']:
            gen = MarkdownGenerator(doc)
            gen.generate(output / 'markdown')
        
        Display.success(f"  ✓ {doc.stats['total_files']} fichiers")
        Display.success(f"  ✓ {doc.stats['total_elements']} éléments")
        
        return {'files': doc.stats['total_files'], 'elements': doc.stats['total_elements']}
    
    except Exception as e:
        Display.error(f"  ✗ {e}")
        return None


def get_source_directories(project, workspace_dir):
    """Trouve les répertoires sources"""
    dirs = []
    project_dir = Path(project.location)
    if not project_dir.is_absolute():
        project_dir = workspace_dir / project_dir
    
    for name in ['src', 'include']:
        d = project_dir / name
        if d.exists():
            dirs.append(d)
    
    if not dirs and project_dir.exists():
        dirs.append(project_dir)
    
    return dirs


def print_summary(stats, output):
    """Résumé"""
    Display.header("📊 RÉSUMÉ")
    Display.success(f"✓ Succès: {stats['success']}")
    if stats['failed']:
        Display.error(f"✗ Échecs: {stats['failed']}")
    if stats['skipped']:
        Display.warning(f"⊘ Ignorés: {stats['skipped']}")
    print()
    Display.info(f"📂 {output}/")


def cmd_stats(args):
    """Stats"""
    workspace = load_workspace()
    if not workspace:
        return 1
    
    Display.header("📊 Statistiques")
    Display.info(f"Projets: {len(workspace.projects)}")
    return 0


def cmd_list(args):
    """Liste"""
    workspace = load_workspace()
    if not workspace:
        return 1
    
    Display.header("📚 Projets")
    for name in workspace.projects:
        Display.info(f"📦 {name}")
    return 0


def cmd_clean(args):
    """Clean"""
    workspace = load_workspace()
    if not workspace:
        return 1
    
    output = workspace.location / args.output
    if args.project:
        output = output / args.project
    
    if not output.exists():
        Display.warning("Déjà propre")
        return 0
    
    import shutil
    shutil.rmtree(output)
    Display.success("✓ Nettoyé")
    return 0


if __name__ == '__main__':
    sys.exit(execute(sys.argv[1:]))
