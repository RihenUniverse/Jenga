from pathlib import Path
from typing import List

from Jenga.Core.Api import Project, ProjectKind
from ...Utils import FileSystem, Process
from .AppleMobileBuilder import AppleMobileBuilder


class XcrunMobileBuilder(AppleMobileBuilder):
    """
    Builder Apple mobile utilisant xcrun (clang/clang++) directement.
    """

    def GetObjectExtension(self) -> str:
        return ".o"

    def GetOutputExtension(self, project: Project) -> str:
        if project.kind == ProjectKind.SHARED_LIB:
            return ".dylib"
        elif project.kind == ProjectKind.STATIC_LIB:
            return ".a"
        elif project.kind in (ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP, ProjectKind.TEST_SUITE):
            return ""  # exécutable Unix
        else:
            return ""

    def GetModuleFlags(self, project: Project, sourceFile: str) -> List[str]:
        if not self.IsModuleFile(sourceFile):
            return []
        return [
            "-fmodules",
            "-fcxx-modules",
            "-fbuiltin-module-map",
            *self._GetTargetFlags(),
        ]

    def Compile(self, project: Project, sourceFile: str, objectFile: str) -> bool:
        src = Path(sourceFile)
        obj = Path(objectFile)
        FileSystem.MakeDirectory(obj.parent)

        compiler = self.toolchain.cxxPath if project.language.value in ("C++", "Objective-C++") else self.toolchain.ccPath
        args = [
            compiler,
            "-c",
            "-o", str(obj),
            *self.GetDependencyFlags(str(obj)),
            *self._GetTargetFlags(),
            "-arch", self._GetArchName(),
        ]
        args.extend(self._GetCommonCompilerFlags(project))
        if self.IsModuleFile(sourceFile):
            args.extend(self.GetModuleFlags(project, sourceFile))
        args.append(str(src))

        result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
        self._lastResult = result
        return result.returnCode == 0

    def Link(self, project: Project, objectFiles: List[str], outputFile: str) -> bool:
        out = Path(outputFile)
        FileSystem.MakeDirectory(out.parent)

        if project.kind == ProjectKind.STATIC_LIB:
            # Utilisation de libtool ou ar
            if hasattr(self.toolchain, "arPath") and self.toolchain.arPath:
                ar = self.toolchain.arPath
            else:
                ar = "ar"
            args = [ar, "rcs", str(out)] + objectFiles
            result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
            self._lastResult = result
            return result.returnCode == 0

        # Pour les exécutables et libs partagées
        linker = self.toolchain.cxxPath
        args = [
            linker,
            "-o", str(out),
            *self._GetTargetFlags(),
            "-arch", self._GetArchName(),
        ]

        # Type de sortie
        if project.kind == ProjectKind.SHARED_LIB:
            args.append("-dynamiclib")

        # Frameworks
        args.extend(self._GetFrameworkLinkerArgs(project))

        # Bibliothèques
        args.extend(self._GetLibraryLinkerArgs(project))

        # Flags du linker
        args.extend(getattr(self.toolchain, "ldflags", []))
        args.extend(project.ldflags)

        # RPath pour exécutables
        if project.kind in (ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP, ProjectKind.TEST_SUITE):
            args.append("-Wl,-rpath,@loader_path/Frameworks")

        # Objets
        args.extend(objectFiles)

        result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
        self._lastResult = result
        return result.returnCode == 0