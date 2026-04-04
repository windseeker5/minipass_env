import json
import os
import sys

from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

load_dotenv(os.path.join(BASE_DIR, ".env"))

from utils.kpi_helpers import capture_kpi_snapshots  # noqa: E402


if __name__ == "__main__":
    snapshots = capture_kpi_snapshots()
    print(json.dumps(snapshots, indent=2))
