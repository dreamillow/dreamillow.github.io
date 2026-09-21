"""Static checks over every HTML page in the repository root."""
import pathlib
import re
import sys
from html.parser import HTMLParser

ALLOWED_SCHEMES = ("mailto:",)


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []       # href values
        self.sources = []     # src / stylesheet href values
        self.ids = set()
        self.headings = []    # heading levels in document order
        self.lang = None
        self.has_viewport = False
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "html":
            self.lang = attrs.get("lang")
        if tag == "meta" and attrs.get("name") == "viewport":
            self.has_viewport = True
        if tag == "title":
            self._in_title = True
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])
        if tag == "link" and "href" in attrs:
            self.sources.append(attrs["href"])
        if tag in ("script", "img", "iframe") and "src" in attrs:
            self.sources.append(attrs["src"])
        if re.fullmatch(r"h[1-6]", tag):
            self.headings.append(int(tag[1]))

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def check_page(path, errors):
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    name = path.name

    if parser.lang != "en":
        errors.append(f"{name}: <html lang> must be 'en', got {parser.lang!r}")
    if not parser.has_viewport:
        errors.append(f"{name}: missing viewport meta tag")
    if not parser.title.strip():
        errors.append(f"{name}: missing non-empty <title>")

    # No external resource loads. This is the rule that keeps the page free of
    # third-party requests: stylesheets, scripts, fonts and images must all be
    # served from this origin.
    for value in parser.sources:
        if value.startswith(("http://", "https://", "//")):
            errors.append(f"{name}: external resource not allowed: {value}")
        elif ":" in value.split("/")[0] and not value.startswith(ALLOWED_SCHEMES):
            errors.append(f"{name}: unexpected URL scheme: {value}")

    # Hyperlinks are a different matter — they fetch nothing until a visitor
    # clicks them, so linking out (to a store page, say) is allowed. Require
    # https so we never hand a visitor an insecure hop.
    for value in parser.links:
        if value.startswith("https://") or value.startswith(ALLOWED_SCHEMES):
            continue
        if value.startswith(("http://", "//")):
            errors.append(f"{name}: outbound link must use https: {value}")
        elif ":" in value.split("/")[0]:
            errors.append(f"{name}: unexpected URL scheme: {value}")

    # heading levels must not skip
    previous = 0
    for level in parser.headings:
        if previous and level > previous + 1:
            errors.append(f"{name}: heading jumps from h{previous} to h{level}")
        previous = level
    if parser.headings and parser.headings[0] != 1:
        errors.append(f"{name}: first heading must be h1, got h{parser.headings[0]}")

    return parser


def check_links(pages, errors, root):
    for path, parser in pages.items():
        for href in parser.links:
            # Anything with a scheme points off this filesystem; the loop above
            # has already judged whether it is allowed.
            if "://" in href or href.startswith(ALLOWED_SCHEMES):
                continue
            target, _, fragment = href.partition("#")
            if target:
                if target.startswith("/"):
                    # Root-absolute path: resolve against the repository
                    # root, not the filesystem root. (pathlib discards the
                    # left operand of `/` when the right side is absolute.)
                    destination = root / target.lstrip("/")
                else:
                    destination = path.parent / target
                if not destination.exists():
                    errors.append(f"{path.name}: link target missing: {href}")
                    continue
            else:
                destination = path
            if fragment:
                target_parser = pages.get(destination.resolve())
                if target_parser is None:
                    errors.append(f"{path.name}: cannot resolve anchor page for {href}")
                elif fragment not in target_parser.ids:
                    errors.append(f"{path.name}: anchor #{fragment} not found in {destination.name}")


def main():
    root = pathlib.Path(".")
    html_files = sorted(root.glob("*.html"))
    if not html_files:
        print("FAIL: no HTML files found in repository root")
        return 1

    errors = []
    pages = {}
    for path in html_files:
        pages[path.resolve()] = check_page(path, errors)

    check_links(pages, errors, root)

    css = pathlib.Path("assets/style.css")
    if css.exists():
        text = css.read_text(encoding="utf-8")
        rule_re = re.compile(r"([^{}]+)\{([^{}]*)\}")
        hidden_re = re.compile(
            r"(?:^|;)\s*(?:opacity\s*:\s*0(?:\.0+)?\b"
            r"|display\s*:\s*none\b"
            r"|visibility\s*:\s*hidden\b)",
            re.I,
        )
        found_scoped_hide = False
        for selector_text, declarations in rule_re.findall(text):
            for selector in selector_text.split(","):
                selector = selector.strip()
                if ".reveal" not in selector:
                    continue
                if not hidden_re.search(declarations):
                    continue
                if re.search(r"\.js\b.*\.reveal", selector):
                    found_scoped_hide = True
                else:
                    errors.append(
                        f"assets/style.css: rule '{selector} {{ {declarations.strip()} }}' "
                        "hides .reveal without being scoped under .js, which would blank "
                        "the page's content for visitors without JavaScript"
                    )
        if ".reveal" in text and not found_scoped_hide:
            errors.append(
                "assets/style.css: .reveal must only be hidden under the .js class "
                "so the page stays readable without JavaScript"
            )

    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        return 1
    print(f"OK: {len(html_files)} page(s) checked, no issues")
    return 0


if __name__ == "__main__":
    sys.exit(main())
