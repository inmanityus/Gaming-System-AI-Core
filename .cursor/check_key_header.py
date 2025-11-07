from pathlib import Path


def main(path: str = ".cursor/aws/gaming-system-ai-core-admin.pem") -> None:
    text = Path(path).read_text(encoding="utf-8")
    first_line = text.splitlines()[0] if text else ""
    print(first_line)


if __name__ == "__main__":
    main()

