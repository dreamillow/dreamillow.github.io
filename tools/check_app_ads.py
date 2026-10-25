"""Verify app-ads.txt is exactly the union of the ad networks' own seller lists.

app-ads.txt is never edited by hand. Each network's list is kept verbatim in
tools/app_ads_sources/ and app-ads.txt is generated from them:

    base.txt   the list carried over from Blogger (LevelPlay, Liftoff, AdMob), 2026-09-21
    unity.txt  Unity Dashboard > Monetization > Organization settings > app-ads.txt,
               copied with the page's copy button on 2026-10-25

Output order: every line of base.txt as is, then the unity.txt lines that are not
already present, in unity.txt order.

    python3 tools/check_app_ads.py           verify (exit 0 OK, exit 1 with FAIL: lines)
    python3 tools/check_app_ads.py --write   regenerate app-ads.txt from the sources
    python3 tools/check_app_ads.py --live    also compare the deployed file byte for byte

When a network updates its list, replace that source file with the new copy, update
its hash in SOURCE_SHA256, run --write, then run the check.
"""
import hashlib
import pathlib
import re
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGET = ROOT / "app-ads.txt"
SOURCES_DIR = ROOT / "tools" / "app_ads_sources"
LIVE_URL = "https://dreamillow.github.io/app-ads.txt"

# Pinned so an accidental edit of a snapshot fails the check.
SOURCE_SHA256 = {
    "base.txt": "f0ac04c8b3e5b9da8865fd6003c84a18c1855a25e8fa57cc1ccfc42a5cf2d3b8",
    "unity.txt": "b1090ee87122daa180bf6a810bf61afcd6e744d31a6e1d4586405a9c62f12304",
}

# Our own accounts. Each value is confirmed in that network's dashboard.
EXPECTED_DIRECT = {
    "ironsrc.com, 631887, DIRECT",                                     # LevelPlay
    "vungle.com, 6aab47ebadbd10019b9a09cd, DIRECT, c107d686becd2d77",  # Liftoff Monetize
    "google.com, pub-8558658162311217, DIRECT, f08c47fec0942fa0",      # AdMob publisher ID
    "unity.com, 2144453, DIRECT, 96cabb5fbdde37a7",                    # Unity developer ID
}

# The same seller account listed more than once with a different certification ID.
# Each line is kept exactly as its source gave it; any new case fails until reviewed.
KNOWN_VARIANTS = {
    # base.txt has it with and without the ID.
    ("rubiconproject.com", "25978"),
    # base.txt line 68 carries smartadserver's ID (060d053dcf45cbf3); unity.txt adds
    # the sharethrough ID (d53b998a7bd4ecd2) used by every other sharethrough line.
    ("sharethrough.com", "5828"),
}

LINE_RE = re.compile(
    r"(?P<domain>[a-z0-9-]+(?:\.[a-z0-9-]+)+), "
    r"(?P<account>[^,\s]+), "
    r"(?P<relation>DIRECT|RESELLER)"
    r"(?:, (?P<cert>[0-9a-f]+))?"
)


def parse(line):
    """Returns (domain, account, relation, cert) or None when the line is malformed."""
    match = LINE_RE.fullmatch(line)
    if not match:
        return None
    return match["domain"], match["account"], match["relation"], match["cert"] or ""


def read_lines(path, errors):
    """Lines of an ASCII, LF-only file that ends with a newline; every line must parse."""
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        errors.append(f"{path.name}: starts with a UTF-8 BOM")
    if b"\r" in raw:
        errors.append(f"{path.name}: contains CR characters (use LF only)")
    if not raw.endswith(b"\n"):
        errors.append(f"{path.name}: must end with a newline")
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError:
        errors.append(f"{path.name}: contains non-ASCII bytes")
        text = raw.decode("utf-8", errors="replace")
    lines = text[:-1].split("\n") if text.endswith("\n") else text.split("\n")
    for number, line in enumerate(lines, 1):
        if parse(line) is None:
            errors.append(f"{path.name}:{number}: malformed line {line!r}")
    return lines


def load_sources(errors):
    sources = {}
    for name, expected in SOURCE_SHA256.items():
        path = SOURCES_DIR / name
        if not path.exists():
            errors.append(f"missing source {path}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"{name}: sha256 {actual} does not match the pinned {expected}")
        lines = read_lines(path, errors)
        if len(set(lines)) != len(lines):
            errors.append(f"{name}: has duplicate lines")
        sources[name] = lines
    return sources


def build(sources):
    """base.txt as is, then the unseen lines of every other source in order."""
    output = list(sources.get("base.txt", []))
    seen = set(output)
    for name in SOURCE_SHA256:
        if name == "base.txt":
            continue
        for line in sources.get(name, []):
            if line not in seen:
                output.append(line)
                seen.add(line)
    return output


def check(lines, sources, errors):
    if len(set(lines)) != len(lines):
        errors.append("app-ads.txt: has duplicate lines")

    expected = build(sources)
    if lines != expected:
        errors.append("app-ads.txt differs from the sources (run --write)")
        errors.extend(f"  missing: {line}" for line in sorted(set(expected) - set(lines)))
        errors.extend(f"  not in any source: {line}" for line in sorted(set(lines) - set(expected)))
        if set(lines) == set(expected):
            errors.append("  same lines in a different order")

    parsed = [p for p in map(parse, lines) if p]

    direct = {line for line in lines if (parse(line) or ("", "", "", ""))[2] == "DIRECT"}
    errors.extend(f"unexpected DIRECT line: {line}" for line in sorted(direct - EXPECTED_DIRECT))
    errors.extend(f"missing DIRECT line: {line}" for line in sorted(EXPECTED_DIRECT - direct))

    variants = {}
    for domain, account, relation, cert in parsed:
        variants.setdefault((domain, account), set()).add((relation, cert))
    for (domain, account), values in sorted(variants.items()):
        if len({relation for relation, _ in values}) > 1:
            errors.append(f"{domain}, {account}: listed as both DIRECT and RESELLER")
        elif len(values) > 1 and (domain, account) not in KNOWN_VARIANTS:
            errors.append(f"{domain}, {account}: new certification ID variants {sorted(values)}")
    varying = {key for key, values in variants.items() if len(values) > 1}
    for domain, account in sorted(KNOWN_VARIANTS - varying):
        errors.append(f"{domain}, {account}: listed in KNOWN_VARIANTS but no longer varies")


def check_live(local, errors):
    request = urllib.request.Request(LIVE_URL, headers={"Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            remote = response.read()
    except OSError as error:
        errors.append(f"could not fetch {LIVE_URL}: {error}")
        return
    if remote != local:
        errors.append(f"{LIVE_URL} differs from the local app-ads.txt (not deployed yet?)")


def main(argv):
    errors = []
    sources = load_sources(errors)

    if "--write" in argv:
        if errors:
            for error in errors:
                print(f"FAIL: {error}")
            return 1
        TARGET.write_bytes(("\n".join(build(sources)) + "\n").encode("ascii"))
        print(f"wrote {TARGET.name}")

    if not TARGET.exists():
        print("FAIL: app-ads.txt does not exist")
        return 1
    lines = read_lines(TARGET, errors)
    check(lines, sources, errors)
    if "--live" in argv:
        check_live(TARGET.read_bytes(), errors)

    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        return 1
    direct = sum(1 for line in lines if parse(line)[2] == "DIRECT")
    print(f"OK: app-ads.txt has {len(lines)} lines, {direct} DIRECT, built from {', '.join(SOURCE_SHA256)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
