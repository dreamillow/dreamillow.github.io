"""Render extracted Blogger blocks into static legal pages."""
import html
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from extract_blogspot import extract  # noqa: E402

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} &mdash; Dreamillow</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>

<header class="nav">
  <a class="wordmark" href="index.html">Dreamillow</a>
  <nav>
    <a href="index.html#about">About</a>
    <a href="index.html#contact">Contact</a>
  </nav>
</header>

<main class="prose">
{body}
</main>

<footer class="footer">
  <p>&copy; Dreamillow</p>
  <nav>
    <a href="privacy.html">Privacy Policy</a>
    <a href="terms.html">Terms of Service</a>
  </nav>
</footer>

</body>
</html>
"""

PAGES = [
    ("tools/fixtures/blogger-privacy.html", "privacy.html", "Privacy Policy"),
    ("tools/fixtures/blogger-terms.html", "terms.html", "Terms of Service"),
]


def render(blocks):
    lines = []
    in_list = False
    first_heading = True

    for kind, text in blocks:
        escaped = html.escape(text)

        if kind == "li":
            if not in_list:
                lines.append("<ul>")
                in_list = True
            lines.append(f"  <li>{escaped}</li>")
            continue

        if in_list:
            lines.append("</ul>")
            in_list = False

        if kind == "h2":
            tag = "h1" if first_heading else "h2"
            first_heading = False
            lines.append(f"<{tag}>{escaped}</{tag}>")
        else:
            lines.append(f"<p>{escaped}</p>")

    if in_list:
        lines.append("</ul>")

    return "\n".join(lines)


def main():
    for fixture, output, title in PAGES:
        blocks = extract(fixture)
        if not blocks:
            print(f"FAIL: no blocks extracted from {fixture}")
            return 1
        page = TEMPLATE.format(title=title, body=render(blocks))
        pathlib.Path(output).write_text(page, encoding="utf-8")
        print(f"wrote {output} from {len(blocks)} blocks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
