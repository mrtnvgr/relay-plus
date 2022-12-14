import subprocess
import os


def run(
    cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kwargs
):
    return subprocess.run(cmd, check=check, stdout=stdout, stderr=stderr, **kwargs)


def fixcwd():
    """Set current working directory to script path"""
    os.chdir(os.path.dirname(__file__))


def update():
    cmds = (["git", "fetch"], ["git", "merge"])
    for cmd in cmds:
        run(cmd)
    exit(0)
