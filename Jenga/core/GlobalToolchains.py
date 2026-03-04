#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Global toolchains registry helpers.

Registry location (global to Jenga installation):
  <JENGA_ROOT>/.jenga/toolchains_registry.json
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

from Jenga.Core.Api import Toolchain, CompilerFamily, TargetOS, TargetArch, TargetEnv


def GetJengaRoot() -> Path:
    # .../Jenga/Core/GlobalToolchains.py -> repo root
    return Path(__file__).resolve().parents[2]


def GetGlobalRegistryPath() -> Path:
    return GetJengaRoot() / ".jenga" / "toolchains_registry.json"


def _EnumByValue(enum_cls, value: Optional[str]):
    if not value:
        return None
    for e in enum_cls:
        if e.value.lower() == str(value).lower():
            return e
    try:
        return enum_cls[str(value).upper().replace("-", "_")]
    except Exception:
        return None


def _ExecutableExists(path_or_cmd: Optional[str]) -> bool:
    value = str(path_or_cmd or "").strip()
    if not value:
        return False
    expanded = os.path.expandvars(os.path.expanduser(value))
    candidate = Path(expanded)
    has_sep = (os.sep and os.sep in expanded) or (os.altsep and os.altsep in expanded)
    if has_sep or candidate.is_absolute() or expanded.startswith("."):
        return candidate.exists()
    return shutil.which(expanded) is not None


def LoadGlobalRegistry(path: Optional[Path] = None) -> Dict[str, Any]:
    registry_path = path or GetGlobalRegistryPath()
    if not registry_path.exists():
        return {"toolchains": [], "sdk": {}}
    try:
        return json.loads(registry_path.read_text(encoding="utf-8"))
    except Exception:
        return {"toolchains": [], "sdk": {}}


def BuildToolchainFromRegistryEntry(entry: Dict[str, Any]) -> Optional[Toolchain]:
    name = entry.get("name")
    family_raw = entry.get("compilerFamily", "clang")
    family = _EnumByValue(CompilerFamily, family_raw)
    if not name or family is None:
        return None

    tc = Toolchain(name=name, compilerFamily=family)
    tc.targetOs = _EnumByValue(TargetOS, entry.get("targetOs"))
    tc.targetArch = _EnumByValue(TargetArch, entry.get("targetArch"))
    tc.targetEnv = _EnumByValue(TargetEnv, entry.get("targetEnv"))

    tc.targetTriple = entry.get("targetTriple") or None
    tc.sysroot = entry.get("sysroot") or None
    tc.ccPath = entry.get("ccPath") or None
    tc.cxxPath = entry.get("cxxPath") or None
    tc.arPath = entry.get("arPath") or None
    tc.ldPath = entry.get("ldPath") or None
    tc.stripPath = entry.get("stripPath") or None
    tc.ranlibPath = entry.get("ranlibPath") or None
    tc.asmPath = entry.get("asmPath") or None
    tc.toolchainDir = entry.get("toolchainDir") or None

    # Skip stale toolchains pointing to non-existent compilers (common when
    # copying registry files across machines).
    if tc.ccPath and not _ExecutableExists(tc.ccPath):
        return None
    if tc.cxxPath and not _ExecutableExists(tc.cxxPath):
        return None
    if not tc.ccPath and not tc.cxxPath:
        return None
    if not tc.ccPath:
        tc.ccPath = tc.cxxPath
    if not tc.cxxPath:
        tc.cxxPath = tc.ccPath
    if tc.ldPath and not _ExecutableExists(tc.ldPath):
        tc.ldPath = None
    if tc.arPath and not _ExecutableExists(tc.arPath):
        tc.arPath = None

    tc.cflags = list(entry.get("cflags", []) or [])
    tc.cxxflags = list(entry.get("cxxflags", []) or [])
    tc.ldflags = list(entry.get("ldflags", []) or [])
    tc.arflags = list(entry.get("arflags", []) or [])

    return tc


def ApplyGlobalRegistryToWorkspace(workspace: Any, registry: Optional[Dict[str, Any]] = None) -> None:
    if workspace is None:
        return

    data = registry or LoadGlobalRegistry()
    for entry in data.get("toolchains", []) or []:
        tc = BuildToolchainFromRegistryEntry(entry)
        if tc is None:
            continue
        if tc.name not in workspace.toolchains:
            workspace.toolchains[tc.name] = tc

    sdk = data.get("sdk", {}) or {}
    if sdk.get("androidSdkPath") and not getattr(workspace, "androidSdkPath", ""):
        workspace.androidSdkPath = sdk["androidSdkPath"]
    if sdk.get("androidNdkPath") and not getattr(workspace, "androidNdkPath", ""):
        workspace.androidNdkPath = sdk["androidNdkPath"]

    # Do not override workspace default toolchain from global registry.
    # Selection should happen per build target via ToolchainManager resolver.
