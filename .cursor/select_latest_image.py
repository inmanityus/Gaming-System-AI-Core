import json
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


def main(path: str = ".cursor/ubuntu_images.json") -> None:
    data = _load_json(Path(path))
    images = data.get("Images", [])
    if not images:
        raise SystemExit("No images found")
    latest = max(images, key=lambda img: img.get("CreationDate", ""))
    image_id = latest.get("ImageId")
    name = latest.get("Name")
    created = latest.get("CreationDate")
    print(f"{image_id}\t{name}\t{created}")


if __name__ == "__main__":
    main()

