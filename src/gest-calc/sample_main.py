import sys
from pathlib import Path

# Redirecciona a la implementacion completa en main.py
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from main import main

if __name__ == "__main__":
    main()
