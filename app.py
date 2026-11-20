"""AirCursor source-checkout launcher: python app.py --lan."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from aircursor.cli import main  # noqa: E402


if __name__ == "__main__":
    main()
