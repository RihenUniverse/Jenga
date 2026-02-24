import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Jenga', 'Exemples', 'NKWindow'))

from pathlib import Path
from Jenga.Core.Builders.Windows import WindowsBuilder

orig_pch = WindowsBuilder.PreparePCH
def patched_pch(self, project, obj_dir):
    print("[PCH-DEBUG] name=%r pchHeader=%r" % (project.name, project.pchHeader), flush=True, file=sys.stderr)
    ret = orig_pch(self, project, obj_dir)
    print("[PCH-DEBUG] ret=%r" % ret, flush=True, file=sys.stderr)
    return ret
WindowsBuilder.PreparePCH = patched_pch

orig_bp = WindowsBuilder.BuildProject
def patched_bp(self, project, *a, **kw):
    print("[BUILD-DEBUG] start %r" % project.name, flush=True, file=sys.stderr)
    try:
        r = orig_bp(self, project, *a, **kw)
        print("[BUILD-DEBUG] done %r ret=%r" % (project.name, r), flush=True, file=sys.stderr)
        return r
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise
WindowsBuilder.BuildProject = patched_bp

import importlib.util
jenga_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Jenga', 'jenga.py')
spec = importlib.util.spec_from_file_location('jenga_main', jenga_path)
mod = importlib.util.module_from_spec(spec)
sys.argv = ['jenga.py', 'build', '--system', 'Windows', '--config', 'Debug']
spec.loader.exec_module(mod)
