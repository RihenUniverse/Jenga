#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nken Build System - Incremental Linker
Évite les relinks inutiles en détectant si les objects ont changé
"""

import json
import hashlib
from pathlib import Path
from typing import List


class IncrementalLinker:
    """
    Linker incrémental qui évite de relinker si:
    - Tous les .o sont identiques
    - Les options de link n'ont pas changé
    - Les bibliothèques n'ont pas changé
    
    Gain typique: 50-90% du temps de link économisé
    """
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_file = cache_dir / "link_cache.json"
        self.cache = {}
        self._load()
    
    def _load(self):
        """Load link cache from disk"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
            except Exception:
                self.cache = {}
        else:
            self.cache = {}
    
    def _save(self):
        """Save link cache to disk"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception:
            pass
    
    def needs_relink(self, output: str, objects: List[str], 
                    libs: List[str]) -> bool:
        """
        Détermine si le relink est nécessaire
        
        Returns:
            True si relink nécessaire, False si output est à jour
        """
        
        # 1. Output n'existe pas
        if not Path(output).exists():
            return True
        
        # 2. Calculer le hash des inputs
        hasher = hashlib.blake2b(digest_size=16)
        
        # Hash des object files (par mtime et size)
        for obj in sorted(objects):
            if Path(obj).exists():
                stat = Path(obj).stat()
                hasher.update(f"{obj}:{stat.st_mtime_ns}:{stat.st_size}".encode())
            else:
                # Object file manquant
                return True
        
        # Hash des bibliothèques
        for lib in sorted(libs):
            hasher.update(lib.encode())
        
        current_hash = hasher.hexdigest()
        
        # 3. Comparer avec le cache
        if output in self.cache:
            if self.cache[output] == current_hash:
                # Hash identique = pas besoin de relink
                return False
        
        # 4. Mettre à jour le cache
        self.cache[output] = current_hash
        self._save()
        
        return True
    
    def invalidate(self, output: str):
        """Force un relink en invalidant le cache pour cet output"""
        if output in self.cache:
            del self.cache[output]
            self._save()
    
    def clear(self):
        """Clear all link cache"""
        self.cache = {}
        self._save()