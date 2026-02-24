import sys, os, subprocess
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Jenga', 'Exemples', 'NKWindow'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Jenga.Core.Builders.Windows import WindowsBuilder

orig_pch = WindowsBuilder.PreparePCH

def patched_pch(self, project, obj_dir):
    if project.pchHeader:
        from pathlib import Path
        header_path = Path(self.ResolveProjectPath(project, project.pchHeader))
        sys.stderr.write("[PCH-DEBUG] name=%s\n" % project.name)
        sys.stderr.write("[PCH-DEBUG] header=%s exists=%s\n" % (header_path, header_path.exists()))
        pch_file = obj_dir / ("%s.pch" % project.name)
        compiler = self.toolchain.cxxPath or self.toolchain.ccPath
        args = [str(compiler), "-x", "c++-header", str(header_path), "-o", str(pch_file)]
        for inc in project.includeDirs:
            args.append("-I" + self.ResolveProjectPath(project, inc))
        sys.stderr.write("[PCH-DEBUG] cmd: %s\n" % " ".join(args))
        try:
            result = subprocess.run(args, capture_output=True, text=True)
            sys.stderr.write("[PCH-DEBUG] rc=%d\n" % result.returncode)
            if result.returncode != 0:
                sys.stderr.write("[PCH-DEBUG] stdout=%s\n" % result.stdout)
                sys.stderr.write("[PCH-DEBUG] stderr=%s\n" % result.stderr)
        except Exception as e:
            sys.stderr.write("[PCH-DEBUG] exception: %s\n" % str(e))
    return orig_pch(self, project, obj_dir)

WindowsBuilder.PreparePCH = patched_pch

import importlib.util
jenga_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Jenga', 'jenga.py')
spec = importlib.util.spec_from_file_location('jenga_main', jenga_path)
mod = importlib.util.module_from_spec(spec)
sys.argv = ['jenga.py', 'build', '--system', 'Windows', '--config', 'Debug']
spec.loader.exec_module(mod)
