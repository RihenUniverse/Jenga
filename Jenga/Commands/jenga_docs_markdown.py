#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga Documentation Markdown Generator
Génère une documentation Markdown moderne avec liens fonctionnels
"""

from pathlib import Path
from typing import List, Dict
from datetime import datetime

from jenga_docs_extractor import (
    ProjectDocumentation, FileDocumentation, DocComment,
    ElementType, create_element_id, sanitize_filename
)


class MarkdownGenerator:
    """Générateur de documentation Markdown avec design moderne"""
    
    def __init__(self, project_doc: ProjectDocumentation):
        self.project_doc = project_doc
        self.output_dir = Path(".")
        
        # Mapping type -> emoji
        self.type_icons = {
            ElementType.CLASS: "🏛️",
            ElementType.STRUCT: "🏗️",
            ElementType.ENUM: "🔢",
            ElementType.UNION: "🤝",
            ElementType.FUNCTION: "⚙️",
            ElementType.METHOD: "🔧",
            ElementType.VARIABLE: "📦",
            ElementType.MACRO: "🔣",
            ElementType.TYPEDEF: "📝",
            ElementType.NAMESPACE: "🗂️",
        }
    
    def generate(self, output_dir: Path):
        """Génère toute la documentation"""
        self.output_dir = output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📝 Generating Markdown documentation in: {output_dir}")
        
        # Page d'accueil
        self._generate_index()
        
        # Par fichier
        self._generate_by_files()
        
        # Par namespace
        self._generate_by_namespace()
        
        # Par type
        self._generate_by_type()
        
        # Recherche alphabétique
        self._generate_search()
        
        # API complète
        self._generate_api()
        
        # Statistiques
        self._generate_stats()
        
        print(f"✅ Markdown generation complete!")
    
    def _generate_index(self):
        """Page d'accueil"""
        stats = self.project_doc.stats
        
        md = f"""# {self.project_doc.project_name} - Documentation API

> 🚀 Généré le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

![Elements](https://img.shields.io/badge/Elements-{stats.get('total_elements', 0)}-blue)
![Files](https://img.shields.io/badge/Files-{stats.get('total_files', 0)}-green)
![Coverage](https://img.shields.io/badge/Coverage-{stats.get('documentation_coverage', 0):.0f}%25-orange)

## 📊 Statistiques Rapides

| Catégorie | Nombre |
|-----------|--------|
| 📁 Fichiers | {stats.get('total_files', 0)} |
| 🧩 Éléments | {stats.get('total_elements', 0)} |
| 🏛️ Classes | {stats.get('classes', 0)} |
| 🏗️ Structures | {stats.get('structs', 0)} |
| 🔢 Enums | {stats.get('enums', 0)} |
| ⚙️ Fonctions | {stats.get('functions', 0)} |
| 🔧 Méthodes | {stats.get('methods', 0)} |

## 🔍 Navigation

- [📁 Par Fichier](./files/index.md) - Documentation organisée par fichier source
- [🗂️ Par Namespace](./namespaces/index.md) - Navigation par espace de noms
- [🎯 Par Type](./types/index.md) - Éléments groupés par type
- [🔍 Recherche](./search.md) - Index alphabétique complet
- [🔧 API Complète](./api.md) - Vue d'ensemble de l'API
- [📊 Statistiques](./stats.md) - Métriques détaillées

## 📚 À Propos

Cette documentation a été générée automatiquement depuis les commentaires Doxygen du code source.

**Couverture:** {stats.get('well_documented', 0)} éléments sur {stats.get('total_elements', 0)} ont une documentation complète ({stats.get('documentation_coverage', 0):.1f}%)

---

*Documentation générée avec ❤️ par Jenga Build System*
"""
        
        (self.output_dir / "index.md").write_text(md, encoding='utf-8')
        print(f"  ✓ index.md")
    
    def _generate_by_files(self):
        """Documentation par fichier"""
        files_dir = self.output_dir / "files"
        files_dir.mkdir(exist_ok=True)
        
        # Index
        md = f"""# 📁 Documentation par Fichier

> {len(self.project_doc.files)} fichiers documentés

[🏠 Accueil](../index.md)

## Liste des Fichiers

"""
        for file_doc in sorted(self.project_doc.files, key=lambda f: f.file_name):
            md_name = sanitize_filename(file_doc.file_name) + ".md"
            md += f"- 📄 [{file_doc.file_name}](./{md_name}) ({len(file_doc.elements)} éléments)\n"
            
            # Générer la page du fichier
            self._generate_file_page(file_doc, files_dir)
        
        (files_dir / "index.md").write_text(md, encoding='utf-8')
        print(f"  ✓ files/ ({len(self.project_doc.files)} files)")
    
    def _generate_file_page(self, file_doc: FileDocumentation, files_dir: Path):
        """Page individuelle d'un fichier"""
        
        md_name = sanitize_filename(file_doc.file_name) + ".md"
        
        md = f"""# 📄 {file_doc.file_name}

[🏠 Accueil](../index.md) | [📁 Fichiers](./index.md)

## Informations

"""
        
        if file_doc.file_description:
            md += f"**Description:** {file_doc.file_description}\n\n"
        
        if file_doc.file_author:
            md += f"**Auteur:** {file_doc.file_author}\n\n"
        
        md += f"**Chemin:** `{file_doc.relative_path}`\n\n"
        
        # Includes
        if file_doc.includes:
            md += "### 📦 Fichiers Inclus\n\n"
            for inc in file_doc.includes:
                # Créer lien si c'est un fichier du projet
                inc_name = Path(inc).name
                linked = False
                for f in self.project_doc.files:
                    if f.file_name == inc_name:
                        inc_md = sanitize_filename(inc_name) + ".md"
                        md += f"- [`{inc}`](./{inc_md})\n"
                        linked = True
                        break
                
                if not linked:
                    md += f"- `{inc}`\n"
            md += "\n"
        
        # Included by
        if file_doc.included_by:
            md += "### 🔗 Inclus Par\n\n"
            for inc_by in file_doc.included_by:
                inc_name = Path(inc_by).name
                inc_md = sanitize_filename(inc_name) + ".md"
                md += f"- [`{inc_name}`](./{inc_md})\n"
            md += "\n"
        
        # Namespaces
        if file_doc.namespaces:
            md += "### 🗂️ Namespaces\n\n"
            for ns in file_doc.namespaces:
                ns_md = ns.replace('::', '_') + ".md"
                md += f"- [`{ns}`](../namespaces/{ns_md})\n"
            md += "\n"
        
        # Éléments
        md += f"## 🎯 Éléments ({len(file_doc.elements)})\n\n"
        
        # Grouper par type
        by_type = {}
        for elem in file_doc.elements:
            t = elem.signature.element_type
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(elem)
        
        for elem_type in sorted(by_type.keys(), key=lambda t: t.value):
            elements = by_type[elem_type]
            icon = self.type_icons.get(elem_type, "📌")
            
            md += f"### {icon} {elem_type.value.capitalize()}s ({len(elements)})\n\n"
            
            for elem in sorted(elements, key=lambda e: e.signature.name):
                md += self._format_element(elem, file_doc.file_name)
                md += "\n---\n\n"
        
        (files_dir / md_name).write_text(md, encoding='utf-8')
    
    def _format_element(self, elem: DocComment, current_file: str = "") -> str:
        """Formate un élément documenté"""
        
        sig = elem.signature
        icon = self.type_icons.get(sig.element_type, "📌")
        elem_id = create_element_id(elem)
        
        md = f'<a name="{elem_id}"></a>\n\n'
        md += f"#### {icon} `{sig.name}`\n\n"
        
        # Badges
        badges = []
        if sig.is_static:
            badges.append("`static`")
        if sig.is_const:
            badges.append("`const`")
        if sig.is_virtual:
            badges.append("`virtual`")
        if sig.is_constexpr:
            badges.append("`constexpr`")
        if sig.is_noexcept:
            badges.append("`noexcept`")
        if sig.access != "public":
            badges.append(f"`{sig.access}`")
        
        if badges:
            md += " ".join(badges) + "\n\n"
        
        # Signature complète
        md += f"```cpp\n{sig.full_signature}\n```\n\n"
        
        # Brief
        if elem.brief:
            md += f"**{elem.brief}**\n\n"
        
        # Description
        if elem.description:
            md += f"{elem.description}\n\n"
        
        # Template parameters
        if sig.template_params:
            md += "**Paramètres Template:**\n\n"
            for tp in sig.template_params:
                md += f"- `{tp}`\n"
            md += "\n"
        
        # Parameters
        if sig.parameters:
            md += "**Paramètres:**\n\n"
            md += "| Nom | Type | Description |\n"
            md += "|-----|------|-------------|\n"
            for param in sig.parameters:
                desc = elem.param_docs.get(param.name, "")
                direction = f"[{param.direction}] " if param.direction else ""
                md += f"| `{param.name}` | `{param.type}` | {direction}{desc} |\n"
            md += "\n"
        
        # Return
        if elem.returns:
            md += f"**Retour:** {elem.returns}\n\n"
        
        # Examples
        if elem.examples:
            md += "**Exemples:**\n\n"
            for i, ex in enumerate(elem.examples, 1):
                md += f"```cpp\n{ex}\n```\n\n"
        
        # Notes
        for note in elem.notes:
            md += f"> 📝 **Note:** {note}\n\n"
        
        # Warnings
        for warn in elem.warnings:
            md += f"> ⚠️ **Attention:** {warn}\n\n"
        
        # See also avec liens
        if elem.see_also:
            md += "**Voir Aussi:**\n\n"
            for see in elem.see_also:
                # Chercher l'élément
                if see in self.project_doc.by_name:
                    target = self.project_doc.by_name[see]
                    target_file = target.file_path
                    target_id = create_element_id(target)
                    
                    # Créer lien relatif
                    if Path(target_file).name == current_file:
                        md += f"- [`{see}`](#{target_id})\n"
                    else:
                        target_md = sanitize_filename(Path(target_file).name) + ".md"
                        md += f"- [`{see}`](./{target_md}#{target_id})\n"
                else:
                    md += f"- `{see}`\n"
            md += "\n"
        
        # Métadonnées
        meta = []
        if elem.since:
            meta.append(f"Depuis: {elem.since}")
        if elem.complexity:
            meta.append(f"Complexité: {elem.complexity}")
        if elem.thread_safety:
            meta.append(f"Thread-safety: {elem.thread_safety}")
        
        if meta:
            md += "*" + " | ".join(meta) + "*\n\n"
        
        # Deprecated
        if elem.deprecated:
            md += f"> 🚫 **DÉPRÉCIÉ:** {elem.deprecated}\n\n"
        
        # Source
        md += f"*Défini dans: `{elem.file_path}:{elem.line_number}`*\n\n"
        
        return md
    
    def _generate_by_namespace(self):
        """Documentation par namespace"""
        ns_dir = self.output_dir / "namespaces"
        ns_dir.mkdir(exist_ok=True)
        
        md = f"""# 🗂️ Documentation par Namespace

> {len(self.project_doc.by_namespace)} namespaces

[🏠 Accueil](../index.md)

## Liste

"""
        for ns in sorted(self.project_doc.by_namespace.keys()):
            elements = self.project_doc.by_namespace[ns]
            ns_display = "Global" if ns == "__global__" else ns
            ns_md = sanitize_filename(ns) + ".md"
            
            md += f"- 🗂️ [`{ns_display}`](./{ns_md}) ({len(elements)} éléments)\n"
            
            # Générer page du namespace
            self._generate_namespace_page(ns, elements, ns_dir)
        
        (ns_dir / "index.md").write_text(md, encoding='utf-8')
        print(f"  ✓ namespaces/ ({len(self.project_doc.by_namespace)} namespaces)")
    
    def _generate_namespace_page(self, ns: str, elements: List[DocComment], ns_dir: Path):
        """Page d'un namespace"""
        
        ns_display = "Global" if ns == "__global__" else ns
        ns_md = sanitize_filename(ns) + ".md"
        
        md = f"""# 🗂️ Namespace `{ns_display}`

> {len(elements)} éléments

[🏠 Accueil](../index.md) | [🗂️ Namespaces](./index.md)

## Éléments

"""
        
        # Grouper par type
        by_type = {}
        for elem in elements:
            t = elem.signature.element_type
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(elem)
        
        for elem_type in sorted(by_type.keys(), key=lambda t: t.value):
            elems = by_type[elem_type]
            icon = self.type_icons.get(elem_type, "📌")
            
            md += f"### {icon} {elem_type.value.capitalize()}s ({len(elems)})\n\n"
            
            for elem in sorted(elems, key=lambda e: e.signature.name):
                # Brief + lien vers fichier
                file_name = Path(elem.file_path).name
                file_md = sanitize_filename(file_name) + ".md"
                elem_id = create_element_id(elem)
                
                md += f"- **[`{elem.signature.name}`](../files/{file_md}#{elem_id})**"
                if elem.brief:
                    md += f" — {elem.brief}"
                md += "\n"
            
            md += "\n"
        
        (ns_dir / ns_md).write_text(md, encoding='utf-8')
    
    def _generate_by_type(self):
        """Documentation par type"""
        types_dir = self.output_dir / "types"
        types_dir.mkdir(exist_ok=True)
        
        md = """# 🎯 Documentation par Type

[🏠 Accueil](../index.md)

## Types

"""
        
        type_lists = [
            (ElementType.CLASS, self.project_doc.classes),
            (ElementType.STRUCT, self.project_doc.structs),
            (ElementType.ENUM, self.project_doc.enums),
            (ElementType.UNION, self.project_doc.unions),
            (ElementType.FUNCTION, self.project_doc.functions),
            (ElementType.METHOD, self.project_doc.methods),
            (ElementType.VARIABLE, self.project_doc.variables),
            (ElementType.MACRO, self.project_doc.macros),
            (ElementType.TYPEDEF, self.project_doc.typedefs),
        ]
        
        for elem_type, elements in type_lists:
            if not elements:
                continue
            
            icon = self.type_icons.get(elem_type, "📌")
            type_md = elem_type.value + "s.md"
            
            md += f"- {icon} [{elem_type.value.capitalize()}s](./{type_md}) ({len(elements)} éléments)\n"
            
            # Générer page du type
            self._generate_type_page(elem_type, elements, types_dir)
        
        (types_dir / "index.md").write_text(md, encoding='utf-8')
        print(f"  ✓ types/ (9 types)")
    
    def _generate_type_page(self, elem_type: ElementType, elements: List[DocComment], types_dir: Path):
        """Page d'un type"""
        
        icon = self.type_icons.get(elem_type, "📌")
        type_md = elem_type.value + "s.md"
        
        md = f"""# {icon} {elem_type.value.capitalize()}s

> {len(elements)} éléments

[🏠 Accueil](../index.md) | [🎯 Types](./index.md)

## Liste

"""
        
        for elem in sorted(elements, key=lambda e: e.signature.name):
            file_name = Path(elem.file_path).name
            file_md = sanitize_filename(file_name) + ".md"
            elem_id = create_element_id(elem)
            
            md += f"- **[`{elem.signature.name}`](../files/{file_md}#{elem_id})**"
            
            # Namespace
            ns = elem.signature.namespace or "__global__"
            if ns != "__global__":
                md += f" (`{ns}`)"
            
            # Brief
            if elem.brief:
                md += f" — {elem.brief}"
            
            md += "\n"
        
        (types_dir / type_md).write_text(md, encoding='utf-8')
    
    def _generate_search(self):
        """Index alphabétique"""
        
        all_elements = []
        for file_doc in self.project_doc.files:
            all_elements.extend(file_doc.elements)
        
        md = f"""# 🔍 Recherche Alphabétique

> {len(all_elements)} éléments

[🏠 Accueil](./index.md)

## Index

"""
        
        # Grouper par première lettre
        by_letter = {}
        for elem in all_elements:
            letter = elem.signature.name[0].upper()
            if letter not in by_letter:
                by_letter[letter] = []
            by_letter[letter].append(elem)
        
        # Navigation
        for letter in sorted(by_letter.keys()):
            md += f"[{letter}](#{letter.lower()}) "
        md += "\n\n---\n\n"
        
        # Listes
        for letter in sorted(by_letter.keys()):
            md += f'<a name="{letter.lower()}"></a>\n\n'
            md += f"## {letter}\n\n"
            
            for elem in sorted(by_letter[letter], key=lambda e: e.signature.name.lower()):
                file_name = Path(elem.file_path).name
                file_md = sanitize_filename(file_name) + ".md"
                elem_id = create_element_id(elem)
                icon = self.type_icons.get(elem.signature.element_type, "📌")
                
                md += f"- {icon} **[`{elem.signature.name}`](./files/{file_md}#{elem_id})**"
                
                if elem.brief:
                    md += f" — {elem.brief}"
                
                md += "\n"
            
            md += "\n"
        
        (self.output_dir / "search.md").write_text(md, encoding='utf-8')
        print(f"  ✓ search.md")
    
    def _generate_api(self):
        """API complète"""
        md = f"""# 🔧 API Complète

[🏠 Accueil](./index.md)

## Vue d'Ensemble

Documentation complète de l'API du projet {self.project_doc.project_name}.

"""
        
        # Lien vers chaque type
        md += "## Par Type\n\n"
        
        type_lists = [
            (ElementType.CLASS, self.project_doc.classes),
            (ElementType.STRUCT, self.project_doc.structs),
            (ElementType.ENUM, self.project_doc.enums),
            (ElementType.FUNCTION, self.project_doc.functions),
            (ElementType.METHOD, self.project_doc.methods),
        ]
        
        for elem_type, elements in type_lists:
            if not elements:
                continue
            
            icon = self.type_icons.get(elem_type, "📌")
            type_md = elem_type.value + "s.md"
            
            md += f"- {icon} [{elem_type.value.capitalize()}s](./types/{type_md}) ({len(elements)})\n"
        
        (self.output_dir / "api.md").write_text(md, encoding='utf-8')
        print(f"  ✓ api.md")
    
    def _generate_stats(self):
        """Statistiques détaillées"""
        stats = self.project_doc.stats
        
        md = f"""# 📊 Statistiques Détaillées

[🏠 Accueil](./index.md)

## Vue d'Ensemble

| Métrique | Valeur |
|----------|--------|
| Fichiers | {stats.get('total_files', 0)} |
| Éléments | {stats.get('total_elements', 0)} |
| Namespaces | {stats.get('namespaces', 0)} |
| Couverture | {stats.get('documentation_coverage', 0):.1f}% |

## Par Type

| Type | Nombre |
|------|--------|
| 🏛️ Classes | {stats.get('classes', 0)} |
| 🏗️ Structures | {stats.get('structs', 0)} |
| 🔢 Enums | {stats.get('enums', 0)} |
| 🤝 Unions | {stats.get('unions', 0)} |
| ⚙️ Fonctions | {stats.get('functions', 0)} |
| 🔧 Méthodes | {stats.get('methods', 0)} |
| 📦 Variables | {stats.get('variables', 0)} |
| 🔣 Macros | {stats.get('macros', 0)} |
| 📝 Typedefs | {stats.get('typedefs', 0)} |

## Qualité

- **Éléments bien documentés:** {stats.get('well_documented', 0)} / {stats.get('total_elements', 0)}
- **Couverture:** {stats.get('documentation_coverage', 0):.1f}%
- **Paramètres moyens par fonction:** {stats.get('avg_params_per_function', 0):.1f}

"""
        
        (self.output_dir / "stats.md").write_text(md, encoding='utf-8')
        print(f"  ✓ stats.md")
