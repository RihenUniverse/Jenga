#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga Documentation Extractor Command
Extracts documentation from all projects in a workspace
"""

import os
import re
import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Add parent directory to path
JENGA_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(JENGA_DIR))

from utils.display import Display
from core.loader import load_workspace


# ============================================================================
# CONSTANTS
# ============================================================================

VERSION = "1.1.0"
COMPANY_NAME = "Rihen"
COPYRIGHT_YEAR = "2024-2026"
LICENSE_TYPE = "Proprietary License - Free to use and modify"

# Extensions de fichiers supportées
SUPPORTED_EXTENSIONS = {
    '.h', '.hpp', '.hxx', '.hh',      # Headers C++
    '.c', '.cpp', '.cxx', '.cc',      # Sources C/C++
    '.m', '.mm',                       # Objective-C/C++
    '.inl',                            # Inline implementations
}

# Types de commentaires reconnus
class CommentType(Enum):
    """Types de commentaires de documentation"""
    CLASS = "class"
    STRUCT = "struct"
    ENUM = "enum"
    UNION = "union"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    NAMESPACE = "namespace"
    FILE = "file"
    TYPEDEF = "typedef"
    MACRO = "macro"
    TEMPLATE = "template"
    
    def __lt__(self, other):
        """Permet de trier les CommentType par leur valeur string"""
        return self.value < other.value
    
    def __gt__(self, other):
        """Permet de trier les CommentType par leur valeur string"""
        return self.value > other.value


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class Parameter:
    """Paramètre de fonction/méthode"""
    name: str
    type: str
    description: str = ""
    direction: str = ""  # in, out, in/out
    

@dataclass
class TemplateParameter:
    """Paramètre de template"""
    name: str
    description: str = ""
    default_value: str = ""
    

@dataclass
class DocComment:
    """Commentaire de documentation extrait"""
    type: CommentType
    name: str
    brief: str = ""
    description: str = ""
    params: List[Parameter] = field(default_factory=list)
    template_params: List[TemplateParameter] = field(default_factory=list)
    returns: str = ""
    return_values: Dict[str, str] = field(default_factory=dict)
    throws: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    see_also: List[str] = field(default_factory=list)
    since: str = ""
    deprecated: str = ""
    author: str = ""
    date: str = ""
    file_path: str = ""
    line_number: int = 0
    namespace: str = ""
    access: str = "public"  # public, private, protected
    is_static: bool = False
    is_const: bool = False
    is_virtual: bool = False
    is_inline: bool = False
    is_explicit: bool = False
    is_constexpr: bool = False
    is_noexcept: bool = False
    complexity: str = ""
    thread_safety: str = ""
    template_specialization: str = ""  # Pour les spécialisations de template
    

@dataclass
class FileDocumentation:
    """Documentation d'un fichier"""
    file_path: str
    file_name: str
    description: str = ""
    author: str = ""
    date: str = ""
    version: str = ""
    comments: List[DocComment] = field(default_factory=list)
    namespaces: List[str] = field(default_factory=list)
    includes: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # Autres fichiers inclus
    

@dataclass
class ProjectDocumentation:
    """Documentation complète du projet"""
    project_name: str
    files: List[FileDocumentation] = field(default_factory=list)
    index_by_type: Dict[CommentType, List[DocComment]] = field(default_factory=dict)
    index_by_namespace: Dict[str, List[DocComment]] = field(default_factory=dict)
    global_functions: List[DocComment] = field(default_factory=list)
    global_variables: List[DocComment] = field(default_factory=list)
    

# ============================================================================
# DOCUMENTATION PARSER AMÉLIORÉ
# ============================================================================

class DocumentationParser:
    """Parse les commentaires de documentation avec support multi-style"""
    
    def __init__(self):
        # Patterns pour différents styles de commentaires
        
        # Style Doxygen: /** ... */
        self.doxygen_pattern = re.compile(
            r'/\*\*(.*?)\*/',
            re.DOTALL
        )
        
        # Style JavaDoc: /*! ... */
        self.javadoc_pattern = re.compile(
            r'/\*!(.*?)\*/',
            re.DOTALL
        )
        
        # Style commentaires de section: // ----- avec titre
        self.section_pattern = re.compile(
            r'//\s*-{3,}\s*\n//\s*([A-Z_]+):\s*(.+?)\n//\s*-{3,}',
            re.DOTALL
        )
        
        # Style commentaires inline ///
        self.inline_doc_pattern = re.compile(
            r'///\s*(.*?)$',
            re.MULTILINE
        )
        
        # Style commentaires Qt: /*! ... */
        self.qt_pattern = re.compile(
            r'/\*!(.*?)\*/',
            re.DOTALL
        )
        
        # Style en-tête de fichier standard
        self.file_header_pattern = re.compile(
            r'//\s*-{3,}\s*\n//\s*FICHIER:\s*(.+?)\n//\s*DESCRIPTION:\s*(.+?)\n//\s*AUTEUR:\s*(.+?)\n//\s*DATE:\s*(.+?)\n//\s*-{3,}',
            re.DOTALL
        )
        
        # Patterns pour tags Doxygen
        self.tag_patterns = {
            'brief': re.compile(r'@brief\s+(.+?)(?=@|\n\n|\*/|\Z)', re.DOTALL),
            'param': re.compile(r'@param(?:\[([^\]]+)\])?\s+(\w+)\s+(.+?)(?=@|\n\n|\*/|\Z)', re.DOTALL),
            'return': re.compile(r'@return\s+(.+?)(?=@|\n\n|\*/|\Z)', re.DOTALL),
            'retval': re.compile(r'@retval\s+(\w+)\s+(.+?)(?=@|\n|\*/|\Z)', re.DOTALL),
            'throw': re.compile(r'@throws?\s+(.+?)(?=@|\n|\*/|\Z)', re.DOTALL),
            'example': re.compile(r'@example\s+(.+?)(?=@|\n\n|\*/|\Z)', re.DOTALL),
            'code': re.compile(r'@code\s*(.*?)@endcode', re.DOTALL | re.IGNORECASE),
            'note': re.compile(r'@note\s+(.+?)(?=@|\n\n|\*/|\Z)', re.DOTALL),
            'warning': re.compile(r'@warning\s+(.+?)(?=@|\n\n|\*/|\Z)', re.DOTALL),
            'see': re.compile(r'@see\s+(.+?)(?=@|\n|\*/|\Z)', re.DOTALL),
            'sa': re.compile(r'@sa\s+(.+?)(?=@|\n|\*/|\Z)', re.DOTALL),
            'since': re.compile(r'@since\s+(.+?)(?=@|\n|\*/|\Z)', re.DOTALL),
            'deprecated': re.compile(r'@deprecated\s+(.+?)(?=@|\n\n|\*/|\Z)', re.DOTALL),
            'author': re.compile(r'@author\s+(.+?)(?=@|\n|\*/|\Z)', re.DOTALL),
            'date': re.compile(r'@date\s+(.+?)(?=@|\n|\*/|\Z)', re.DOTALL),
            'complexity': re.compile(r'@complexity\s+(.+?)(?=@|\n|\*/|\Z)', re.DOTALL),
            'threadsafe': re.compile(r'@threadsafe', re.DOTALL | re.IGNORECASE),
            'notthreadsafe': re.compile(r'@notthreadsafe', re.DOTALL | re.IGNORECASE),
            'tparam': re.compile(r'@tparam\s+(\w+)\s+(.+?)(?=@|\n|\*/|\Z)', re.DOTALL),
            'interface': re.compile(r'@interface', re.DOTALL | re.IGNORECASE),
            'abstract': re.compile(r'@abstract', re.DOTALL | re.IGNORECASE),
            'final': re.compile(r'@final', re.DOTALL | re.IGNORECASE),
            'ingroup': re.compile(r'@ingroup\s+(\w+)', re.DOTALL),
            'defgroup': re.compile(r'@defgroup\s+(\w+)\s+(.+?)(?=@|\n|\*/|\Z)', re.DOTALL),
            'addtogroup': re.compile(r'@addtogroup\s+(\w+)', re.DOTALL),
        }
    
    def parse_file(self, file_path: Path, include_private: bool = False) -> FileDocumentation:
        """Parse un fichier et extrait toute la documentation"""
        
        file_doc = FileDocumentation(
            file_path=str(file_path),
            file_name=file_path.name
        )
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"⚠️  Erreur lecture {file_path}: {e}")
            return file_doc
        
        # Extraire les includes
        file_doc.includes = self._extract_includes(content)
        
        # Extraire les namespaces
        file_doc.namespaces = self._extract_namespaces(content)
        
        # Extraire documentation du fichier (header)
        file_header_doc = self._extract_file_header(content)
        if file_header_doc:
            file_doc.description = file_header_doc.get('description', '')
            file_doc.author = file_header_doc.get('author', '')
            file_doc.date = file_header_doc.get('date', '')
            file_doc.version = file_header_doc.get('version', '')
        
        # Trouver tous les commentaires de documentation
        doc_comments = self._find_doc_comments(content)
        
        # Parser chaque commentaire et identifier le code associé
        for comment_text, line_num, comment_type in doc_comments:
            # Trouver le code qui suit le commentaire
            code_after = self._get_code_after_comment(content, line_num)
            
            if code_after:
                doc_comment = self._parse_comment(
                    comment_text, 
                    code_after, 
                    file_path, 
                    line_num,
                    comment_type
                )
                
                if doc_comment:
                    # Filtrer les membres privés si demandé
                    if include_private or doc_comment.access == "public":
                        file_doc.comments.append(doc_comment)
        
        return file_doc
    
    def _find_doc_comments(self, content: str) -> List[Tuple[str, int, str]]:
        """Trouve tous les commentaires de documentation dans le contenu"""
        
        comments = []
        
        # Commentaires Doxygen /** ... */
        for match in self.doxygen_pattern.finditer(content):
            comment_text = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            comments.append((comment_text, line_num, "doxygen"))
        
        # Commentaires JavaDoc /*! ... */
        for match in self.javadoc_pattern.finditer(content):
            comment_text = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            comments.append((comment_text, line_num, "javadoc"))
        
        # Commentaires Qt /*! ... */
        for match in self.qt_pattern.finditer(content):
            comment_text = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            comments.append((comment_text, line_num, "qt"))
        
        # Commentaires /// (plusieurs lignes consécutives)
        lines = content.split('\n')
        current_comment = []
        start_line = 0
        
        for i, line in enumerate(lines):
            if line.strip().startswith('///'):
                if not current_comment:
                    start_line = i + 1
                # Extraire le texte après ///
                text = line.strip()[3:].strip()
                current_comment.append(text)
            else:
                if current_comment:
                    # Fin d'un bloc de commentaires ///
                    comment_text = '\n'.join(current_comment)
                    comments.append((comment_text, start_line, "triple_slash"))
                    current_comment = []
        
        # Dernier bloc s'il existe
        if current_comment:
            comment_text = '\n'.join(current_comment)
            comments.append((comment_text, start_line, "triple_slash"))
        
        # Commentaires de section style "// -----"
        # Ces commentaires décrivent des classes/énumérations/structures
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('// -----') and ':' in stripped:
                # C'est un commentaire de section
                section_match = re.search(r'//\s*-{3,}\s*\n//\s*([A-Z_]+):\s*(.+?)\n//\s*-{3,}', 
                                         '\n'.join(lines[max(0, i-2):min(len(lines), i+3)]))
                if section_match:
                    element_type = section_match.group(1).lower()
                    element_name = section_match.group(2).strip()
                    comment_text = f"{element_type.upper()}: {element_name}"
                    comments.append((comment_text, i + 1, "section"))
        
        return comments
    
    def _parse_comment(self, comment_text: str, code_after: str, 
                      file_path: Path, line_num: int, comment_type: str) -> Optional[DocComment]:
        """Parse un commentaire de documentation"""
        
        # Nettoyer le commentaire selon son type
        if comment_type == "section":
            # Pour les commentaires de section, on extrait directement le type et le nom
            match = re.match(r'([A-Z_]+):\s*(.+)', comment_text)
            if match:
                element_type_str = match.group(1).lower()
                element_name = match.group(2).strip()
                
                # Mapper le type
                type_map = {
                    'classe': CommentType.CLASS,
                    'enumération': CommentType.ENUM,
                    'enum': CommentType.ENUM,
                    'structure': CommentType.STRUCT,
                    'union': CommentType.UNION,
                    'namespace': CommentType.NAMESPACE,
                    'alias': CommentType.TYPEDEF,
                    'macro': CommentType.MACRO,
                }
                
                element_type = type_map.get(element_type_str, CommentType.CLASS)
                
                doc_comment = DocComment(
                    type=element_type,
                    name=element_name,
                    file_path=str(file_path),
                    line_number=line_num,
                    access='public'
                )
                
                # Pour les commentaires de section, la description est dans la ligne suivante
                lines = code_after.split('\n')
                if len(lines) > 0:
                    # Chercher la description dans les premières lignes
                    for line in lines[:5]:
                        if 'DESCRIPTION:' in line:
                            desc_match = re.search(r'DESCRIPTION:\s*(.+)', line)
                            if desc_match:
                                doc_comment.description = desc_match.group(1).strip()
                                break
                
                return doc_comment
            return None
        else:
            # Pour les autres types de commentaires, identifier l'élément
            element_info = self._identify_element(code_after)
            if not element_info:
                return None
            
            element_type, element_name, element_details = element_info
            
            doc_comment = DocComment(
                type=element_type,
                name=element_name,
                file_path=str(file_path),
                line_number=line_num,
                access=element_details.get('access', 'public'),
                is_static=element_details.get('static', False),
                is_const=element_details.get('const', False),
                is_virtual=element_details.get('virtual', False),
                is_inline=element_details.get('inline', False),
                is_explicit=element_details.get('explicit', False),
                is_constexpr=element_details.get('constexpr', False),
                is_noexcept=element_details.get('noexcept', False),
                namespace=element_details.get('namespace', ''),
                template_specialization=element_details.get('specialization', '')
            )
            
            # Parser les tags selon le type de commentaire
            if comment_type in ["doxygen", "javadoc", "qt", "triple_slash"]:
                self._parse_doxygen_tags(comment_text, doc_comment)
            elif comment_type == "section":
                # Les sections n'ont pas de tags Doxygen standard
                pass
        
        return doc_comment
    
    def _parse_doxygen_tags(self, comment_text: str, doc_comment: DocComment):
        """Parse tous les tags Doxygen dans le commentaire"""
        
        # @brief
        match = self.tag_patterns['brief'].search(comment_text)
        if match:
            doc_comment.brief = self._clean_text(match.group(1))
        
        # @param
        for match in re.finditer(self.tag_patterns['param'], comment_text):
            direction = match.group(1) or ""  # [in], [out], [in,out]
            param_name = match.group(2)
            param_desc = self._clean_text(match.group(3))
            
            doc_comment.params.append(Parameter(
                name=param_name,
                type="",  # Type sera extrait du code
                description=param_desc,
                direction=direction
            ))
        
        # @tparam (template parameters)
        for match in re.finditer(self.tag_patterns['tparam'], comment_text):
            param_name = match.group(1)
            param_desc = self._clean_text(match.group(2))
            
            # Détecter une valeur par défaut
            default_value = ""
            if "=" in param_desc:
                parts = param_desc.split("=", 1)
                param_desc = parts[0].strip()
                default_value = parts[1].strip()
            
            doc_comment.template_params.append(TemplateParameter(
                name=param_name,
                description=param_desc,
                default_value=default_value
            ))
        
        # @return
        match = self.tag_patterns['return'].search(comment_text)
        if match:
            doc_comment.returns = self._clean_text(match.group(1))
        
        # @retval
        for match in re.finditer(self.tag_patterns['retval'], comment_text):
            value = match.group(1)
            description = self._clean_text(match.group(2))
            doc_comment.return_values[value] = description
        
        # @throw/@throws
        for match in re.finditer(self.tag_patterns['throw'], comment_text):
            doc_comment.throws.append(self._clean_text(match.group(1)))
        
        # @example + @code
        for match in re.finditer(self.tag_patterns['code'], comment_text):
            code_example = match.group(1).strip()
            doc_comment.examples.append(code_example)
        
        # @note
        for match in re.finditer(self.tag_patterns['note'], comment_text):
            doc_comment.notes.append(self._clean_text(match.group(1)))
        
        # @warning
        for match in re.finditer(self.tag_patterns['warning'], comment_text):
            doc_comment.warnings.append(self._clean_text(match.group(1)))
        
        # @see et @sa
        for pattern_name in ['see', 'sa']:
            for match in re.finditer(self.tag_patterns[pattern_name], comment_text):
                doc_comment.see_also.append(self._clean_text(match.group(1)))
        
        # @since
        match = self.tag_patterns['since'].search(comment_text)
        if match:
            doc_comment.since = self._clean_text(match.group(1))
        
        # @deprecated
        match = self.tag_patterns['deprecated'].search(comment_text)
        if match:
            doc_comment.deprecated = self._clean_text(match.group(1))
        
        # @author
        match = self.tag_patterns['author'].search(comment_text)
        if match:
            doc_comment.author = self._clean_text(match.group(1))
        
        # @date
        match = self.tag_patterns['date'].search(comment_text)
        if match:
            doc_comment.date = self._clean_text(match.group(1))
        
        # @complexity
        match = self.tag_patterns['complexity'].search(comment_text)
        if match:
            doc_comment.complexity = self._clean_text(match.group(1))
        
        # @threadsafe / @notthreadsafe
        if self.tag_patterns['threadsafe'].search(comment_text):
            doc_comment.thread_safety = "Thread-safe"
        elif self.tag_patterns['notthreadsafe'].search(comment_text):
            doc_comment.thread_safety = "Not thread-safe"
        
        # Description (tout ce qui n'est pas un tag)
        # Pour les commentaires Doxygen, la description est avant le premier @tag
        if not doc_comment.brief:
            # Extraire la première ligne comme brief
            lines = comment_text.split('\n')
            for line in lines:
                clean_line = self._clean_text(line)
                if clean_line and not clean_line.startswith('@'):
                    doc_comment.brief = clean_line
                    break
        
        # Description complète
        desc_lines = []
        in_tag = False
        for line in comment_text.split('\n'):
            clean_line = self._clean_text(line)
            if clean_line.startswith('@'):
                in_tag = True
                continue
            if not in_tag and clean_line and clean_line != doc_comment.brief:
                desc_lines.append(clean_line)
        
        if desc_lines:
            doc_comment.description = ' '.join(desc_lines)
    
    def _clean_text(self, text: str) -> str:
        """Nettoie le texte extrait"""
        # Enlever les * au début des lignes
        text = re.sub(r'^\s*\*+\s*', '', text, flags=re.MULTILINE)
        # Enlever les / au début des lignes
        text = re.sub(r'^\s*/+\s*', '', text, flags=re.MULTILINE)
        # Enlever espaces multiples
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _identify_element(self, code: str) -> Optional[Tuple[CommentType, str, Dict]]:
        """Identifie le type d'élément C++ et son nom"""
        
        code = code.strip()
        details = {}
        
        # Détecter access specifier (public/private/protected)
        if 'private:' in code or code.startswith('private'):
            details['access'] = 'private'
        elif 'protected:' in code or code.startswith('protected'):
            details['access'] = 'protected'
        else:
            details['access'] = 'public'
        
        # Détecter modifiers
        details['static'] = 'static ' in code
        details['const'] = ' const' in code or code.startswith('const ')
        details['virtual'] = 'virtual ' in code
        details['inline'] = 'inline ' in code
        details['explicit'] = 'explicit ' in code
        details['constexpr'] = 'constexpr ' in code
        details['noexcept'] = 'noexcept' in code
        
        # Template class/struct
        if 'template<' in code:
            details['template'] = True
            # Chercher la spécialisation
            specialization_match = re.search(r'template<.*?>\s*(class|struct|typename)\s+(\w+)', code)
            if specialization_match:
                element_type = specialization_match.group(1)
                element_name = specialization_match.group(2)
                
                # Extraire les paramètres de template
                template_match = re.search(r'template<(.+?)>', code)
                if template_match:
                    details['template_params'] = template_match.group(1)
                
                if element_type == 'class':
                    return (CommentType.CLASS, element_name, details)
                elif element_type == 'struct':
                    return (CommentType.STRUCT, element_name, details)
                elif element_type == 'typename':
                    return (CommentType.TEMPLATE, element_name, details)
        
        # Union
        match = re.search(r'union\s+(\w+)', code)
        if match:
            return (CommentType.UNION, match.group(1), details)
        
        # Class avec potentiellement NK_API
        match = re.search(r'class\s+(?:NK_API\s+)?(\w+)', code)
        if match:
            return (CommentType.CLASS, match.group(1), details)
        
        # Struct avec potentiellement NK_API
        match = re.search(r'struct\s+(?:NK_API\s+)?(\w+)', code)
        if match:
            return (CommentType.STRUCT, match.group(1), details)
        
        # Enum class
        match = re.search(r'enum\s+class\s+(\w+)', code)
        if match:
            return (CommentType.ENUM, match.group(1), details)
        
        # Enum
        match = re.search(r'enum\s+(\w+)', code)
        if match:
            return (CommentType.ENUM, match.group(1), details)
        
        # Function/Method - détection améliorée
        # Pattern pour fonction/méthode : [type] [name]([params])
        # Supporte les templates: template<...> type name(...)
        func_pattern = r'(?:template\s*<[^>]*>\s*)?(?:(?:static|virtual|inline|explicit|constexpr)\s+)*(\w+(?:<[^>]+>)?(?:\s*\*|\s*&)?)\s+(\w+)\s*\('
        match = re.search(func_pattern, code)
        if match:
            return_type = match.group(1)
            func_name = match.group(2)
            
            # Vérifier si c'est un constructeur/destructeur
            if func_name.startswith('~'):
                return (CommentType.METHOD, func_name, details)
            elif '::' in code and func_name == code.split('::')[-2].strip():
                # Constructeur
                return (CommentType.METHOD, func_name, details)
            else:
                return (CommentType.FUNCTION, func_name, details)
        
        # Variable/Member
        # Pattern : [type] [name];
        var_pattern = r'(?:static\s+)?(?:const\s+)?(\w+(?:<[^>]+>)?(?:\s*\*|\s*&)?)\s+(\w+)\s*[;=]'
        match = re.search(var_pattern, code)
        if match:
            return (CommentType.VARIABLE, match.group(2), details)
        
        # Namespace
        match = re.search(r'namespace\s+(\w+)', code)
        if match:
            return (CommentType.NAMESPACE, match.group(1), details)
        
        # Typedef
        match = re.search(r'typedef\s+.+\s+(\w+)', code)
        if match:
            return (CommentType.TYPEDEF, match.group(1), details)
        
        # Using (alias moderne)
        match = re.search(r'using\s+(\w+)\s*=', code)
        if match:
            return (CommentType.TYPEDEF, match.group(1), details)
        
        # Macro
        match = re.search(r'#define\s+(\w+)', code)
        if match:
            return (CommentType.MACRO, match.group(1), details)
        
        # Template function
        if 'template<' in code and '(' in code:
            # C'est une fonction template
            func_match = re.search(r'(\w+)\s*\(', code)
            if func_match:
                return (CommentType.FUNCTION, func_match.group(1), details)
        
        return None
    
    def _get_code_after_comment(self, content: str, comment_line: int) -> str:
        """Récupère le code qui suit un commentaire"""
        
        lines = content.split('\n')
        
        # Trouver la ligne après le commentaire
        code_start = comment_line
        while code_start < len(lines):
            line = lines[code_start].strip()
            # Ignorer lignes vides et commentaires
            if line and not line.startswith('//') and not line.startswith('/*') and not line.startswith('*'):
                break
            code_start += 1
        
        if code_start >= len(lines):
            return ""
        
        # Récupérer plusieurs lignes de code (max 20 pour capturer les templates)
        code_lines = []
        for i in range(code_start, min(code_start + 20, len(lines))):
            code_lines.append(lines[i])
        
        return '\n'.join(code_lines)
    
    def _extract_includes(self, content: str) -> List[str]:
        """Extrait les #include"""
        includes = []
        for match in re.finditer(r'#include\s+[<"](.+?)[>"]', content):
            includes.append(match.group(1))
        return includes
    
    def _extract_namespaces(self, content: str) -> List[str]:
        """Extrait les namespaces déclarés"""
        namespaces = []
        for match in re.finditer(r'namespace\s+(\w+)\s*\{', content):
            namespaces.append(match.group(1))
        return namespaces
    
    def _extract_file_header(self, content: str) -> Optional[Dict]:
        """Extrait la documentation du header du fichier avec différents formats"""
        
        # Chercher dans les 100 premières lignes
        lines = content.split('\n')[:100]
        content_start = '\n'.join(lines)
        
        # Format 1: Standard avec FICHIER: DESCRIPTION: etc.
        match = re.search(
            r'//\s*-{3,}.*?\n//\s*FICHIER:\s*(.+?)\n//\s*DESCRIPTION:\s*(.+?)\n//\s*AUTEUR:\s*(.+?)\n//\s*DATE:\s*(.+?)\n//\s*-{3,}',
            content_start, re.DOTALL
        )
        
        if match:
            return {
                'filename': match.group(1).strip(),
                'description': match.group(2).strip(),
                'author': match.group(3).strip(),
                'date': match.group(4).strip()
            }
        
        # Format 2: Commentaire Doxygen au début du fichier
        doxygen_match = re.search(r'/\*\*\s*(.*?)\*/', content_start, re.DOTALL)
        if doxygen_match:
            comment_text = doxygen_match.group(1)
            result = {}
            
            # Extraire @file
            file_match = re.search(r'@file\s+(.+?)(?=\n|@|\*/)', comment_text)
            if file_match:
                result['filename'] = file_match.group(1).strip()
            
            # Extraire @brief
            brief_match = re.search(r'@brief\s+(.+?)(?=\n|@|\*/)', comment_text)
            if brief_match:
                result['description'] = brief_match.group(1).strip()
            
            # Extraire @author
            author_match = re.search(r'@author\s+(.+?)(?=\n|@|\*/)', comment_text)
            if author_match:
                result['author'] = author_match.group(1).strip()
            
            # Extraire @date
            date_match = re.search(r'@date\s+(.+?)(?=\n|@|\*/)', comment_text)
            if date_match:
                result['date'] = date_match.group(1).strip()
            
            return result if result else None
        
        return None


# ============================================================================
# GÉNÉRATEUR MARKDOWN AMÉLIORÉ
# ============================================================================

class MarkdownGenerator:
    """Génère la documentation en Markdown avec structure complète"""
    
    def __init__(self, project_doc: ProjectDocumentation):
        self.project_doc = project_doc
    
    def generate(self, output_dir: Path, split_by_namespace: bool = True):
        """Génère les fichiers Markdown avec structure complète"""
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Index principal (page d'accueil)
        self._generate_index(output_dir / "index.md")
        
        # Table des matières
        self._generate_table_of_contents(output_dir / "SUMMARY.md")
        
        # Documentation par namespace
        if split_by_namespace and self.project_doc.index_by_namespace:
            self._generate_by_namespace(output_dir)
        
        # Documentation par type
        if self.project_doc.index_by_type:
            self._generate_by_type(output_dir)
        
        # Documentation par fichier
        if self.project_doc.files:
            self._generate_by_file(output_dir)
        
        # Page API complète
        self._generate_api_page(output_dir / "api.md")
        
        # Page de recherche
        self._generate_search_page(output_dir / "search.md")
        
        # Page de statistiques détaillées
        self._generate_stats_page(output_dir / "stats.md")
        
        print(f"✅ Documentation Markdown générée dans: {output_dir}")
    
    def _generate_index(self, output_file: Path):
        """Génère la page d'index principale"""
        
        total_items = sum(len(items) for items in self.project_doc.index_by_type.values())
        total_files = len(self.project_doc.files)
        
        md = f"""# {self.project_doc.project_name} - Documentation API

> 🚀 Généré automatiquement le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

![Documentation Status](https://img.shields.io/badge/Documentation-Complete-brightgreen)
![Version](https://img.shields.io/badge/Version-{VERSION}-blue)
![Elements](https://img.shields.io/badge/Elements-{total_items}-orange)
![Files](https://img.shields.io/badge/Files-{total_files}-green)

## 📋 Vue d'ensemble

Cette documentation a été générée automatiquement depuis les commentaires du code source. 
Elle couvre toutes les classes, fonctions, structures et autres éléments documentés.

## 📊 Statistiques rapides

| Catégorie | Nombre |
|-----------|--------|
| 📁 Fichiers analysés | {total_files} |
| 🧩 Éléments documentés | {total_items} |
| 🗂️ Namespaces | {len(self.project_doc.index_by_namespace)} |
| ⚙️ Fonctions globales | {len(self.project_doc.global_functions)} |
| 📦 Variables globales | {len(self.project_doc.global_variables)} |

## 🎯 Répartition par type

"""
        
        # Par type avec icônes
        for doc_type, items in sorted(self.project_doc.index_by_type.items(), 
                                      key=lambda x: (-len(x[1]), x[0].value)):
            type_icon = self._get_type_icon(doc_type)
            md += f"- {type_icon} **{doc_type.value.capitalize()}s:** {len(items)} éléments\n"
        
        md += f"""
## 🔍 Navigation

### Vues principales
- [📖 Table des matières](SUMMARY.md)
- [🔧 API complète](api.md)
- [🔍 Recherche alphabétique](search.md)
- [📊 Statistiques détaillées](stats.md)

### Naviguer par catégorie
"""
        
        if self.project_doc.files:
            md += "- [📁 Par fichier](files/index.md)\n"
        
        if self.project_doc.index_by_namespace:
            md += "- [🗂️ Par namespace](namespaces/index.md)\n"
        
        if self.project_doc.index_by_type:
            md += "- [🎯 Par type](types/index.md)\n"
        
        md += f"""
## 📚 Structure de documentation

```
docs/
├── index.md              # Cette page
├── SUMMARY.md           # Table des matières complète
├── api.md               # Documentation API complète
├── search.md            # Page de recherche
├── stats.md             # Statistiques détaillées
├── files/              # Documentation par fichier
│   ├── index.md
│   └── *.md
├── namespaces/         # Documentation par namespace
│   ├── index.md
│   └── *.md
└── types/             # Documentation par type
    ├── index.md
    └── *.md
```

## 🚀 Comment utiliser cette documentation

### Pour les développeurs
1. **Chercher un élément spécifique** : Utilisez la [page de recherche](search.md)
2. **Explorer par namespace** : Parcourez les éléments logiquement groupés
3. **Voir le code source** : Chaque élément a un lien vers sa définition

### Pour les nouveaux arrivants
1. **Commencer par l'[API complète](api.md)** pour une vue d'ensemble
2. **Consulter les [statistiques](stats.md)** pour comprendre la taille du projet
3. **Explorer les [fichiers principaux](files/index.md)**

## 📝 Style de documentation

Cette documentation est générée à partir des commentaires suivants :
- **Commentaires Doxygen** : `/** ... */` avec tags `@param`, `@return`, etc.
- **Commentaires de section** : `// -----` avec titres comme `CLASSE:`, `ENUMÉRATION:`
- **Commentaires inline** : `///` pour la documentation simple

## 🔗 Liens utiles

- [Code source du projet]()
- [Guide de contribution]()
- [Style de codage]()
- [Tests unitaires]()

---

*Documentation générée avec ❤️ par Jenga Documentation Extractor v{VERSION}*

**Dernière mise à jour** : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        output_file.write_text(md, encoding='utf-8')
        print(f"✅ Généré: index.md")
    
    def _generate_table_of_contents(self, output_file: Path):
        """Génère la table des matières complète"""
        
        total_items = sum(len(items) for items in self.project_doc.index_by_type.values())
        
        md = f"""# 📖 Table des matières - {self.project_doc.project_name}

## 📚 Pages principales

- [🏠 Accueil](index.md) - Page principale avec vue d'ensemble
- [🔧 API Complète](api.md) - Tous les éléments documentés
- [🔍 Recherche](search.md) - Recherche alphabétique
- [📊 Statistiques](stats.md) - Métriques et analyses

## 📁 Documentation par fichier

*{len(self.project_doc.files)} fichiers documentés*

"""
        
        if self.project_doc.files:
            # Trier les fichiers par nom
            for file_doc in sorted(self.project_doc.files, key=lambda x: x.file_name):
                safe_name = file_doc.file_name.replace('.', '_').replace(' ', '_')
                element_count = len(file_doc.comments)
                
                # Ajouter une icône selon le type de fichier
                if file_doc.file_name.endswith('.h'):
                    icon = "📄"
                elif file_doc.file_name.endswith('.cpp'):
                    icon = "⚙️"
                else:
                    icon = "📝"
                
                md += f"- {icon} [{file_doc.file_name}](files/{safe_name}.md) ({element_count} éléments)\n"
        else:
            md += "*Aucun fichier avec documentation*\n"
        
        md += "\n## 🗂️ Documentation par namespace\n\n"
        
        if self.project_doc.index_by_namespace:
            # Trier les namespaces
            namespace_items = list(self.project_doc.index_by_namespace.items())
            namespace_items.sort(key=lambda x: x[0] if x[0] != "__global__" else "")
            
            for namespace, comments in namespace_items:
                if namespace == "__global__":
                    md += f"- 🌍 [Global](namespaces/global.md) ({len(comments)} éléments)\n"
                else:
                    ns_safe = namespace.replace('::', '_')
                    md += f"- 🗂️ [`{namespace}`](namespaces/{ns_safe}.md) ({len(comments)} éléments)\n"
        else:
            md += "*Aucun namespace avec documentation*\n"
        
        md += "\n## 🎯 Documentation par type\n\n"
        
        if self.project_doc.index_by_type:
            for doc_type, items in sorted(self.project_doc.index_by_type.items(), 
                                         key=lambda x: (-len(x[1]), x[0].value)):
                type_icon = self._get_type_icon(doc_type)
                md += f"- {type_icon} [{doc_type.value.capitalize()}s](types/{doc_type.value}s.md) ({len(items)} éléments)\n"
        else:
            md += "*Aucun type avec documentation*\n"
        
        md += f"""
## 📊 Résumé statistique

| Métrique | Valeur |
|----------|--------|
| Total d'éléments | {total_items} |
| Fichiers analysés | {len(self.project_doc.files)} |
| Namespaces | {len(self.project_doc.index_by_namespace)} |
| Types différents | {len(self.project_doc.index_by_type)} |

## 🔍 Recherche rapide

### Par première lettre
"""
        
        if total_items > 0:
            # Index alphabétique
            all_comments = []
            for comments in self.project_doc.index_by_type.values():
                all_comments.extend(comments)
            
            letters = set()
            for comment in all_comments:
                if comment.name:
                    letters.add(comment.name[0].upper())
            
            for letter in sorted(letters):
                md += f"- **{letter}** : Voir la [page de recherche](search.md#{letter.lower()})\n"
        else:
            md += "*Aucun élément documenté*\n"
        
        md += f"""
## 🚀 Prochaines étapes

1. **Explorer l'API** : Commencez par [api.md](api.md) pour une vue complète
2. **Chercher un élément** : Utilisez [search.md](search.md) pour trouver rapidement
3. **Naviguer par fichier** : Consultez [files/index.md](files/index.md) pour voir la structure

---

*Table des matières générée le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Total : {total_items} éléments dans {len(self.project_doc.files)} fichiers*
"""
        
        output_file.write_text(md, encoding='utf-8')
        print(f"✅ Généré: SUMMARY.md")
    
    def _generate_by_namespace(self, output_dir: Path):
        """Génère documentation organisée par namespace"""
        
        ns_dir = output_dir / "namespaces"
        ns_dir.mkdir(exist_ok=True)
        
        # Index des namespaces
        index_md = f"""# 🗂️ Documentation par Namespace

> {len(self.project_doc.index_by_namespace)} namespaces documentés

## 📋 Liste des namespaces

"""
        
        namespace_items = list(self.project_doc.index_by_namespace.items())
        namespace_items.sort(key=lambda x: x[0] if x[0] != "__global__" else "")
        
        for namespace, comments in namespace_items:
            if namespace == "__global__":
                index_md += f"- 🌍 **[Global](global.md)** - {len(comments)} éléments (sans namespace)\n"
            else:
                ns_safe = namespace.replace('::', '_')
                index_md += f"- 🗂️ **[`{namespace}`]({ns_safe}.md)** - {len(comments)} éléments\n"
        
        index_md += f"""
## 📊 Statistiques globales

| Namespace | Éléments | Types principaux |
|-----------|----------|------------------|
"""
        
        for namespace, comments in namespace_items:
            # Compter les types dans ce namespace
            type_counts = {}
            for comment in comments:
                if comment.type not in type_counts:
                    type_counts[comment.type] = 0
                type_counts[comment.type] += 1
            
            # Les 3 types les plus courants
            top_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            type_str = ", ".join([f"{self._get_type_icon(t)} {t.value}s" for t, _ in top_types])
            
            if namespace == "__global__":
                display_name = "Global"
            else:
                display_name = f"`{namespace}`"
            
            index_md += f"| {display_name} | {len(comments)} | {type_str} |\n"
        
        (ns_dir / "index.md").write_text(index_md, encoding='utf-8')
        
        # Générer chaque namespace
        for namespace, comments in namespace_items:
            if namespace == "__global__":
                ns_file = ns_dir / "global.md"
                ns_display = "🌍 Global (sans namespace)"
            else:
                ns_file = ns_dir / f"{namespace.replace('::', '_')}.md"
                ns_display = f"🗂️ Namespace `{namespace}`"
            
            self._generate_namespace_page(ns_file, namespace, comments, ns_display)
        
        print(f"✅ Généré: {len(self.project_doc.index_by_namespace)} fichiers namespace")
    
    def _generate_namespace_page(self, output_file: Path, namespace: str, 
                                comments: List[DocComment], title: str):
        """Génère une page de documentation pour un namespace"""
        
        md = f"""# {title}

> {len(comments)} éléments documentés

[← Retour à l'index des namespaces](index.md) | [🏠 Accueil](../index.md)

## 📊 Statistiques du namespace

"""
        
        # Compter les types
        type_counts = {}
        for comment in comments:
            if comment.type not in type_counts:
                type_counts[comment.type] = 0
            type_counts[comment.type] += 1
        
        if type_counts:
            md += "| Type | Nombre | Pourcentage |\n"
            md += "|------|--------|-------------|\n"
            
            total = len(comments)
            for doc_type, count in sorted(type_counts.items(), key=lambda x: (-x[1], x[0].value)):
                percentage = (count / total) * 100
                type_icon = self._get_type_icon(doc_type)
                md += f"| {type_icon} {doc_type.value.capitalize()} | {count} | {percentage:.1f}% |\n"
            
            md += "\n"
        
        # Grouper par type avec des sections dédiées
        by_type = {}
        for comment in comments:
            if comment.type not in by_type:
                by_type[comment.type] = []
            by_type[comment.type].append(comment)
        
        for doc_type, items in sorted(by_type.items(), key=lambda x: (-len(x[1]), x[0].value)):
            type_icon = self._get_type_icon(doc_type)
            md += f"## {type_icon} {doc_type.value.capitalize()}s ({len(items)})\n\n"
            
            for item in sorted(items, key=lambda x: x.name.lower()):
                md += self._format_doc_comment(item, include_navigation=True)
                md += "\n---\n\n"
        
        # Pied de page avec navigation
        md += f"""
## 🔗 Navigation

- [← Retour à l'index des namespaces](index.md)
- [🏠 Accueil](../index.md)
- [🔧 API complète](../api.md)
- [🔍 Recherche](../search.md)

---

*Namespace `{namespace}` - {len(comments)} éléments*
*Documentation générée le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        output_file.write_text(md, encoding='utf-8')
    
    def _generate_by_type(self, output_dir: Path):
        """Génère documentation organisée par type"""
        
        types_dir = output_dir / "types"
        types_dir.mkdir(exist_ok=True)
        
        # Index des types
        index_md = f"""# 🎯 Documentation par Type

> {len(self.project_doc.index_by_type)} types d'éléments documentés

## 📋 Liste des types

"""
        
        for doc_type, items in sorted(self.project_doc.index_by_type.items(), 
                                     key=lambda x: (-len(x[1]), x[0].value)):
            type_icon = self._get_type_icon(doc_type)
            index_md += f"- {type_icon} **[{doc_type.value.capitalize()}s]({doc_type.value}s.md)** - {len(items)} éléments\n"
        
        index_md += f"""
## 📊 Répartition des types

| Type | Nombre | Pourcentage |
|------|--------|-------------|
"""
        
        total_items = sum(len(items) for items in self.project_doc.index_by_type.values())
        
        for doc_type, items in sorted(self.project_doc.index_by_type.items(), 
                                     key=lambda x: (-len(x[1]), x[0].value)):
            percentage = (len(items) / total_items) * 100 if total_items > 0 else 0
            type_icon = self._get_type_icon(doc_type)
            index_md += f"| {type_icon} {doc_type.value.capitalize()} | {len(items)} | {percentage:.1f}% |\n"
        
        (types_dir / "index.md").write_text(index_md, encoding='utf-8')
        
        # Générer chaque type
        for doc_type, comments in self.project_doc.index_by_type.items():
            type_file = types_dir / f"{doc_type.value}s.md"
            self._generate_type_page(type_file, doc_type, comments)
        
        print(f"✅ Généré: {len(self.project_doc.index_by_type)} fichiers type")
    
    def _generate_type_page(self, output_file: Path, doc_type: CommentType, 
                           comments: List[DocComment]):
        """Génère une page de documentation pour un type spécifique"""
        
        type_icon = self._get_type_icon(doc_type)
        type_name = doc_type.value.capitalize()
        
        md = f"""# {type_icon} {type_name}s

> {len(comments)} éléments de type {type_name.lower()}

[← Retour à l'index des types](index.md) | [🏠 Accueil](../index.md)

## 📊 Statistiques

"""
        
        # Grouper par namespace
        by_namespace = {}
        for comment in comments:
            ns = comment.namespace or "__global__"
            if ns not in by_namespace:
                by_namespace[ns] = []
            by_namespace[ns].append(comment)
        
        if by_namespace:
            md += "| Namespace | Nombre | Pourcentage |\n"
            md += "|-----------|--------|-------------|\n"
            
            total = len(comments)
            for namespace, items in sorted(by_namespace.items(), 
                                          key=lambda x: (-len(x[1]), x[0] if x[0] != "__global__" else "")):
                percentage = (len(items) / total) * 100
                
                if namespace == "__global__":
                    display_name = "Global"
                else:
                    display_name = f"`{namespace}`"
                
                md += f"| {display_name} | {len(items)} | {percentage:.1f}% |\n"
            
            md += "\n"
        
        # Lister les éléments par namespace
        for namespace, items in sorted(by_namespace.items(), 
                                      key=lambda x: (-len(x[1]), x[0] if x[0] != "__global__" else "")):
            if namespace == "__global__":
                md += "## 🌍 Global\n\n"
            else:
                md += f"## 🗂️ Namespace `{namespace}`\n\n"
            
            for item in sorted(items, key=lambda x: x.name.lower()):
                md += self._format_doc_comment(item, include_navigation=True)
                md += "\n---\n\n"
        
        # Pied de page
        md += f"""
## 🔗 Navigation

- [← Retour à l'index des types](index.md)
- [🏠 Accueil](../index.md)
- [🗂️ Par namespace](../namespaces/index.md)
- [📁 Par fichier](../files/index.md)

---

*{type_name}s - {len(comments)} éléments*
*Documentation générée le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        output_file.write_text(md, encoding='utf-8')
    
    def _generate_by_file(self, output_dir: Path):
        """Génère documentation organisée par fichier"""
        
        files_dir = output_dir / "files"
        files_dir.mkdir(exist_ok=True)
        
        # Index des fichiers
        index_md = f"""# 📁 Documentation par Fichier

> {len(self.project_doc.files)} fichiers documentés

## 📋 Liste des fichiers

"""
        
        for file_doc in sorted(self.project_doc.files, key=lambda x: x.file_name):
            safe_name = file_doc.file_name.replace('.', '_').replace(' ', '_')
            element_count = len(file_doc.comments)
            
            # Déterminer l'icône selon l'extension
            if file_doc.file_name.endswith('.h'):
                icon = "📄"
            elif file_doc.file_name.endswith('.cpp'):
                icon = "⚙️"
            elif file_doc.file_name.endswith('.c'):
                icon = "🔧"
            else:
                icon = "📝"
            
            index_md += f"- {icon} **[{file_doc.file_name}]({safe_name}.md)** - {element_count} éléments\n"
        
        (files_dir / "index.md").write_text(index_md, encoding='utf-8')
        
        # Générer chaque fichier
        for file_doc in self.project_doc.files:
            safe_name = file_doc.file_name.replace('.', '_').replace(' ', '_')
            file_file = files_dir / f"{safe_name}.md"
            self._generate_file_page(file_file, file_doc)
        
        print(f"✅ Généré: {len(self.project_doc.files)} fichiers source")
    
    def _generate_file_page(self, output_file: Path, file_doc: FileDocumentation):
        """Génère une page de documentation pour un fichier"""
        
        md = f"""# 📄 {file_doc.file_name}

[← Retour à l'index des fichiers](index.md) | [🏠 Accueil](../index.md)

## 📋 Métadonnées

"""
        
        # Métadonnées du fichier
        if file_doc.description:
            md += f"**Description:** {file_doc.description}\n\n"
        
        metadata = []
        if file_doc.author:
            metadata.append(f"**Auteur:** {file_doc.author}")
        if file_doc.date:
            metadata.append(f"**Date:** {file_doc.date}")
        if file_doc.version:
            metadata.append(f"**Version:** {file_doc.version}")
        
        if metadata:
            md += " | ".join(metadata) + "\n\n"
        
        md += f"**Chemin:** `{file_doc.file_path}`\n\n"
        
        # Includes
        if file_doc.includes:
            md += "## 📦 Fichiers inclus\n\n"
            for inc in file_doc.includes:
                md += f"- `{inc}`\n"
            md += "\n"
        
        # Namespaces
        if file_doc.namespaces:
            md += "## 🗂️ Namespaces déclarés\n\n"
            for ns in file_doc.namespaces:
                md += f"- `{ns}`\n"
            md += "\n"
        
        # Éléments documentés
        md += f"## 🎯 Éléments documentés ({len(file_doc.comments)})\n\n"
        
        if not file_doc.comments:
            md += "*Aucun élément documenté dans ce fichier*\n\n"
        else:
            # Grouper par type
            by_type = {}
            for comment in file_doc.comments:
                if comment.type not in by_type:
                    by_type[comment.type] = []
                by_type[comment.type].append(comment)
            
            for doc_type, items in sorted(by_type.items(), key=lambda x: (-len(x[1]), x[0].value)):
                type_icon = self._get_type_icon(doc_type)
                md += f"### {type_icon} {doc_type.value.capitalize()}s ({len(items)})\n\n"
                
                for comment in sorted(items, key=lambda x: x.name.lower()):
                    md += self._format_doc_comment(comment, include_navigation=True)
                    md += "\n---\n\n"
        
        # Pied de page
        md += f"""
## 🔗 Navigation

- [← Retour à l'index des fichiers](index.md)
- [🏠 Accueil](../index.md)
- [🗂️ Par namespace](../namespaces/index.md)
- [🎯 Par type](../types/index.md)

---

*Fichier: {file_doc.file_name} - {len(file_doc.comments)} éléments*
*Documentation générée le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        output_file.write_text(md, encoding='utf-8')
    
    def _generate_api_page(self, output_file: Path):
        """Génère une page API complète"""
        
        total_items = sum(len(items) for items in self.project_doc.index_by_type.values())
        
        md = f"""# 🔧 API Complète - {self.project_doc.project_name}

> Documentation complète de {total_items} éléments

[🏠 Accueil](index.md) | [🔍 Recherche](search.md)

## 📋 Vue d'ensemble

Cette page présente tous les éléments de l'API organisés par type et namespace.

**Total d'éléments:** {total_items}

## 🎯 Index par type

"""
        
        if self.project_doc.index_by_type:
            # Index par type avec liens d'ancrage
            for doc_type, items in sorted(self.project_doc.index_by_type.items(), 
                                         key=lambda x: (-len(x[1]), x[0].value)):
                type_icon = self._get_type_icon(doc_type)
                md += f"### {type_icon} [{doc_type.value.capitalize()}s](#{doc_type.value.lower()}) ({len(items)})\n\n"
            
            md += "\n---\n\n## 🔍 Détails par type\n\n"
            
            # Détails complets par type
            for doc_type, items in sorted(self.project_doc.index_by_type.items(), 
                                         key=lambda x: (-len(x[1]), x[0].value)):
                type_icon = self._get_type_icon(doc_type)
                md += f'<a name="{doc_type.value.lower()}"></a>\n'
                md += f"## {type_icon} {doc_type.value.capitalize()}s\n\n"
                
                # Grouper par namespace
                by_namespace = {}
                for comment in items:
                    ns = comment.namespace or "__global__"
                    if ns not in by_namespace:
                        by_namespace[ns] = []
                    by_namespace[ns].append(comment)
                
                for namespace, namespace_items in sorted(by_namespace.items(), 
                                                         key=lambda x: (-len(x[1]), x[0] if x[0] != "__global__" else "")):
                    if namespace == "__global__":
                        md += "### 🌍 Global\n\n"
                    else:
                        md += f"### 🗂️ Namespace `{namespace}`\n\n"
                    
                    for item in sorted(namespace_items, key=lambda x: x.name.lower()):
                        # Version simplifiée pour la page API
                        md += f"#### `{item.name}`\n\n"
                        
                        if item.brief:
                            md += f"*{item.brief}*\n\n"
                        
                        if item.description and item.description != item.brief:
                            md += f"{item.description}\n\n"
                        
                        # Métadonnées rapides
                        metadata = []
                        if item.access != "public":
                            metadata.append(f"`{item.access}`")
                        if item.is_static:
                            metadata.append("`static`")
                        if item.is_const:
                            metadata.append("`const`")
                        
                        if metadata:
                            md += " ".join(metadata) + "\n\n"
                        
                        md += f"*Défini dans: `{item.file_path}:{item.line_number}`*\n\n"
                        md += "---\n\n"
        else:
            md += "*Aucun élément documenté*\n\n"
        
        md += f"""
## 🔗 Navigation

- [🏠 Accueil](index.md)
- [📖 Table des matières](SUMMARY.md)
- [🔍 Recherche](search.md)
- [📊 Statistiques](stats.md)

---

*API complète - {total_items} éléments*
*Documentation générée le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        output_file.write_text(md, encoding='utf-8')
        print(f"✅ Généré: api.md")
    
    def _generate_search_page(self, output_file: Path):
        """Génère une page de recherche alphabétique"""
        
        all_comments = []
        for comments in self.project_doc.index_by_type.values():
            all_comments.extend(comments)
        
        md = f"""# 🔍 Recherche alphabétique

> Index de {len(all_comments)} éléments par ordre alphabétique

[🏠 Accueil](index.md) | [🔧 API complète](api.md)

## 📋 Comment utiliser

1. **Recherche rapide** : Utilisez Ctrl+F dans votre navigateur
2. **Navigation par lettre** : Cliquez sur une lettre ci-dessous
3. **Accès direct** : Les noms sont des liens vers les éléments

## 🔤 Index alphabétique

"""
        
        if all_comments:
            # Regrouper par première lettre
            by_letter = {}
            for comment in all_comments:
                if comment.name:
                    first_letter = comment.name[0].upper()
                    if first_letter not in by_letter:
                        by_letter[first_letter] = []
                    by_letter[first_letter].append(comment)
            
            # Menu de navigation par lettre
            md += "### Navigation rapide\n\n"
            for letter in sorted(by_letter.keys()):
                md += f"[{letter}](#letter-{letter.lower()}) "
            md += "\n\n---\n\n"
            
            # Liste complète par lettre
            for letter in sorted(by_letter.keys()):
                md += f'<a name="letter-{letter.lower()}"></a>\n'
                md += f"## {letter}\n\n"
                
                items = sorted(by_letter[letter], key=lambda x: x.name.lower())
                
                for item in items:
                    type_icon = self._get_type_icon(item.type)
                    ns_display = item.namespace if item.namespace else "global"
                    
                    md += f"- {type_icon} **`{item.name}`**"
                    md += f" *({item.type.value} dans `{ns_display}`)*"
                    
                    if item.brief:
                        md += f" — {item.brief}"
                    
                    md += "\n"
                
                md += "\n"
        else:
            md += "*Aucun élément documenté*\n\n"
        
        md += f"""
## 🔗 Navigation

- [🏠 Accueil](index.md)
- [🔧 API complète](api.md)
- [🗂️ Par namespace](namespaces/index.md)
- [🎯 Par type](types/index.md)

---

*Index alphabétique - {len(all_comments)} éléments*
*Documentation générée le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        output_file.write_text(md, encoding='utf-8')
        print(f"✅ Généré: search.md")
    
    def _generate_stats_page(self, output_file: Path):
        """Génère une page de statistiques détaillées"""
        
        total_items = sum(len(items) for items in self.project_doc.index_by_type.values())
        total_files = len(self.project_doc.files)
        
        md = f"""# 📊 Statistiques détaillées

> Analyse complète de la documentation

[🏠 Accueil](index.md) | [🔧 API complète](api.md)

## 📋 Vue d'ensemble

| Métrique | Valeur |
|----------|--------|
| 📁 Fichiers analysés | {total_files} |
| 🧩 Éléments documentés | {total_items} |
| 🗂️ Namespaces | {len(self.project_doc.index_by_namespace)} |
| 🎯 Types différents | {len(self.project_doc.index_by_type)} |
| ⚙️ Fonctions globales | {len(self.project_doc.global_functions)} |
| 📦 Variables globales | {len(self.project_doc.global_variables)} |

## 📈 Répartition par type

"""
        
        if total_items > 0:
            # Graphique ASCII simple pour la répartition
            max_count = max(len(items) for items in self.project_doc.index_by_type.values())
            
            for doc_type, items in sorted(self.project_doc.index_by_type.items(), 
                                         key=lambda x: (-len(x[1]), x[0].value)):
                type_icon = self._get_type_icon(doc_type)
                count = len(items)
                percentage = (count / total_items) * 100 if total_items > 0 else 0
                
                # Barre ASCII
                bar_length = int((count / max_count) * 50) if max_count > 0 else 0
                bar = "█" * bar_length + "░" * (50 - bar_length)
                
                md += f"**{type_icon} {doc_type.value.capitalize()}s** ({count})\n"
                md += f"`{bar}` {percentage:.1f}%\n\n"
        else:
            md += "*Aucune donnée disponible*\n\n"
        
        md += "## 🗂️ Répartition par namespace\n\n"
        
        if self.project_doc.index_by_namespace:
            namespace_items = list(self.project_doc.index_by_namespace.items())
            namespace_items.sort(key=lambda x: (-len(x[1]), x[0] if x[0] != "__global__" else ""))
            
            md += "| Namespace | Éléments | Pourcentage |\n"
            md += "|-----------|----------|-------------|\n"
            
            for namespace, items in namespace_items[:10]:  # Top 10
                percentage = (len(items) / total_items) * 100 if total_items > 0 else 0
                
                if namespace == "__global__":
                    display_name = "Global"
                else:
                    display_name = f"`{namespace}`"
                
                md += f"| {display_name} | {len(items)} | {percentage:.1f}% |\n"
            
            if len(namespace_items) > 10:
                md += f"| *{len(namespace_items) - 10} autres* | ... | ... |\n"
        else:
            md += "*Aucun namespace avec documentation*\n\n"
        
        md += "\n## 📁 Top 10 des fichiers\n\n"
        
        if self.project_doc.files:
            # Top 10 des fichiers avec le plus d'éléments
            sorted_files = sorted(self.project_doc.files, 
                                 key=lambda x: len(x.comments), 
                                 reverse=True)[:10]
            
            md += "| Fichier | Éléments | Pourcentage |\n"
            md += "|---------|----------|-------------|\n"
            
            for file_doc in sorted_files:
                percentage = (len(file_doc.comments) / total_items) * 100 if total_items > 0 else 0
                md += f"| `{file_doc.file_name}` | {len(file_doc.comments)} | {percentage:.1f}% |\n"
        else:
            md += "*Aucun fichier avec documentation*\n\n"
        
        # CORRECTION ICI : Calculer la moyenne d'abord, puis formater
        avg_elements = total_items / total_files if total_files > 0 else 0
        
        md += f"""
## 📊 Métriques avancées

### Densité de documentation
- **Éléments par fichier** : {avg_elements:.1f} (moyenne)
- **Fichiers avec documentation** : {sum(1 for f in self.project_doc.files if f.comments)}/{total_files}

### Complexité (estimée)
- **Méthodes par classe** : *Calcul en cours...*
- **Paramètres par fonction** : *Calcul en cours...*
- **Templates** : {len(self.project_doc.index_by_type.get(CommentType.TEMPLATE, []))}

## 🔍 Insights

"""
        
        # Générer des insights basés sur les statistiques
        if total_items > 0:
            # Insight 1: Type dominant
            dominant_type = max(self.project_doc.index_by_type.items(), 
                               key=lambda x: len(x[1]))
            md += f"1. **Type dominant** : {dominant_type[0].value.capitalize()}s ({len(dominant_type[1])} éléments)\n"
            
            # Insight 2: Namespace le plus peuplé
            if self.project_doc.index_by_namespace:
                namespace_items = list(self.project_doc.index_by_namespace.items())
                top_namespace = max(namespace_items, key=lambda x: len(x[1]))
                if top_namespace[0] != "__global__":
                    md += f"2. **Namespace principal** : `{top_namespace[0]}` ({len(top_namespace[1])} éléments)\n"
            
            # Insight 3: Fichier le plus documenté
            if self.project_doc.files:
                top_file = max(self.project_doc.files, key=lambda x: len(x.comments))
                md += f"3. **Fichier le plus documenté** : `{top_file.file_name}` ({len(top_file.comments)} éléments)\n"
        else:
            md += "*Aucune donnée pour générer des insights*\n"
        
        md += f"""
## 🔗 Navigation

- [🏠 Accueil](index.md)
- [🔧 API complète](api.md)
- [🔍 Recherche](search.md)
- [📖 Table des matières](SUMMARY.md)

---

*Statistiques générées le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Base de données: {total_items} éléments dans {total_files} fichiers*
"""
        
        output_file.write_text(md, encoding='utf-8')
        print(f"✅ Généré: stats.md")
    
    def _format_doc_comment(self, comment: DocComment, include_navigation: bool = True) -> str:
        """Formate un commentaire de documentation en Markdown"""
        
        type_icon = self._get_type_icon(comment.type)
        
        md = f"### {type_icon} `{comment.name}`\n\n"
        
        # Badges et métadonnées
        badges = []
        if comment.access != "public":
            badges.append(f"`{comment.access}`")
        if comment.is_static:
            badges.append("`static`")
        if comment.is_virtual:
            badges.append("`virtual`")
        if comment.is_const:
            badges.append("`const`")
        if comment.is_inline:
            badges.append("`inline`")
        if comment.is_constexpr:
            badges.append("`constexpr`")
        if comment.is_noexcept:
            badges.append("`noexcept`")
        if comment.deprecated:
            badges.append("`deprecated`")
        
        if badges:
            md += " ".join(badges) + "\n\n"
        
        # Brief
        if comment.brief:
            md += f"**{comment.brief}**\n\n"
        
        # Description
        if comment.description and comment.description != comment.brief:
            md += f"{comment.description}\n\n"
        
        # Template parameters
        if comment.template_params:
            md += "#### 📋 Paramètres de template\n\n"
            md += "| Paramètre | Description | Défaut |\n"
            md += "|-----------|-------------|--------|\n"
            for tparam in comment.template_params:
                default = tparam.default_value if tparam.default_value else "—"
                md += f"| `{tparam.name}` | {tparam.description} | `{default}` |\n"
            md += "\n"
        
        # Parameters
        if comment.params:
            md += "#### 📥 Paramètres\n\n"
            md += "| Paramètre | Direction | Description |\n"
            md += "|-----------|-----------|-------------|\n"
            for param in comment.params:
                direction = param.direction if param.direction else "in"
                md += f"| `{param.name}` | `{direction}` | {param.description} |\n"
            md += "\n"
        
        # Returns
        if comment.returns:
            md += f"#### 📤 Retour\n\n{comment.returns}\n\n"
        
        if comment.return_values:
            md += "#### 🎯 Valeurs de retour\n\n"
            for value, desc in comment.return_values.items():
                md += f"- `{value}`: {desc}\n"
            md += "\n"
        
        # Throws
        if comment.throws:
            md += "#### ⚠️ Exceptions\n\n"
            for throw in comment.throws:
                md += f"- {throw}\n"
            md += "\n"
        
        # Examples
        if comment.examples:
            md += "#### 💡 Exemples\n\n"
            for i, example in enumerate(comment.examples, 1):
                md += f"**Exemple {i}:**\n\n"
                md += f"```cpp\n{example}\n```\n\n"
        
        # Notes
        if comment.notes:
            md += "#### 📝 Notes\n\n"
            for note in comment.notes:
                md += f"> 📌 {note}\n\n"
        
        # Warnings
        if comment.warnings:
            md += "#### ⚠️ Avertissements\n\n"
            for warning in comment.warnings:
                md += f"> ⚠️ {warning}\n\n"
        
        # Complexity
        if comment.complexity:
            md += f"#### 🕒 Complexité\n\n{comment.complexity}\n\n"
        
        # Thread safety
        if comment.thread_safety:
            md += f"#### 🔒 Sécurité des threads\n\n{comment.thread_safety}\n\n"
        
        # See also
        if comment.see_also:
            md += "#### 🔗 Voir aussi\n\n"
            for see in comment.see_also:
                md += f"- {see}\n"
            md += "\n"
        
        # Metadata
        metadata = []
        if comment.since:
            metadata.append(f"**Depuis:** {comment.since}")
        if comment.author:
            metadata.append(f"**Auteur:** {comment.author}")
        if comment.date:
            metadata.append(f"**Date:** {comment.date}")
        
        if metadata:
            md += "*" + " | ".join(metadata) + "*\n\n"
        
        # Deprecated
        if comment.deprecated:
            md += f"> 🚫 **DÉPRÉCIÉ:** {comment.deprecated}\n\n"
        
        # Navigation
        if include_navigation:
            md += "#### 📍 Navigation\n\n"
            ns_display = comment.namespace if comment.namespace else "global"
            md += f"- **Fichier:** `{comment.file_path}:{comment.line_number}`\n"
            md += f"- **Namespace:** `{ns_display}`\n"
            md += f"- **Type:** {comment.type.value.capitalize()}\n"
            
            # Liens vers d'autres vues
            if comment.namespace:
                ns_safe = comment.namespace.replace('::', '_')
                md += f"- [Voir dans namespace](../namespaces/{ns_safe}.md)\n"
            
            md += f"- [Voir par type](../types/{comment.type.value}s.md)\n"
            
            # Trouver le fichier correspondant
            for file_doc in self.project_doc.files:
                if file_doc.file_path == comment.file_path:
                    safe_name = file_doc.file_name.replace('.', '_').replace(' ', '_')
                    md += f"- [Voir le fichier](../files/{safe_name}.md)\n"
                    break
        
        return md
    
    def _get_type_icon(self, comment_type: CommentType) -> str:
        """Retourne l'emoji/icône pour un type"""
        icons = {
            CommentType.CLASS: "🏛️",
            CommentType.STRUCT: "🏗️",
            CommentType.ENUM: "🔢",
            CommentType.UNION: "🤝",
            CommentType.FUNCTION: "⚙️",
            CommentType.METHOD: "🔧",
            CommentType.VARIABLE: "📦",
            CommentType.NAMESPACE: "🗂️",
            CommentType.FILE: "📄",
            CommentType.TYPEDEF: "📝",
            CommentType.MACRO: "🔣",
            CommentType.TEMPLATE: "🎨",
        }
        return icons.get(comment_type, "📌")


# ============================================================================
# MAIN EXTRACTOR
# ============================================================================

class DocumentationExtractor:
    """Extracteur principal de documentation"""
    
    def __init__(self, project_name: str, source_dirs: List[Path], 
                 include_private: bool = False, exclude_dirs: Optional[List[str]] = None):
        self.project_name = project_name
        self.source_dirs = source_dirs
        self.include_private = include_private
        self.exclude_dirs = exclude_dirs if exclude_dirs is not None else []
        self.parser = DocumentationParser()
    
    def extract(self) -> ProjectDocumentation:
        """Extrait la documentation de tous les fichiers"""
        
        project_doc = ProjectDocumentation(project_name=self.project_name)
        
        # Parcourir tous les fichiers
        all_files = []
        for source_dir in self.source_dirs:
            for ext in SUPPORTED_EXTENSIONS:
                files = source_dir.rglob(f"*{ext}")
                
                # Filtrer les répertoires exclus
                for file_path in files:
                    # Vérifier si le fichier est dans un répertoire exclu
                    exclude = False
                    for exclude_dir in self.exclude_dirs:
                        if exclude_dir in str(file_path):
                            exclude = True
                            break
                    
                    if not exclude:
                        all_files.append(file_path)
        
        print(f"📁 Analyse de {len(all_files)} fichiers...")
        
        for i, file_path in enumerate(all_files):
            print(f"  [{i+1}/{len(all_files)}] 📄 {file_path.name}...", end='\r')
            file_doc = self.parser.parse_file(file_path, self.include_private)
            
            if file_doc.comments:  # Ne garder que les fichiers avec documentation
                project_doc.files.append(file_doc)
                
                # Indexer par type et namespace
                for comment in file_doc.comments:
                    # Par type
                    if comment.type not in project_doc.index_by_type:
                        project_doc.index_by_type[comment.type] = []
                    project_doc.index_by_type[comment.type].append(comment)
                    
                    # Par namespace
                    ns = comment.namespace or "__global__"
                    if ns not in project_doc.index_by_namespace:
                        project_doc.index_by_namespace[ns] = []
                    project_doc.index_by_namespace[ns].append(comment)
                    
                    # Global functions/variables
                    if ns == "__global__":
                        if comment.type == CommentType.FUNCTION:
                            project_doc.global_functions.append(comment)
                        elif comment.type == CommentType.VARIABLE:
                            project_doc.global_variables.append(comment)
        
        if all_files:
            print()  # Nouvelle ligne après la barre de progression
        
        print(f"✅ {len(all_files)} fichiers analysés")
        
        # Statistiques
        total_comments = sum(len(f.comments) for f in project_doc.files)
        files_with_docs = sum(1 for f in project_doc.files if f.comments)
        
        print(f"📊 {total_comments} éléments documentés extraits")
        print(f"📁 {files_with_docs} fichiers avec documentation")
        
        return project_doc


def execute(args):
    """Main entry point for docs command"""
    
    # Load workspace
    workspace = load_workspace()
    if not workspace:
        Display.error("No workspace found. Run from workspace directory.")
        return 1
    
    parser = argparse.ArgumentParser(
        description="Extract documentation from workspace projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  jenga docs                   # Show documentation help
  jenga docs extract           # Extract from all projects
  jenga docs extract --project Engine  # Extract from specific project
  jenga docs stats             # Show documentation statistics
  jenga docs list              # List documented projects
  jenga docs clean             # Clean generated documentation
"""
    )
    
    # If no args, show help
    if not args:
        parser.print_help()
        return 0
    
    subparsers = parser.add_subparsers(
        dest='subcommand',
        help='Documentation operation'
    )
    
    # Extract command
    extract_parser = subparsers.add_parser(
        'extract',
        help='Extract documentation from source files'
    )
    
    extract_parser.add_argument(
        '--project',
        help='Specific project to extract (default: all projects)'
    )
    
    extract_parser.add_argument(
        '--output',
        default='docs',
        help='Output directory (default: docs/)'
    )
    
    extract_parser.add_argument(
        '--format',
        choices=['markdown', 'html', 'all'],
        default='markdown',
        help='Output format (default: markdown)'
    )
    
    extract_parser.add_argument(
        '--include-private',
        action='store_true',
        help='Include private/protected members'
    )
    
    extract_parser.add_argument(
        '--no-split-namespace',
        action='store_true',
        help='Do not split documentation by namespace'
    )
    
    extract_parser.add_argument(
        '--exclude-dirs',
        nargs='+',
        help='Directories to exclude from analysis'
    )
    
    extract_parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    extract_parser.add_argument(
        '--exclude-projects',
        nargs='+',
        help='Projects to exclude from extraction'
    )
    
    # Stats command
    stats_parser = subparsers.add_parser(
        'stats',
        help='Show documentation statistics'
    )
    
    stats_parser.add_argument(
        '--project',
        help='Specific project to show stats for'
    )
    
    stats_parser.add_argument(
        '--json',
        action='store_true',
        help='Output statistics as JSON'
    )
    
    # List command
    list_parser = subparsers.add_parser(
        'list',
        help='List documented projects'
    )
    
    # Clean command
    clean_parser = subparsers.add_parser(
        'clean',
        help='Clean generated documentation'
    )
    
    clean_parser.add_argument(
        '--project',
        help='Clean documentation for specific project'
    )
    
    clean_parser.add_argument(
        '--output',
        default='docs',
        help='Output directory to clean (default: docs/)'
    )
    
    # Version command
    version_parser = subparsers.add_parser(
        'version',
        help='Show version information'
    )
    
    # Help command
    help_parser = subparsers.add_parser(
        'help',
        help='Show help message'
    )
    
    # Parse arguments
    try:
        parsed = parser.parse_args(args)
    except SystemExit:
        return 1  # Error in argument parsing
    
    # Handle commands
    if parsed.subcommand == 'extract':
        return extract_command(parsed, workspace)
    elif parsed.subcommand == 'stats':
        return stats_command(parsed, workspace)
    elif parsed.subcommand == 'list':
        return list_command(parsed, workspace)
    elif parsed.subcommand == 'clean':
        return clean_command(parsed, workspace)
    elif parsed.subcommand == 'version':
        Display.info(f"Jenga Documentation Extractor v{VERSION}")
        Display.info(f"Copyright © {COPYRIGHT_YEAR} {COMPANY_NAME}")
        return 0
    elif parsed.subcommand == 'help':
        parser.print_help()
        return 0
    elif not parsed.subcommand:
        # No subcommand provided, show help
        parser.print_help()
        return 0
    else:
        parser.print_help()
        return 1


def extract_command(args, workspace) -> int:
    """Extract documentation from workspace projects"""
    
    Display.info(f"📚 Extracting documentation from workspace: {workspace.name}")
    
    # Determine which projects to process
    if args.project:
        if args.project not in workspace.projects:
            Display.error(f"Project '{args.project}' not found in workspace")
            Display.info(f"Available projects: {', '.join(workspace.projects.keys())}")
            return 1
        projects_to_process = [args.project]
    else:
        projects_to_process = list(workspace.projects.keys())
        
    if args.exclude_projects:
        projects_to_process = [p for p in projects_to_process if p not in args.exclude_projects]
    
    Display.info(f"📦 Processing {len(projects_to_process)} project(s)")
    
    total_stats = {
        'projects': 0,
        'files': 0,
        'elements': 0,
        'errors': 0,
        'skipped': 0
    }
    
    for project_name in projects_to_process:
        project = workspace.projects[project_name]
        
        # Vérifier si le projet est dans le workspace
        project_dir = Path(project.location)
        if not project_dir.is_absolute():
            project_dir = workspace.location / project_dir
        
        try:
            project_dir.relative_to(workspace.location)
        except ValueError:
            # Le projet est en dehors du workspace
            Display.warning(f"⚠️  Skipping external project: {project_name}")
            Display.detail(f"  Location: {project_dir}")
            total_stats['skipped'] += 1
            continue
        
        project_stats = extract_project_documentation(
            project, args, workspace.location
        )
        
        if project_stats:
            total_stats['projects'] += 1
            total_stats['files'] += project_stats['files']
            total_stats['elements'] += project_stats['elements']
        else:
            total_stats['errors'] += 1
    
    # Print summary
    print_summary(total_stats, args.output)
    
    return 0 if total_stats['errors'] == 0 else 1


def extract_project_documentation(project, args, workspace_dir: Path) -> Optional[Dict]:
    """Extract documentation for a single project"""
    
    Display.info(f"\n📦 Processing project: {project.name}")
    
    # Get project source directories
    source_dirs = get_project_source_dirs(project, workspace_dir)
    if not source_dirs:
        Display.warning(f"  No source directories found for project {project.name}")
        return None
    
    # Afficher les chemins des répertoires sources
    dir_paths = []
    for d in source_dirs:
        try:
            rel_path = d.relative_to(workspace_dir)
            dir_paths.append(str(rel_path))
        except ValueError:
            # Si le répertoire n'est pas dans le workspace, afficher le chemin absolu
            dir_paths.append(str(d))
    
    if dir_paths:
        Display.detail(f"  Source directories: {', '.join(dir_paths)}")
    
    try:
        # Create extractor
        extractor = DocumentationExtractor(
            project_name=project.name,
            source_dirs=source_dirs,
            include_private=args.include_private,
            exclude_dirs=args.exclude_dirs
        )
        
        # Extract documentation
        project_doc = extractor.extract()
        
        # Vérifier s'il y a des éléments documentés
        total_elements = sum(len(items) for items in project_doc.index_by_type.values())
        if total_elements == 0:
            Display.warning(f"  ⚠️ No documentation found for project {project.name}")
            return None
        
        # Generate output
        output_dir = Path(workspace_dir) / args.output / project.name
        
        if args.format in ['markdown', 'all']:
            generator = MarkdownGenerator(project_doc)
            generator.generate(
                output_dir / 'markdown',
                split_by_namespace=not args.no_split_namespace
            )
            Display.success(f"  ✅ Markdown generated: {output_dir / 'markdown'}")
        
        if args.format in ['html', 'all']:
            # HTML generation would go here
            Display.info(f"  HTML generation not implemented yet")
        
        # Return statistics
        return {
            'name': project.name,
            'files': len(project_doc.files),
            'elements': total_elements,
            'types': len(project_doc.index_by_type),
            'namespaces': len(project_doc.index_by_namespace)
        }
        
    except Exception as e:
        Display.error(f"  ❌ Error processing project {project.name}: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return None


def get_project_source_dirs(project, workspace_dir: Path) -> List[Path]:
    """Get source directories for a project"""
    
    source_dirs = []
    
    # Add project directory
    project_dir = Path(project.location)
    if not project_dir.is_absolute():
        project_dir = workspace_dir / project_dir
    
    # Check for src directory
    src_dir = project_dir / 'src'
    if src_dir.exists():
        source_dirs.append(src_dir)
    
    # Check for include directory
    include_dir = project_dir / 'include'
    if include_dir.exists():
        source_dirs.append(include_dir)
    
    # Vérifier si les répertoires sont dans le workspace
    valid_source_dirs = []
    for dir_path in source_dirs:
        if dir_path.exists():
            try:
                # Essayer de calculer le chemin relatif
                rel_path = dir_path.relative_to(workspace_dir)
                valid_source_dirs.append(dir_path)
            except ValueError:
                # Le répertoire n'est pas dans le workspace
                Display.warning(f"  ⚠️ Directory outside workspace: {dir_path}")
                # On l'inclut quand même, mais on ne pourra pas montrer le chemin relatif
                valid_source_dirs.append(dir_path)
        else:
            Display.warning(f"  ⚠️ Directory does not exist: {dir_path}")
    
    # Si aucun répertoire valide trouvé, utiliser le répertoire du projet
    if not valid_source_dirs and project_dir.exists():
        try:
            rel_path = project_dir.relative_to(workspace_dir)
            valid_source_dirs.append(project_dir)
        except ValueError:
            Display.warning(f"  ⚠️ Project directory outside workspace: {project_dir}")
            # On l'inclut quand même si c'est un projet externe
            valid_source_dirs.append(project_dir)
    
    return valid_source_dirs


def print_summary(stats: Dict, output_dir: str):
    """Print extraction summary"""
    
    Display.info(f"\n{'='*60}")
    Display.info("📊 EXTRACTION SUMMARY")
    Display.info(f"{'='*60}")
    
    Display.info(f"✅ Projects processed: {stats['projects']}")
    if stats['errors'] > 0:
        Display.warning(f"⚠️  Errors: {stats['errors']}")
    
    if stats['projects'] > 0:
        Display.info(f"📁 Total files: {stats['files']}")
        Display.info(f"🧩 Total elements: {stats['elements']}")
        
        if stats['elements'] > 0:
            avg_elements = stats['elements'] / stats['projects']
            Display.info(f"📊 Average per project: {avg_elements:.1f} elements")
    
    Display.info(f"\n📂 Documentation generated in: {output_dir}/")
    Display.info(f"   Each project has its own subdirectory")
    
    Display.info(f"\n🚀 Next steps:")
    Display.info(f"   1. Open {output_dir}/[project]/markdown/index.md")
    Display.info(f"   2. View the API documentation")
    Display.info(f"   3. Share with your team")
    
    Display.info(f"\n{'='*60}")


def stats_command(args, workspace) -> int:
    """Show documentation statistics"""
    
    # This would show statistics from already extracted documentation
    # For now, we'll show project statistics
    
    if args.project:
        if args.project not in workspace.projects:
            Display.error(f"Project '{args.project}' not found")
            return 1
        
        projects = {args.project: workspace.projects[args.project]}
    else:
        projects = workspace.projects
    
    stats = {
        'workspace': workspace.name,
        'projects': len(projects),
        'total_projects': len(workspace.projects),
        'project_details': []
    }
    
    for name, project in projects.items():
        project_stats = {
            'name': name,
            'location': str(project.location),
            'kind': str(project.kind),
            'language': project.language,
            'has_documentation': check_documentation_exists(workspace.location, name)
        }
        stats['project_details'].append(project_stats)
    
    if args.json:
        print(json.dumps(stats, indent=2))
    else:
        Display.info(f"📚 Documentation Statistics - {workspace.name}")
        Display.info(f"📦 Total projects: {len(workspace.projects)}")
        Display.info(f"🎯 Showing: {len(projects)} project(s)")
        Display.info("")
        
        for detail in stats['project_details']:
            status = "✅" if detail['has_documentation'] else "⏳"
            Display.info(f"{status} {detail['name']} ({detail['kind']})")
            if detail['has_documentation']:
                Display.detail(f"    Documentation available in docs/{detail['name']}/")
    
    return 0


def check_documentation_exists(workspace_dir: Path, project_name: str) -> bool:
    """Check if documentation exists for a project"""
    docs_dir = Path(workspace_dir) / 'docs' / project_name / 'markdown' / 'index.md'
    return docs_dir.exists()


def list_command(args, workspace) -> int:
    """List projects that can be documented"""
    
    Display.info(f"📚 Projects in workspace: {workspace.name}")
    Display.info("")
    
    for name, project in workspace.projects.items():
        # Check for source files
        source_dirs = get_project_source_dirs(project, workspace.location)
        has_sources = any(d.exists() for d in source_dirs)
        
        if has_sources:
            icon = "📄"
            status = "Has source files"
        else:
            icon = "📁"
            status = "No source files found"
        
        Display.info(f"{icon} {name}")
        Display.detail(f"    Type: {project.kind}, Language: {project.language}")
        Display.detail(f"    Status: {status}")
        
        if source_dirs:
            dirs_str = ", ".join([str(d.relative_to(workspace.location)) for d in source_dirs[:2]])
            if len(source_dirs) > 2:
                dirs_str += f", +{len(source_dirs)-2} more"
            Display.detail(f"    Sources: {dirs_str}")
        
        Display.info("")
    
    Display.info(f"💡 To extract documentation: jenga docs extract [--project NAME]")
    
    return 0


def clean_command(args, workspace) -> int:
    """Clean generated documentation"""
    
    output_dir = Path(workspace.location) / args.output
    
    if args.project:
        # Clean specific project
        project_dir = output_dir / args.project
        if project_dir.exists():
            import shutil
            try:
                shutil.rmtree(project_dir)
                Display.success(f"✅ Cleaned documentation for project: {args.project}")
            except Exception as e:
                Display.error(f"❌ Error cleaning {project_dir}: {e}")
                return 1
        else:
            Display.warning(f"⚠️  No documentation found for project: {args.project}")
    else:
        # Clean all projects
        if output_dir.exists():
            import shutil
            try:
                shutil.rmtree(output_dir)
                Display.success(f"✅ Cleaned all documentation in: {output_dir}")
            except Exception as e:
                Display.error(f"❌ Error cleaning {output_dir}: {e}")
                return 1
        else:
            Display.warning(f"⚠️  No documentation directory found: {output_dir}")
    
    return 0

# ============================================================================
# MAIN (Legacy mode)
# ============================================================================

def main_legacy():
    """Legacy main function for backward compatibility"""
    parser = argparse.ArgumentParser(
        description="Extrait la documentation depuis les sources C/C++",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--project',
        required=True,
        help='Nom du projet'
    )
    
    parser.add_argument(
        '--source',
        action='append',
        required=True,
        help='Répertoires sources à analyser (peut être répété)'
    )
    
    parser.add_argument(
        '--output',
        default='docs',
        help='Répertoire de sortie (défaut: docs/)'
    )
    
    parser.add_argument(
        '--format',
        choices=['markdown', 'html', 'all'],
        default='all',
        help='Format de sortie (défaut: all)'
    )
    
    parser.add_argument(
        '--include-private',
        action='store_true',
        help='Inclure les membres privés/protégés'
    )
    
    args = parser.parse_args()
    
    # Convert args to list for execute function
    execute_args = ['extract']
    execute_args.extend(['--project', args.project])
    
    for source in args.source:
        execute_args.extend(['--source', source])
    
    execute_args.extend(['--output', args.output])
    execute_args.extend(['--format', args.format])
    
    if args.include_private:
        execute_args.append('--include-private')
    
    return execute(execute_args)


if __name__ == "__main__":
    # Use the new Jenga-style execute function
    sys.exit(execute(sys.argv[1:]))