#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga Documentation Parser - Version améliorée
Parse C/C++ avec détection précise des éléments et leurs signatures
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


# ============================================================================
# TYPES ET STRUCTURES
# ============================================================================

class ElementType(Enum):
    """Types d'éléments C++ reconnus"""
    CLASS = "class"
    STRUCT = "struct"
    ENUM = "enum"
    UNION = "union"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    MACRO = "macro"
    TYPEDEF = "typedef"
    NAMESPACE = "namespace"
    TEMPLATE = "template"
    
    def __lt__(self, other):
        return self.value < other.value


@dataclass
class Parameter:
    """Paramètre de fonction"""
    name: str
    type: str
    description: str = ""
    direction: str = ""  # in, out, in/out
    default_value: str = ""


@dataclass
class ElementSignature:
    """Signature complète d'un élément C++"""
    element_type: ElementType
    name: str
    full_signature: str  # Signature complète comme dans le code
    return_type: str = ""
    parameters: List[Parameter] = field(default_factory=list)
    template_params: List[str] = field(default_factory=list)
    namespace: str = ""
    parent_class: str = ""  # Pour les méthodes
    
    # Modifiers
    is_const: bool = False
    is_static: bool = False
    is_virtual: bool = False
    is_override: bool = False
    is_final: bool = False
    is_inline: bool = False
    is_explicit: bool = False
    is_constexpr: bool = False
    is_noexcept: bool = False
    is_pure_virtual: bool = False
    
    access: str = "public"  # public, private, protected


@dataclass
class DocComment:
    """Commentaire de documentation Doxygen"""
    signature: ElementSignature
    brief: str = ""
    description: str = ""
    param_docs: Dict[str, str] = field(default_factory=dict)
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
    complexity: str = ""
    thread_safety: str = ""
    
    # Métadonnées de localisation
    file_path: str = ""
    line_number: int = 0


# ============================================================================
# PARSER C++ AVANCÉ
# ============================================================================

class CppSignatureParser:
    """Parse les signatures C++ avec précision"""
    
    def __init__(self):
        # Patterns de détection
        self.patterns = {
            'namespace': re.compile(
                r'namespace\s+([a-zA-Z_]\w*)\s*\{',
                re.MULTILINE
            ),
            'class': re.compile(
                r'(?:template\s*<[^>]*>\s*)?'
                r'(?:(class|struct)\s+(?:[A-Z_]+\s+)?([a-zA-Z_]\w*))'
                r'(?:\s*:\s*(?:public|private|protected)\s+[^{]+)?'
                r'\s*\{',
                re.MULTILINE
            ),
            'enum': re.compile(
                r'enum\s+(?:class\s+)?([a-zA-Z_]\w*)\s*(?::\s*\w+)?\s*\{',
                re.MULTILINE
            ),
            'union': re.compile(
                r'union\s+([a-zA-Z_]\w*)\s*\{',
                re.MULTILINE
            ),
            'function': re.compile(
                r'(?:template\s*<[^>]*>\s*)?'
                r'(?:(inline|static|virtual|explicit|constexpr)\s+)*'
                r'([a-zA-Z_]\w*(?:<[^>]*>)?(?:\s*[*&])?)\s+'  # return type
                r'([a-zA-Z_]\w*)\s*'  # function name
                r'\(([^)]*)\)'  # parameters
                r'(?:\s*(const|noexcept|override|final))*'
                r'(?:\s*=\s*0)?'  # pure virtual
                r'\s*[;{]',
                re.MULTILINE
            ),
            'variable': re.compile(
                r'(?:(static|const|constexpr|inline)\s+)*'
                r'([a-zA-Z_]\w*(?:<[^>]*>)?(?:\s*[*&])?)\s+'
                r'([a-zA-Z_]\w*)\s*'
                r'(?:=\s*[^;]+)?\s*;',
                re.MULTILINE
            ),
            'macro': re.compile(
                r'#define\s+([A-Z_]\w*)'
                r'(?:\([^)]*\))?'
                r'(?:\s+(.+))?',
                re.MULTILINE
            ),
            'typedef': re.compile(
                r'(?:typedef\s+(.+?)\s+([a-zA-Z_]\w*))|'
                r'(?:using\s+([a-zA-Z_]\w*)\s*=\s*(.+?))',
                re.MULTILINE
            ),
        }
    
    def parse_signature(self, code: str, element_type: str) -> Optional[ElementSignature]:
        """Parse une signature C++ selon son type"""
        
        if element_type == 'class' or element_type == 'struct':
            return self._parse_class_signature(code, element_type)
        elif element_type == 'enum':
            return self._parse_enum_signature(code)
        elif element_type == 'union':
            return self._parse_union_signature(code)
        elif element_type == 'function':
            return self._parse_function_signature(code)
        elif element_type == 'variable':
            return self._parse_variable_signature(code)
        elif element_type == 'macro':
            return self._parse_macro_signature(code)
        elif element_type == 'typedef':
            return self._parse_typedef_signature(code)
        
        return None
    
    def _parse_class_signature(self, code: str, kind: str) -> Optional[ElementSignature]:
        """Parse signature de class/struct"""
        match = self.patterns['class'].search(code)
        if not match:
            return None
        
        class_type = match.group(1)  # class ou struct
        name = match.group(2)
        
        # Détecter template
        template_params = []
        template_match = re.search(r'template\s*<([^>]+)>', code)
        if template_match:
            template_params = [p.strip() for p in template_match.group(1).split(',')]
        
        # Extraire héritage
        inheritance = ""
        inherit_match = re.search(r':\s*((?:(?:public|private|protected)\s+\w+(?:,\s*)?)+)', code)
        if inherit_match:
            inheritance = inherit_match.group(1)
        
        # Construire signature complète
        sig = f"template<{', '.join(template_params)}> " if template_params else ""
        sig += f"{class_type} {name}"
        if inheritance:
            sig += f" : {inheritance}"
        
        return ElementSignature(
            element_type=ElementType.CLASS if class_type == 'class' else ElementType.STRUCT,
            name=name,
            full_signature=sig,
            template_params=template_params
        )
    
    def _parse_enum_signature(self, code: str) -> Optional[ElementSignature]:
        """Parse signature d'enum"""
        match = self.patterns['enum'].search(code)
        if not match:
            return None
        
        name = match.group(1)
        
        # Détecter enum class
        is_scoped = 'enum class' in code
        
        # Détecter underlying type
        underlying_type = ""
        type_match = re.search(r'enum\s+(?:class\s+)?\w+\s*:\s*(\w+)', code)
        if type_match:
            underlying_type = type_match.group(1)
        
        sig = f"enum {'class ' if is_scoped else ''}{name}"
        if underlying_type:
            sig += f" : {underlying_type}"
        
        return ElementSignature(
            element_type=ElementType.ENUM,
            name=name,
            full_signature=sig
        )
    
    def _parse_union_signature(self, code: str) -> Optional[ElementSignature]:
        """Parse signature d'union"""
        match = self.patterns['union'].search(code)
        if not match:
            return None
        
        name = match.group(1)
        
        return ElementSignature(
            element_type=ElementType.UNION,
            name=name,
            full_signature=f"union {name}"
        )
    
    def _parse_function_signature(self, code: str) -> Optional[ElementSignature]:
        """Parse signature de fonction/méthode"""
        match = self.patterns['function'].search(code)
        if not match:
            return None
        
        modifiers_str = match.group(1) or ""
        return_type = match.group(2)
        func_name = match.group(3)
        params_str = match.group(4) or ""
        trailing_str = match.group(5) or ""
        
        # Parser les paramètres
        parameters = self._parse_parameters(params_str)
        
        # Détecter les modifiers
        is_static = 'static' in modifiers_str
        is_virtual = 'virtual' in modifiers_str
        is_inline = 'inline' in modifiers_str
        is_explicit = 'explicit' in modifiers_str
        is_constexpr = 'constexpr' in modifiers_str
        is_const = 'const' in trailing_str
        is_noexcept = 'noexcept' in trailing_str
        is_override = 'override' in trailing_str
        is_final = 'final' in trailing_str
        is_pure_virtual = '= 0' in code
        
        # Détecter template
        template_params = []
        template_match = re.search(r'template\s*<([^>]+)>', code)
        if template_match:
            template_params = [p.strip() for p in template_match.group(1).split(',')]
        
        # Construire signature complète
        sig = ""
        if template_params:
            sig += f"template<{', '.join(template_params)}> "
        
        if is_static:
            sig += "static "
        if is_virtual:
            sig += "virtual "
        if is_inline:
            sig += "inline "
        if is_explicit:
            sig += "explicit "
        if is_constexpr:
            sig += "constexpr "
        
        sig += f"{return_type} {func_name}("
        sig += ", ".join([f"{p.type} {p.name}" for p in parameters])
        sig += ")"
        
        if is_const:
            sig += " const"
        if is_noexcept:
            sig += " noexcept"
        if is_override:
            sig += " override"
        if is_final:
            sig += " final"
        if is_pure_virtual:
            sig += " = 0"
        
        # Déterminer si c'est une fonction ou méthode
        # (nécessite contexte de la classe parente - sera déterminé plus tard)
        element_type = ElementType.FUNCTION
        
        return ElementSignature(
            element_type=element_type,
            name=func_name,
            full_signature=sig,
            return_type=return_type,
            parameters=parameters,
            template_params=template_params,
            is_static=is_static,
            is_virtual=is_virtual,
            is_inline=is_inline,
            is_explicit=is_explicit,
            is_constexpr=is_constexpr,
            is_const=is_const,
            is_noexcept=is_noexcept,
            is_override=is_override,
            is_final=is_final,
            is_pure_virtual=is_pure_virtual
        )
    
    def _parse_parameters(self, params_str: str) -> List[Parameter]:
        """Parse la liste de paramètres d'une fonction"""
        if not params_str.strip():
            return []
        
        parameters = []
        
        # Diviser par virgules (en respectant les templates)
        param_parts = self._smart_split(params_str, ',')
        
        for part in param_parts:
            part = part.strip()
            if not part or part == 'void':
                continue
            
            # Parser type et nom
            # Format: [const] type [*&] name [= default]
            
            # Extraire valeur par défaut
            default_value = ""
            if '=' in part:
                part, default_value = part.split('=', 1)
                part = part.strip()
                default_value = default_value.strip()
            
            # Extraire nom (dernier mot)
            tokens = part.split()
            if len(tokens) >= 2:
                param_name = tokens[-1]
                # Enlever * et & du nom si présents
                param_name = param_name.lstrip('*&')
                
                param_type = ' '.join(tokens[:-1])
            else:
                # Pas de nom (déclaration forward)
                param_name = ""
                param_type = part
            
            parameters.append(Parameter(
                name=param_name,
                type=param_type,
                default_value=default_value
            ))
        
        return parameters
    
    def _smart_split(self, text: str, delimiter: str) -> List[str]:
        """Split intelligent qui respecte les <> et ()"""
        parts = []
        current = []
        depth_angle = 0
        depth_paren = 0
        
        for char in text:
            if char == '<':
                depth_angle += 1
            elif char == '>':
                depth_angle -= 1
            elif char == '(':
                depth_paren += 1
            elif char == ')':
                depth_paren -= 1
            elif char == delimiter and depth_angle == 0 and depth_paren == 0:
                parts.append(''.join(current))
                current = []
                continue
            
            current.append(char)
        
        if current:
            parts.append(''.join(current))
        
        return parts
    
    def _parse_variable_signature(self, code: str) -> Optional[ElementSignature]:
        """Parse signature de variable"""
        match = self.patterns['variable'].search(code)
        if not match:
            return None
        
        modifiers = match.group(1) or ""
        var_type = match.group(2)
        var_name = match.group(3)
        
        is_static = 'static' in modifiers
        is_const = 'const' in modifiers
        is_constexpr = 'constexpr' in modifiers
        is_inline = 'inline' in modifiers
        
        sig = ""
        if is_static:
            sig += "static "
        if is_const:
            sig += "const "
        if is_constexpr:
            sig += "constexpr "
        if is_inline:
            sig += "inline "
        
        sig += f"{var_type} {var_name}"
        
        return ElementSignature(
            element_type=ElementType.VARIABLE,
            name=var_name,
            full_signature=sig,
            return_type=var_type,
            is_static=is_static,
            is_const=is_const,
            is_constexpr=is_constexpr,
            is_inline=is_inline
        )
    
    def _parse_macro_signature(self, code: str) -> Optional[ElementSignature]:
        """Parse signature de macro"""
        match = self.patterns['macro'].search(code)
        if not match:
            return None
        
        macro_name = match.group(1)
        macro_value = match.group(2) or ""
        
        sig = f"#define {macro_name}"
        if macro_value:
            sig += f" {macro_value}"
        
        return ElementSignature(
            element_type=ElementType.MACRO,
            name=macro_name,
            full_signature=sig
        )
    
    def _parse_typedef_signature(self, code: str) -> Optional[ElementSignature]:
        """Parse signature de typedef/using"""
        match = self.patterns['typedef'].search(code)
        if not match:
            return None
        
        if match.group(1):  # typedef
            original_type = match.group(1)
            alias_name = match.group(2)
            sig = f"typedef {original_type} {alias_name}"
        else:  # using
            alias_name = match.group(3)
            original_type = match.group(4)
            sig = f"using {alias_name} = {original_type}"
        
        return ElementSignature(
            element_type=ElementType.TYPEDEF,
            name=alias_name,
            full_signature=sig,
            return_type=original_type
        )


# ============================================================================
# PARSER DOXYGEN
# ============================================================================

class DoxygenParser:
    """Parse les commentaires Doxygen"""
    
    def __init__(self):
        self.tag_patterns = {
            'brief': re.compile(r'@brief\s+(.+?)(?=@|\n\n|\*/|\Z)', re.DOTALL),
            'class': re.compile(r'@class\s+(\w+)', re.MULTILINE),
            'struct': re.compile(r'@struct\s+(\w+)', re.MULTILINE),
            'enum': re.compile(r'@enum\s+(\w+)', re.MULTILINE),
            'union': re.compile(r'@union\s+(\w+)', re.MULTILINE),
            'function': re.compile(r'@(?:function|fn)\s+(\w+)', re.MULTILINE),
            'var': re.compile(r'@var\s+(.+)', re.MULTILINE),
            'macro': re.compile(r'@(?:macro|def)\s+(\w+)', re.MULTILINE),
            'param': re.compile(r'@param(?:\[([^\]]+)\])?\s+(\w+)\s+(.+?)(?=@|\n\n|\*/|\Z)', re.DOTALL),
            'tparam': re.compile(r'@tparam\s+(\w+)\s+(.+?)(?=@|\n|\*/|\Z)', re.DOTALL),
            'return': re.compile(r'@return\s+(.+?)(?=@|\n\n|\*/|\Z)', re.DOTALL),
            'retval': re.compile(r'@retval\s+(\w+)\s+(.+?)(?=@|\n|\*/|\Z)', re.DOTALL),
            'throw': re.compile(r'@throws?\s+(.+?)(?=@|\n|\*/|\Z)', re.DOTALL),
            'example': re.compile(r'@example\s+(.+?)(?=@|\n\n|\*/|\Z)', re.DOTALL),
            'code': re.compile(r'@code\s*(.*?)@endcode', re.DOTALL | re.IGNORECASE),
            'note': re.compile(r'@note\s+(.+?)(?=@|\n\n|\*/|\Z)', re.DOTALL),
            'warning': re.compile(r'@warning\s+(.+?)(?=@|\n\n|\*/|\Z)', re.DOTALL),
            'see': re.compile(r'@(?:see|sa)\s+(.+?)(?=@|\n|\*/|\Z)', re.DOTALL),
            'since': re.compile(r'@since\s+(.+?)(?=@|\n|\*/|\Z)', re.DOTALL),
            'deprecated': re.compile(r'@deprecated\s+(.+?)(?=@|\n\n|\*/|\Z)', re.DOTALL),
            'author': re.compile(r'@author\s+(.+?)(?=@|\n|\*/|\Z)', re.DOTALL),
            'date': re.compile(r'@date\s+(.+?)(?=@|\n|\*/|\Z)', re.DOTALL),
            'complexity': re.compile(r'@complexity\s+(.+?)(?=@|\n|\*/|\Z)', re.DOTALL),
            'threadsafe': re.compile(r'@threadsafe', re.IGNORECASE),
            'notthreadsafe': re.compile(r'@notthreadsafe', re.IGNORECASE),
        }
    
    def parse(self, comment_text: str, signature: ElementSignature) -> DocComment:
        """Parse un commentaire Doxygen"""
        
        doc = DocComment(signature=signature)
        
        # @brief
        match = self.tag_patterns['brief'].search(comment_text)
        if match:
            doc.brief = self._clean_text(match.group(1))
        
        # Si pas de @brief, utiliser première ligne
        if not doc.brief:
            lines = comment_text.split('\n')
            for line in lines:
                clean = self._clean_text(line)
                if clean and not clean.startswith('@'):
                    doc.brief = clean
                    break
        
        # @param
        for match in re.finditer(self.tag_patterns['param'], comment_text):
            direction = match.group(1) or "in"
            param_name = match.group(2)
            param_desc = self._clean_text(match.group(3))
            doc.param_docs[param_name] = param_desc
            
            # Mettre à jour le paramètre dans la signature si trouvé
            for param in signature.parameters:
                if param.name == param_name:
                    param.description = param_desc
                    param.direction = direction
        
        # @return
        match = self.tag_patterns['return'].search(comment_text)
        if match:
            doc.returns = self._clean_text(match.group(1))
        
        # @retval
        for match in re.finditer(self.tag_patterns['retval'], comment_text):
            value = match.group(1)
            desc = self._clean_text(match.group(2))
            doc.return_values[value] = desc
        
        # @throw/@throws
        for match in re.finditer(self.tag_patterns['throw'], comment_text):
            doc.throws.append(self._clean_text(match.group(1)))
        
        # @code...@endcode
        for match in re.finditer(self.tag_patterns['code'], comment_text):
            doc.examples.append(match.group(1).strip())
        
        # @note
        for match in re.finditer(self.tag_patterns['note'], comment_text):
            doc.notes.append(self._clean_text(match.group(1)))
        
        # @warning
        for match in re.finditer(self.tag_patterns['warning'], comment_text):
            doc.warnings.append(self._clean_text(match.group(1)))
        
        # @see
        for match in re.finditer(self.tag_patterns['see'], comment_text):
            doc.see_also.append(self._clean_text(match.group(1)))
        
        # Métadonnées
        for tag in ['since', 'deprecated', 'author', 'date', 'complexity']:
            match = self.tag_patterns[tag].search(comment_text)
            if match:
                setattr(doc, tag, self._clean_text(match.group(1)))
        
        # Thread safety
        if self.tag_patterns['threadsafe'].search(comment_text):
            doc.thread_safety = "Thread-safe"
        elif self.tag_patterns['notthreadsafe'].search(comment_text):
            doc.thread_safety = "Not thread-safe"
        
        # Description (tout sauf les tags)
        desc_lines = []
        in_tag = False
        for line in comment_text.split('\n'):
            clean = self._clean_text(line)
            if clean.startswith('@'):
                in_tag = True
                continue
            if not in_tag and clean and clean != doc.brief:
                desc_lines.append(clean)
        
        if desc_lines:
            doc.description = ' '.join(desc_lines)
        
        return doc
    
    def _clean_text(self, text: str) -> str:
        """Nettoie le texte extrait"""
        # Enlever * au début
        text = re.sub(r'^\s*\*+\s*', '', text, flags=re.MULTILINE)
        # Enlever / au début
        text = re.sub(r'^\s*/+\s*', '', text, flags=re.MULTILINE)
        # Espaces multiples
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
