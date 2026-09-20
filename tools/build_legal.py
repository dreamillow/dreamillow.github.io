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
<link rel="stylesheet" href="/assets/style.css">
</head>
<body>

<header class="nav">
  <a class="wordmark" href="/index.html">Dreamillow</a>
  <nav aria-label="Main">
    <a href="/index.html#about">About</a>
    <a href="/index.html#contact">Contact</a>
  </nav>
</header>

<main class="prose">
{body}
</main>

<footer class="footer">
  <p>&copy; Dreamillow</p>
  <nav aria-label="Legal">
    <a href="/privacy.html">Privacy Policy</a>
    <a href="/terms.html">Terms of Service</a>
  </nav>
</footer>

</body>
</html>
"""

PAGES = [
    ("tools/fixtures/blogger-privacy.html", "privacy.html", "Privacy Policy"),
    ("tools/fixtures/blogger-terms.html", "terms.html", "Terms of Service"),
]

# Country -> minimum age, transcribed by hand from the "age restrictions by
# country" table image in the Blogger source (see
# tools/fixtures/blogger-privacy-ages.png). Order matches the source image.
AGE_TABLE_ROWS = [
    ("Austria", "14"),
    ("Belgium", "13"),
    ("Bulgaria", "13"),
    ("Croatia", "13"),
    ("Republic of Cyprus", "13"),
    ("Czech Republic", "13"),
    ("Denmark", "13"),
    ("Estonia", "13"),
    ("Finland", "15"),
    ("France", "16"),
    ("Germany", "16"),
    ("Greece", "13"),
    ("Hungary", "16"),
    ("Ireland", "13"),
    ("Italy", "13"),
    ("Latvia", "13"),
    ("Lithuania", "16"),
    ("Luxembourg", "16"),
    ("Malta", "13"),
    ("Netherlands", "16"),
    ("Poland", "13"),
    ("Portugal", "13"),
    ("Romania", "13"),
    ("Slovakia", "16"),
    ("Slovenia", "13"),
    ("Spain", "13"),
    ("Sweden", "13"),
    ("United Kingdom", "13"),
    ("Rest of the world (excluding Korea)", "13"),
]


def _render_age_table():
    rows = "\n".join(
        f"      <tr><th scope=\"row\">{html.escape(country)}</th><td>{html.escape(age)}</td></tr>"
        for country, age in AGE_TABLE_ROWS
    )
    return (
        '<div class="table-wrap" tabindex="0" role="region" '
        'aria-label="Minimum age by country">\n'
        "  <table>\n"
        "    <caption>Minimum age to play our games and use our Services, by country</caption>\n"
        "    <thead>\n"
        "      <tr><th scope=\"col\">Country</th>"
        "<th scope=\"col\">Age you must be to play our games and use our Services</th></tr>\n"
        "    </thead>\n"
        "    <tbody>\n"
        f"{rows}\n"
        "    </tbody>\n"
        "  </table>\n"
        "</div>"
    )


# Known image sources from the Blogger fixtures, mapped to the transcribed
# HTML that should be rendered in their place. An image whose src is not
# listed here fails the build loudly instead of silently vanishing.
IMAGE_BLOCKS = {
    "https://k.kakaocdn.net/dn/pHrj1/btqDUFKPv1L/NDToHXKvWlc8bDj4SvQX7k/img.png": _render_age_table,
}


def render(blocks):
    lines = []
    in_list = False
    first_heading = True

    for kind, text in blocks:
        if kind == "img":
            if in_list:
                lines.append("</ul>")
                in_list = False
            renderer = IMAGE_BLOCKS.get(text)
            if renderer is None:
                raise Exception(f"unhandled image in legal source: {text}")
            lines.append(renderer())
            continue

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


def render_page(fixture, title):
    """Render one legal page's full HTML text in memory, without writing it."""
    blocks = extract(fixture)
    if not blocks:
        raise Exception(f"no blocks extracted from {fixture}")
    return TEMPLATE.format(title=title, body=render(blocks))


def main():
    for fixture, output, title in PAGES:
        try:
            page = render_page(fixture, title)
        except Exception as exc:
            print(f"FAIL: {exc}")
            return 1
        pathlib.Path(output).write_text(page, encoding="utf-8")
        print(f"wrote {output} from {fixture}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
