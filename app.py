import os
import sys

# Ensure root directory and ui directory are in sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
ui_dir = os.path.join(root_dir, "ui")

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if ui_dir not in sys.path:
    sys.path.insert(0, ui_dir)

# Import and execute main Streamlit application logic from ui/app.py
from ui.app import *
