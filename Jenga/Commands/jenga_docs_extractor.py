#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga Documentation Extractor - Orchestrateur principal
Coordonne le parsing, l'indexation et la génération de documentation
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict

from jenga_docs_parser import (
    ElementType, ElementSignature, Parameter, DocComment,
    CppSignatureParser, DoxygenParser
)


# ============================================================================
# STRUCTURES D'INDEXATION
# ============================================================================

@dataclass
class FileDocumentation:
    """Documentation complète d'un fichier"""
    file_path: Path
    file_name: str
    relative_path: str  # Relatif au workspace
    
    # En-tête du fichier
    file_description: str = ""
    file_author: str = ""
    file_date: str = ""
    
    # Éléments documentés
    elements: List[DocComment] = field(default_factory=list)
    
    # Métadonnées
    namespaces: List[str] = field(default_factory=list)
    includes: List[str] = field(default_factory=list)
    forward_declarations: List[str] = field(default_factory=list)
    
    # Relations
    included_by: List[str] = field(default_factory=list)  # Fichiers qui incluent ce fichier


@dataclass
class ProjectDocumentation:
    """Documentation complète d'un projet"""
    project_name: str
    project_path: Path
    
    # Tous les fichiers
    files: List[FileDocumentation] = field(default_factory=list)
    
    # Index par type
    classes: List[DocComment] = field(default_factory=list)
    structs: List[DocComment] = field(default_factory=list)
    enums: List[DocComment] = field(default_factory=list)
    unions: List[DocComment] = field(default_factory=list)
    functions: List[DocComment] = field(default_factory=list)
    methods: List[DocComment] = field(default_factory=list)
    variables: List[DocComment] = field(default_factory=list)
    macros: List[DocComment] = field(default_factory=list)
    typedefs: List[DocComment] = field(default_factory=list)
    
    # Index par namespace
    by_namespace: Dict[str, List[DocComment]] = field(default_factory=dict)
    
    # Index par nom (pour liens)
    by_name: Dict[str, DocComment] = field(default_factory=dict)
    
    # Graphe de dépendances entre fichiers
    file_dependencies: Dict[str, Set[str]] = field(default_factory=dict)
    
    # Statistiques
    stats: Dict[str, int] = field(default_factory=dict)


# ============================================================================
# EXTRACTEUR PRINCIPAL
# ============================================================================

class DocumentationExtractor:
    """Extracteur principal de documentation"""
    
    SUPPORTED_EXTENSIONS = {'.h', '.hpp', '.hxx', '.hh', '.cpp', '.cxx', '.cc', '.c', '.inl'}
    
    def __init__(self, project_name: str, project_path: Path, 
                 include_private: bool = False, verbose: bool = False):
        self.project_name = project_name
        self.project_path = project_path
        self.include_private = include_private
        self.verbose = verbose
        
        # Parsers
        self.signature_parser = CppSignatureParser()
        self.doxygen_parser = DoxygenParser()
        
        # Documentation du projet
        self.project_doc = ProjectDocumentation(
            project_name=project_name,
            project_path=project_path
        )
        
        # Contexte de parsing
        self.current_file: Optional[Path] = None
        self.current_namespace_stack: List[str] = []
        self.current_class_stack: List[str] = []
        self.current_access: str = "public"
    
    def extract(self, source_dirs: List[Path]) -> ProjectDocumentation:
        """Extrait la documentation de tous les fichiers"""
        
        if self.verbose:
            print(f"📚 Extracting documentation for project: {self.project_name}")
        
        # Collecter tous les fichiers
        all_files = self._collect_files(source_dirs)
        
        if self.verbose:
            print(f"📁 Found {len(all_files)} source files")
        
        # Parser chaque fichier
        for i, file_path in enumerate(all_files):
            if self.verbose:
                print(f"  [{i+1}/{len(all_files)}] Processing {file_path.name}...", end='\r')
            
            file_doc = self._parse_file(file_path)
            if file_doc and file_doc.elements:
                self.project_doc.files.append(file_doc)
        
        if self.verbose:
            print()  # Nouvelle ligne après progression
        
        # Construire les index
        self._build_indices()
        
        # Résoudre les liens inter-éléments
        self._resolve_links()
        
        # Analyser les dépendances
        self._analyze_dependencies()
        
        # Calculer les statistiques
        self._calculate_stats()
        
        if self.verbose:
            print(f"✅ Extraction complete:")
            print(f"   - {len(self.project_doc.files)} files with documentation")
            print(f"   - {self.project_doc.stats.get('total_elements', 0)} elements documented")
        
        return self.project_doc
    
    def _collect_files(self, source_dirs: List[Path]) -> List[Path]:
        """Collecte tous les fichiers sources"""
        files = []
        for source_dir in source_dirs:
            if not source_dir.exists():
                if self.verbose:
                    print(f"⚠️  Warning: Directory does not exist: {source_dir}")
                continue
            
            for ext in self.SUPPORTED_EXTENSIONS:
                files.extend(source_dir.rglob(f"*{ext}"))
        
        # Trier pour avoir un ordre déterministe
        return sorted(set(files))
    
    def _parse_file(self, file_path: Path) -> Optional[FileDocumentation]:
        """Parse un fichier source complet"""
        
        self.current_file = file_path
        self.current_namespace_stack = []
        self.current_class_stack = []
        self.current_access = "public"
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            if self.verbose:
                print(f"⚠️  Error reading {file_path}: {e}")
            return None
        
        # Créer la documentation du fichier
        try:
            relative_path = file_path.relative_to(self.project_path)
        except ValueError:
            relative_path = file_path.name
        
        file_doc = FileDocumentation(
            file_path=file_path,
            file_name=file_path.name,
            relative_path=str(relative_path)
        )
        
        # Parser l'en-tête du fichier
        self._parse_file_header(content, file_doc)
        
        # Extraire métadonnées
        file_doc.includes = self._extract_includes(content)
        file_doc.namespaces = self._extract_namespaces(content)
        
        # Trouver tous les commentaires de documentation
        doc_blocks = self._find_documentation_blocks(content)
        
        # Parser chaque bloc
        for comment_text, line_num, code_after in doc_blocks:
            doc_comment = self._parse_documentation_block(
                comment_text, code_after, file_path, line_num
            )
            
            if doc_comment:
                # Filtrer les éléments privés si demandé
                if self.include_private or doc_comment.signature.access == "public":
                    file_doc.elements.append(doc_comment)
        
        return file_doc
    
    def _find_documentation_blocks(self, content: str) -> List[Tuple[str, int, str]]:
        """Trouve tous les blocs de documentation avec le code qui suit"""
        
        blocks = []
        lines = content.split('\n')
        
        # Pattern pour commentaires /** ... */
        doxygen_pattern = re.compile(r'/\*\*(.*?)\*/', re.DOTALL)
        
        for match in doxygen_pattern.finditer(content):
            comment_text = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            
            # Trouver le code qui suit
            end_pos = match.end()
            remaining_lines = content[end_pos:].split('\n')
            
            # Ignorer les lignes vides et commentaires
            code_lines = []
            for line in remaining_lines[:30]:  # Max 30 lignes
                stripped = line.strip()
                if stripped and not stripped.startswith('//'):
                    code_lines.append(line)
                    if len(code_lines) >= 10:  # Assez pour capturer une signature
                        break
            
            code_after = '\n'.join(code_lines)
            blocks.append((comment_text, line_num, code_after))
        
        # Pattern pour commentaires /// (lignes consécutives)
        i = 0
        while i < len(lines):
            if lines[i].strip().startswith('///'):
                # Début d'un bloc ///
                comment_lines = []
                start_line = i + 1
                
                while i < len(lines) and lines[i].strip().startswith('///'):
                    text = lines[i].strip()[3:].strip()
                    comment_lines.append(text)
                    i += 1
                
                comment_text = '\n'.join(comment_lines)
                
                # Code qui suit
                code_lines = []
                j = i
                while j < len(lines) and len(code_lines) < 10:
                    stripped = lines[j].strip()
                    if stripped and not stripped.startswith('//'):
                        code_lines.append(lines[j])
                    j += 1
                
                code_after = '\n'.join(code_lines)
                blocks.append((comment_text, start_line, code_after))
            else:
                i += 1
        
        return blocks
    
    def _parse_documentation_block(self, comment_text: str, code_after: str,
                                   file_path: Path, line_num: int) -> Optional[DocComment]:
        """Parse un bloc de documentation complet"""
        
        # Mettre à jour le contexte (namespace, classe, access)
        self._update_context(code_after)
        
        # Détecter le type d'élément et parser sa signature
        signature = self._parse_element_signature(code_after)
        
        if not signature:
            return None
        
        # Enrichir la signature avec le contexte
        signature.namespace = "::".join(self.current_namespace_stack)
        signature.access = self.current_access
        
        if self.current_class_stack:
            signature.parent_class = "::".join(self.current_class_stack)
            # Si dans une classe, c'est une méthode
            if signature.element_type == ElementType.FUNCTION:
                signature.element_type = ElementType.METHOD
        
        # Parser le commentaire Doxygen
        doc_comment = self.doxygen_parser.parse(comment_text, signature)
        doc_comment.file_path = str(file_path)
        doc_comment.line_number = line_num
        
        return doc_comment
    
    def _parse_element_signature(self, code: str) -> Optional[ElementSignature]:
        """Détecte et parse la signature d'un élément C++"""
        
        # Essayer de détecter le type d'élément
        code_clean = code.strip()
        
        # Class/Struct
        if re.search(r'\b(class|struct)\b', code_clean):
            return self.signature_parser.parse_signature(code, 'class')
        
        # Enum
        if re.search(r'\benum\b', code_clean):
            return self.signature_parser.parse_signature(code, 'enum')
        
        # Union
        if re.search(r'\bunion\b', code_clean):
            return self.signature_parser.parse_signature(code, 'union')
        
        # Macro
        if code_clean.startswith('#define'):
            return self.signature_parser.parse_signature(code, 'macro')
        
        # Typedef/using
        if re.search(r'\b(typedef|using)\b', code_clean):
            return self.signature_parser.parse_signature(code, 'typedef')
        
        # Function (avec parenthèses et potentiel type de retour)
        if '(' in code_clean and ')' in code_clean:
            # Vérifier que ce n'est pas juste un appel de fonction
            if not code_clean.strip().endswith(';') or '=' not in code_clean:
                return self.signature_parser.parse_signature(code, 'function')
        
        # Variable (dernier recours)
        if ';' in code_clean:
            return self.signature_parser.parse_signature(code, 'variable')
        
        return None
    
    def _update_context(self, code: str):
        """Met à jour le contexte de parsing (namespace, classe, access)"""
        
        # Détecter namespace
        ns_match = re.search(r'namespace\s+([a-zA-Z_]\w*)\s*\{', code)
        if ns_match:
            self.current_namespace_stack.append(ns_match.group(1))
        
        # Détecter class/struct
        class_match = re.search(r'(class|struct)\s+(?:[A-Z_]+\s+)?([a-zA-Z_]\w*)', code)
        if class_match:
            self.current_class_stack.append(class_match.group(2))
            # struct = public par défaut, class = private
            self.current_access = "public" if class_match.group(1) == "struct" else "private"
        
        # Détecter access specifier
        for access in ['public', 'private', 'protected']:
            if f'{access}:' in code:
                self.current_access = access
        
        # Détecter fermeture de scope (approximatif)
        if code.count('}') > code.count('{'):
            # Approximation: fermeture de namespace ou classe
            if self.current_class_stack:
                self.current_class_stack.pop()
            elif self.current_namespace_stack:
                self.current_namespace_stack.pop()
    
    def _parse_file_header(self, content: str, file_doc: FileDocumentation):
        """Parse l'en-tête du fichier"""
        
        lines = content.split('\n')[:50]  # Chercher dans les 50 premières lignes
        
        # Pattern pour en-tête standard
        header_pattern = re.compile(
            r'//\s*-{3,}.*?'
            r'//\s*FICHIER:\s*(.+?)\n'
            r'//\s*DESCRIPTION:\s*(.+?)\n'
            r'//\s*AUTEUR:\s*(.+?)\n'
            r'//\s*DATE:\s*(.+?)\n',
            re.DOTALL
        )
        
        header_text = '\n'.join(lines)
        match = header_pattern.search(header_text)
        
        if match:
            file_doc.file_description = match.group(2).strip()
            file_doc.file_author = match.group(3).strip()
            file_doc.file_date = match.group(4).strip()
    
    def _extract_includes(self, content: str) -> List[str]:
        """Extrait les #include"""
        includes = []
        for match in re.finditer(r'#include\s+[<"](.+?)[>"]', content):
            includes.append(match.group(1))
        return includes
    
    def _extract_namespaces(self, content: str) -> List[str]:
        """Extrait les namespaces déclarés"""
        namespaces = []
        for match in re.finditer(r'namespace\s+([a-zA-Z_]\w*)\s*\{', content):
            ns = match.group(1)
            if ns not in namespaces:
                namespaces.append(ns)
        return namespaces
    
    def _build_indices(self):
        """Construit les index par type, namespace, nom"""
        
        for file_doc in self.project_doc.files:
            for element in file_doc.elements:
                sig = element.signature
                
                # Index par type
                if sig.element_type == ElementType.CLASS:
                    self.project_doc.classes.append(element)
                elif sig.element_type == ElementType.STRUCT:
                    self.project_doc.structs.append(element)
                elif sig.element_type == ElementType.ENUM:
                    self.project_doc.enums.append(element)
                elif sig.element_type == ElementType.UNION:
                    self.project_doc.unions.append(element)
                elif sig.element_type == ElementType.FUNCTION:
                    self.project_doc.functions.append(element)
                elif sig.element_type == ElementType.METHOD:
                    self.project_doc.methods.append(element)
                elif sig.element_type == ElementType.VARIABLE:
                    self.project_doc.variables.append(element)
                elif sig.element_type == ElementType.MACRO:
                    self.project_doc.macros.append(element)
                elif sig.element_type == ElementType.TYPEDEF:
                    self.project_doc.typedefs.append(element)
                
                # Index par namespace
                ns = sig.namespace or "__global__"
                if ns not in self.project_doc.by_namespace:
                    self.project_doc.by_namespace[ns] = []
                self.project_doc.by_namespace[ns].append(element)
                
                # Index par nom (pour liens)
                # Utiliser nom complet avec namespace
                full_name = f"{ns}::{sig.name}" if ns != "__global__" else sig.name
                self.project_doc.by_name[full_name] = element
                
                # Aussi indexer par nom simple
                if sig.name not in self.project_doc.by_name:
                    self.project_doc.by_name[sig.name] = element
    
    def _resolve_links(self):
        """Résout les liens inter-éléments (@see, types, etc.)"""
        
        for file_doc in self.project_doc.files:
            for element in file_doc.elements:
                # Résoudre les liens @see
                resolved_see = []
                for see_ref in element.see_also:
                    # Chercher l'élément référencé
                    if see_ref in self.project_doc.by_name:
                        resolved_see.append(see_ref)
                    else:
                        # Peut-être juste un nom sans namespace
                        resolved_see.append(see_ref)
                
                element.see_also = resolved_see
    
    def _analyze_dependencies(self):
        """Analyse les dépendances entre fichiers"""
        
        # Construire un index include -> fichier
        file_by_name = {}
        for file_doc in self.project_doc.files:
            file_by_name[file_doc.file_name] = file_doc
            # Aussi par path relatif
            file_by_name[file_doc.relative_path] = file_doc
        
        # Pour chaque fichier, résoudre ses includes
        for file_doc in self.project_doc.files:
            deps = set()
            
            for include in file_doc.includes:
                # Chercher le fichier correspondant
                include_name = Path(include).name
                
                if include_name in file_by_name:
                    deps.add(file_by_name[include_name].relative_path)
                elif include in file_by_name:
                    deps.add(include)
            
            self.project_doc.file_dependencies[file_doc.relative_path] = deps
            
            # Remplir included_by (inverse)
            for dep in deps:
                if dep in file_by_name:
                    file_by_name[dep].included_by.append(file_doc.relative_path)
    
    def _calculate_stats(self):
        """Calcule les statistiques du projet"""
        
        stats = {
            'total_files': len(self.project_doc.files),
            'total_elements': sum(len(f.elements) for f in self.project_doc.files),
            'classes': len(self.project_doc.classes),
            'structs': len(self.project_doc.structs),
            'enums': len(self.project_doc.enums),
            'unions': len(self.project_doc.unions),
            'functions': len(self.project_doc.functions),
            'methods': len(self.project_doc.methods),
            'variables': len(self.project_doc.variables),
            'macros': len(self.project_doc.macros),
            'typedefs': len(self.project_doc.typedefs),
            'namespaces': len(self.project_doc.by_namespace),
        }
        
        # Statistiques avancées
        total_params = sum(
            len(e.signature.parameters) 
            for f in self.project_doc.files 
            for e in f.elements 
            if e.signature.parameters
        )
        stats['total_parameters'] = total_params
        
        # Moyenne de paramètres par fonction
        functions_with_params = [
            e for f in self.project_doc.files 
            for e in f.elements 
            if e.signature.element_type in [ElementType.FUNCTION, ElementType.METHOD]
        ]
        if functions_with_params:
            stats['avg_params_per_function'] = int(total_params / len(functions_with_params))
        else:
            stats['avg_params_per_function'] = 0
        
        # Éléments avec documentation complète
        well_documented = sum(
            1 for f in self.project_doc.files 
            for e in f.elements 
            if e.brief and e.description
        )
        stats['well_documented'] = well_documented
        
        if stats['total_elements'] > 0:
            stats['documentation_coverage'] = int((well_documented / stats['total_elements']) * 100)
        else:
            stats['documentation_coverage'] = 0
        
        self.project_doc.stats = stats


# ============================================================================
# UTILITAIRES
# ============================================================================

def create_element_id(element: DocComment) -> str:
    """Crée un ID unique pour un élément (pour les ancres HTML/MD)"""
    sig = element.signature
    
    # Format: namespace-classname-elementname
    parts = []
    
    if sig.namespace:
        parts.append(sig.namespace.replace('::', '-').lower())
    
    if sig.parent_class:
        parts.append(sig.parent_class.replace('::', '-').lower())
    
    parts.append(sig.name.lower())
    
    return '-'.join(parts)


def create_file_link(from_file: str, to_file: str, base_dir: str = "files") -> str:
    """Crée un lien relatif entre deux fichiers de documentation"""
    
    # Convertir les chemins en chemins MD
    from_md = Path(from_file).with_suffix('.md').name.replace('.', '_')
    to_md = Path(to_file).with_suffix('.md').name.replace('.', '_')
    
    # Si même fichier, lien interne
    if from_md == to_md:
        return f"#{to_md}"
    
    # Sinon, lien relatif
    return f"./{base_dir}/{to_md}"


def sanitize_filename(name: str) -> str:
    """Nettoie un nom pour l'utiliser comme nom de fichier"""
    # Remplacer caractères spéciaux
    name = name.replace('::', '_')
    name = name.replace('/', '_')
    name = name.replace('\\', '_')
    name = name.replace(' ', '_')
    name = re.sub(r'[<>:"|?*]', '', name)
    return name
