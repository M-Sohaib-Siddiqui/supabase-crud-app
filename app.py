import os
import sys
import runpy

# Ensure root directory and python_client directory are in sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
ui_dir = os.path.join(root_dir, "ui")

for path in [root_dir, ui_dir]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Execute ui/app.py as __main__ for Streamlit Cloud
target_script = os.path.join(ui_dir, "app.py")
runpy.run_path(target_script, run_name="__main__")
