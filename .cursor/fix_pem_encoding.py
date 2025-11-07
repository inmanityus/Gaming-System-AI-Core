from pathlib import Path


def main(path: str = ".cursor/aws/gaming-system-ai-core-admin.pem") -> None:
    pem_path = Path(path)
    data = pem_path.read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "latin-1"):
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise SystemExit("Unable to decode key file")

    pem_path.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()

