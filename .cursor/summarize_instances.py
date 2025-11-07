import json
import sys
from pathlib import Path


def _load_json(path: Path) -> dict:
    encodings = ["utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be"]
    last_error: Exception | None = None
    for enc in encodings:
        try:
            return json.loads(path.read_text(encoding=enc))
        except UnicodeDecodeError as exc:
            last_error = exc
    raise last_error if last_error else ValueError(f"Unable to decode JSON at {path}")


def main(path: str | None = None) -> int:
    if path is None:
        if len(sys.argv) > 1:
            path = sys.argv[1]
        else:
            path = ".cursor/tmp_instances.json"
    data = _load_json(Path(path))
    reservations = data.get("Reservations", [])
    for res in reservations:
        for inst in res.get("Instances", []):
            tags = {tag.get("Key"): tag.get("Value") for tag in inst.get("Tags", [])}
            name = tags.get("Name", "")
            iid = inst.get("InstanceId", "")
            state = inst.get("State", {}).get("Name", "")
            print(f"{iid}\t{state}\t{name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

