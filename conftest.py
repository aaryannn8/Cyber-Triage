import sys
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PROTOTYPE_DIR = os.path.join(ROOT_DIR, "Cyber Triage Prototype")

for path in [ROOT_DIR, PROTOTYPE_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)
