"""
Create an isolated copy of the current project into ./isolated_project.
Run this script from the repository root:
.venv\Scripts\python.exe tools\create_isolated_copy.py
"""
import os
import shutil

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
target = os.path.join(root, 'isolated_project')
# exclude patterns
exclude = ['isolated_project', '.git', '.venv', 'venv', '__pycache__', 'node_modules']

if os.path.exists(target):
    print('Target already exists at', target)
else:
    def ignore_func(path, names):
        ignored = set()
        for ex in exclude:
            if ex in names:
                ignored.add(ex)
        return ignored

    shutil.copytree(root, target, ignore=shutil.ignore_patterns(*exclude))
    print('Copied project to', target)
