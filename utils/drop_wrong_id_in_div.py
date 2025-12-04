import re
from pathlib import Path

LOG_FILE = "tolstaya_diaries_log.txt"

# Регекс для строк вида:
# Line 83, Column 69: xml:id : attribute value 1905.1_января is not an NCName
ERROR_RE = re.compile(
    r'Line\s+(\d+).*?attribute value\s+([^\s]+)\s+is not an NCName'
)


def process_file(xml_path: Path, broken_ids):
    """Fix XML file by clearing invalid xml:id attributes."""
    if not xml_path.exists():
        print(f"[WARN] File not found: {xml_path}")
        return

    text = xml_path.read_text(encoding="utf-8")

    for value in broken_ids:
        # Pattern like xml:id="1905.1_января"
        pattern = rf' xml:id="{re.escape(value)}"'
        replacement = ''

        if re.search(pattern, text):
            text = re.sub(pattern, replacement, text)
            print(f"[FIX] {xml_path}: cleared xml:id=\"{value}\"")
        else:
            print(f"[MISS] Not found in {xml_path}: {value}")

    xml_path.write_text(text, encoding="utf-8")


def parse_log():
    """Parse log and return dict {file: [broken_ids]}"""
    result = {}
    current_file = None

    with open(LOG_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip()

            # Detect start of a block: "❌ some/path.xml"
            if line.startswith("❌"):
                # Extract path after the symbol ❌
                parts = line.split("❌", 1)[1].strip()
                current_file = Path(parts)
                result.setdefault(current_file, [])
                continue

            if current_file:
                # Try to extract broken value
                m = ERROR_RE.search(line)
                if m:
                    value = m.group(2)  # the invalid xml:id value
                    result[current_file].append(value)

    return result


def main():
    data = parse_log()
    current_file = Path(__file__).resolve().parent.parent
    print(f"{current_file=}")
    print("\n=== Parsed files and IDs to fix ===")
    for file, ids in data.items():
        print(f"{file}: {ids}")

    print("\n=== Starting fixes ===")
    for file, ids in data.items():
        file = current_file / file
        process_file(file, ids)

    print("\nDone.")


if __name__ == "__main__":
    main()
