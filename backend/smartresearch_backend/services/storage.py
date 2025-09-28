import os
from typing import Dict, Any

# folders
UPLOAD_DIR = os.path.join("data", "uploads")

# simple in-memory stores (swap with DB later)
FILES: Dict[str, Dict[str, Any]] = {}
JOBS:  Dict[str, Dict[str, Any]] = {}
