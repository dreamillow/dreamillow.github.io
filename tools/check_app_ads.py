"""Verify app-ads.txt matches what the spec requires."""
import pathlib
import sys

EXPECTED_LINES = 127
EXPECTED_DIRECT = [
    "ironsrc.com, 631887, DIRECT",
    "vungle.com, 6aab47ebadbd10019b9a09cd, DIRECT, c107d686becd2d77",
    "google.com, pub-8558658162311217, DIRECT, f08c47fec0942fa0",
]


def relationship(line):
    parts = [p.strip() for p in line.split(",")]
    return parts[2].upper() if len(parts) >= 3 else ""


def main():
    path = pathlib.Path("app-ads.txt")
    errors = []

    if not path.exists():
        print("FAIL: app-ads.txt does not exist")
        return 1

    raw = path.read_text(encoding="utf-8")
    if not raw.endswith("\n"):
        errors.append("file must end with a newline")

    lines = [line for line in raw.splitlines() if line.strip()]

    if len(lines) != EXPECTED_LINES:
        errors.append(f"expected {EXPECTED_LINES} non-empty lines, got {len(lines)}")

    owner = [line for line in lines if line.upper().replace(" ", "").startswith("OWNERDOMAIN=")]
    if owner:
        errors.append(f"OWNERDOMAIN line must be removed, found: {owner}")

    direct = [line for line in lines if relationship(line) == "DIRECT"]
    if direct != EXPECTED_DIRECT:
        errors.append(f"DIRECT lines changed.\n  expected: {EXPECTED_DIRECT}\n  got:      {direct}")

    for error in errors:
        print(f"FAIL: {error}")

    if errors:
        return 1
    print(f"OK: app-ads.txt has {len(lines)} lines, {len(direct)} DIRECT, no OWNERDOMAIN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
