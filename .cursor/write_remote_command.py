import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: write_remote_command.py '<command>'")
    command = sys.argv[1]
    path = Path(".cursor/remote-command.txt")
    path.write_text(command, encoding="utf-8")


if __name__ == "__main__":
    main()

