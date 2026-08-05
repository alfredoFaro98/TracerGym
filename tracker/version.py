import subprocess
from functools import lru_cache
from pathlib import Path

# Major version: da alzare a mano solo per milestone vere e proprie.
MAJOR_VERSION = 1

_REPO_ROOT = Path(__file__).resolve().parent.parent


@lru_cache(maxsize=1)
def get_app_version():
    """MAJOR_VERSION + numero totale di commit (calcolato una volta sola per processo).

    Cosi' la versione cresce da sola ad ogni push, senza doverla incrementare a mano.
    """
    try:
        commit_count = subprocess.check_output(
            ['git', 'rev-list', '--count', 'HEAD'],
            cwd=_REPO_ROOT,
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        return f"{MAJOR_VERSION}.{commit_count}"
    except (subprocess.SubprocessError, OSError):
        return f"{MAJOR_VERSION}.0"
