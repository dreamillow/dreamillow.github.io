"""Verify the generated legal pages carry the Blogger text verbatim."""
import difflib
import html
import pathlib
import re
import sys
from html.parser import HTMLParser

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from extract_blogspot import extract, normalize  # noqa: E402
from build_legal import PAGES as BUILD_PAGES, render_page  # noqa: E402

HANGUL = re.compile(r"[가-힣]")
SKIP_TAGS = ("script", "style", "svg", "button", "noscript", "form")

PAIRS = [
    ("privacy.html", "tools/fixtures/blogger-privacy.html"),
    ("terms.html", "tools/fixtures/blogger-terms.html"),
]


def reference_words(fixture):
    """Tag-stripped words from the Blogger post body, cut where its Korean UI starts."""
    source = pathlib.Path(fixture).read_text(encoding="utf-8")
    start = source.find("post-body entry-content float-container")
    start = source.find(">", start) + 1
    body = source[start:]
    for tag in SKIP_TAGS:
        body = re.sub(rf"<{tag}\b.*?</{tag}>", " ", body, flags=re.S | re.I)
    text = html.unescape(re.sub(r"<[^>]+>", " ", body))
    words = normalize(text.replace("\n", " ")).split()
    for index, word in enumerate(words):
        if index > 50 and HANGUL.search(word):
            return words[:index]
    return words


class ProseParser(HTMLParser):
    """Collect the text inside <main class="prose">, excluding <table> content.

    Tables hold transcribed image content (e.g. the age-restriction table),
    which never existed as text in the Blogger source, so it is out of scope
    for this verbatim-text check.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.inside = False
        self.depth = 0
        self.table_depth = 0
        self.text = []

    def handle_starttag(self, tag, attrs):
        if tag == "main" and "prose" in dict(attrs).get("class", ""):
            self.inside = True
            self.depth = 0
            return
        if self.inside and tag == "main":
            self.depth += 1
        if self.inside and tag == "table":
            self.table_depth += 1

    def handle_endtag(self, tag):
        if self.inside and tag == "table" and self.table_depth:
            self.table_depth -= 1
        if self.inside and tag == "main":
            if self.depth == 0:
                self.inside = False
            else:
                self.depth -= 1

    def handle_data(self, data):
        if self.inside and not self.table_depth:
            self.text.append(data)


def prose_words(page):
    parser = ProseParser()
    parser.feed(pathlib.Path(page).read_text(encoding="utf-8"))
    return normalize(" ".join(parser.text).replace("\n", " ")).split()


def check_regeneration(errors):
    """Confirm the committed pages are exactly what build_legal.py produces.

    Renders each page in memory via build_legal's own functions and compares
    against the committed bytes on disk -- never writes to the repository.
    """
    for fixture, output, title in BUILD_PAGES:
        output_path = pathlib.Path(output)
        if not output_path.exists():
            errors.append(f"{output} does not exist")
            continue
        try:
            rendered = render_page(fixture, title)
        except Exception as exc:
            errors.append(f"{output}: could not regenerate from {fixture}: {exc}")
            continue
        committed = output_path.read_text(encoding="utf-8")
        if rendered != committed:
            errors.append(
                f"{output}: does not match output of build_legal.py -- "
                "regenerate with `python3 tools/build_legal.py`"
            )


def main():
    errors = []
    for page, fixture in PAIRS:
        if not pathlib.Path(page).exists():
            errors.append(f"{page} does not exist")
            continue

        rendered = prose_words(page)
        reference = reference_words(fixture)
        matcher = difflib.SequenceMatcher(None, reference, rendered, autojunk=False)
        ratio = matcher.ratio()

        lost = []
        for op, a1, a2, _, _ in matcher.get_opcodes():
            if op in ("delete", "replace"):
                lost.append(" ".join(reference[a1:a2]))

        print(f"{page}: {len(rendered)} words vs {len(reference)} reference, ratio {ratio:.4f}")
        if ratio < 0.995:
            errors.append(f"{page}: text similarity {ratio:.4f} is below 0.995")
        for chunk in lost:
            print(f"  dropped from source: {chunk[:200]}")
        if len(lost) > 1:
            errors.append(f"{page}: {len(lost)} chunks of source text are missing")

        blocks = extract(fixture)
        if not blocks:
            errors.append(f"{fixture}: extractor returned no blocks")

    check_regeneration(errors)

    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        return 1
    print("OK: legal pages match the Blogger source")
    return 0


if __name__ == "__main__":
    sys.exit(main())
