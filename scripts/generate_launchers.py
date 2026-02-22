#!/usr/bin/env python3
"""
Generate launcher scripts for built Jenga examples.

Outputs inside each built project directory:
  - Windows native: run.bat
  - Linux/macOS native: run.sh
  - Web (Emscripten): run_web.bat + run_web.sh

Web launchers always run a local HTTP server to avoid file:// CORS/WASM errors.
"""

from __future__ import annotations

import argparse
import stat
from pathlib import Path
from typing import Iterable, Optional, Tuple


def write_if_changed(path: Path, content: str, make_executable: bool = False) -> bool:
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old == content:
        if make_executable and path.exists():
            mode = path.stat().st_mode
            path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        return False
    path.write_text(content, encoding="utf-8", newline="\n")
    if make_executable:
        mode = path.stat().st_mode
        path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return True


def iter_project_dirs(build_bin_dir: Path) -> Iterable[Tuple[str, Path]]:
    for cfg_dir in sorted(build_bin_dir.iterdir()):
        if not cfg_dir.is_dir():
            continue
        for project_dir in sorted(cfg_dir.iterdir()):
            if project_dir.is_dir():
                yield cfg_dir.name, project_dir


def find_web_html(project_dir: Path, project_name: str) -> Optional[Path]:
    preferred = project_dir / f"{project_name}.html"
    if preferred.is_file():
        return preferred
    htmls = sorted(project_dir.glob("*.html"))
    return htmls[0] if htmls else None


def windows_native_launcher(project_name: str) -> str:
    exe = f"{project_name}.exe"
    return (
        "@echo off\n"
        "setlocal\n"
        "set \"DIR=%~dp0\"\n"
        "pushd \"%DIR%\"\n"
        f"if not exist \"{exe}\" (\n"
        f"  echo [run] Missing executable: {exe}\n"
        "  exit /b 1\n"
        ")\n"
        f"\"{exe}\" %*\n"
        "set \"EXIT_CODE=%ERRORLEVEL%\"\n"
        "popd\n"
        "exit /b %EXIT_CODE%\n"
    )


def posix_native_launcher(project_name: str) -> str:
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "DIR=\"$(cd \"$(dirname \"${BASH_SOURCE[0]}\")\" && pwd)\"\n"
        "cd \"$DIR\"\n"
        f"if [[ ! -f \"./{project_name}\" ]]; then\n"
        f"  echo \"[run] Missing executable: ./{project_name}\" >&2\n"
        "  exit 1\n"
        "fi\n"
        f"exec \"./{project_name}\" \"$@\"\n"
    )


def windows_web_launcher(html_name: str) -> str:
    return (
        "@echo off\n"
        "setlocal EnableDelayedExpansion\n"
        "set \"PORT=%~1\"\n"
        "if \"%PORT%\"==\"\" set \"PORT=8080\"\n"
        "set \"DIR=%~dp0\"\n"
        "if \"%DIR:~-1%\"==\"\\\" set \"DIR=%DIR:~0,-1%\"\n"
        f"if not exist \"%DIR%\\{html_name}\" (\n"
        f"  echo [run_web] Missing HTML: %DIR%\\{html_name}\n"
        "  exit /b 1\n"
        ")\n"
        ":find_port\n"
        "netstat -ano -p tcp | findstr /R /C:\":%PORT% .*LISTENING\" >nul\n"
        "if %ERRORLEVEL% EQU 0 (\n"
        "  echo [run_web] Port %PORT% is already in use, trying next...\n"
        "  set /a PORT+=1\n"
        "  goto find_port\n"
        ")\n"
        f"set \"URL=http://127.0.0.1:%PORT%/{html_name}\"\n"
        "echo [run_web] Serving \"%DIR%\" at %URL%\n"
        "echo [run_web] Tip: browser extension errors like content.js are unrelated to app runtime.\n"
        "start \"\" powershell -NoProfile -Command \"Start-Sleep -Milliseconds 700; Start-Process '%URL%'\"\n"
        "pushd \"%DIR%\"\n"
        "where py >nul 2>nul\n"
        "if %ERRORLEVEL% EQU 0 (\n"
        "  py -3 -m http.server %PORT% --bind 127.0.0.1\n"
        ") else (\n"
        "  where python3 >nul 2>nul\n"
        "  if %ERRORLEVEL% EQU 0 (\n"
        "    python3 -m http.server %PORT% --bind 127.0.0.1\n"
        "  ) else (\n"
        "    python -m http.server %PORT% --bind 127.0.0.1\n"
        "  )\n"
        ")\n"
        "set \"EXIT_CODE=%ERRORLEVEL%\"\n"
        "popd\n"
        "exit /b %EXIT_CODE%\n"
    )


def posix_web_launcher(html_name: str) -> str:
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "PORT=\"${1:-8080}\"\n"
        "DIR=\"$(cd \"$(dirname \"${BASH_SOURCE[0]}\")\" && pwd)\"\n"
        "cd \"$DIR\"\n"
        f"URL=\"http://127.0.0.1:${{PORT}}/{html_name}\"\n"
        "echo \"[run_web] Serving '$DIR' at ${URL}\"\n"
        "if command -v xdg-open >/dev/null 2>&1; then\n"
        "  xdg-open \"${URL}\" >/dev/null 2>&1 || true\n"
        "elif command -v open >/dev/null 2>&1; then\n"
        "  open \"${URL}\" >/dev/null 2>&1 || true\n"
        "fi\n"
        "if command -v python3 >/dev/null 2>&1; then\n"
        "  exec python3 -m http.server \"${PORT}\" --bind 127.0.0.1 --directory \"$DIR\"\n"
        "else\n"
        "  exec python -m http.server \"${PORT}\" --bind 127.0.0.1 --directory \"$DIR\"\n"
        "fi\n"
    )


def generate(example_dir: Path, verbose: bool = False) -> int:
    build_bin = example_dir / "Build" / "Bin"
    if not build_bin.is_dir():
        raise FileNotFoundError(f"Build output not found: {build_bin}")

    changed = 0
    scanned = 0

    for cfg_name, project_dir in iter_project_dirs(build_bin):
        scanned += 1
        project_name = project_dir.name

        is_windows = "windows" in cfg_name.lower()
        is_linux = "linux" in cfg_name.lower()
        is_macos = "macos" in cfg_name.lower()
        is_web = "web" in cfg_name.lower()

        if is_windows:
            exe = project_dir / f"{project_name}.exe"
            if exe.is_file():
                path = project_dir / "run.bat"
                if write_if_changed(path, windows_native_launcher(project_name)):
                    changed += 1
                    if verbose:
                        print(f"[launcher] updated {path}")

        if is_linux or is_macos:
            native_bin = project_dir / project_name
            if native_bin.is_file():
                path = project_dir / "run.sh"
                if write_if_changed(path, posix_native_launcher(project_name), make_executable=True):
                    changed += 1
                    if verbose:
                        print(f"[launcher] updated {path}")

        if is_web:
            html = find_web_html(project_dir, project_name)
            if html is not None:
                bat = project_dir / "run_web.bat"
                sh = project_dir / "run_web.sh"
                if write_if_changed(bat, windows_web_launcher(html.name)):
                    changed += 1
                    if verbose:
                        print(f"[launcher] updated {bat}")
                if write_if_changed(sh, posix_web_launcher(html.name), make_executable=True):
                    changed += 1
                    if verbose:
                        print(f"[launcher] updated {sh}")

    print(f"[launcher] scanned {scanned} project output folder(s), updated {changed} launcher file(s).")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate run launchers for Jenga build outputs.")
    parser.add_argument(
        "--example-dir",
        required=True,
        help="Path to example directory (contains Build/Bin).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print each generated file.",
    )
    args = parser.parse_args()

    example_dir = Path(args.example_dir).resolve()
    if not example_dir.is_dir():
        raise FileNotFoundError(f"Example directory not found: {example_dir}")
    generate(example_dir, verbose=args.verbose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
