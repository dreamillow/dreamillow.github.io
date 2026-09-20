"""Extract ordered content blocks from a saved Blogger page."""
import re
import sys
from html.parser import HTMLParser

BLOCK = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "div", "li"}
SKIP = {"script", "style", "svg", "button", "noscript", "form"}
HEADING = {"h1", "h2", "h3", "h4", "h5", "h6"}
CHROME = {"Share this post", "Get link", "Report Abuse", "Comments"}


def normalize(text):
    text = text.replace(" ", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    return text.strip()


class PostBodyExtractor(HTMLParser):
    """Capture the post-body subtree, emitting one block per heading/paragraph/list item."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.capturing = False
        self.skip_depth = 0
        self.stack = []
        self.blocks = []

    def _is_post_body(self, attrs):
        classes = dict(attrs).get("class", "")
        return "post-body" in classes and "entry-content" in classes

    def handle_starttag(self, tag, attrs):
        if self.skip_depth:
            if tag in SKIP:
                self.skip_depth += 1
            return
        if tag in SKIP:
            self.skip_depth = 1
            return

        if not self.capturing:
            if tag == "div" and self._is_post_body(attrs):
                self.capturing = True
                self.depth = 1
            return

        if tag == "div":
            self.depth += 1
        if tag == "br":
            if self.stack:
                self.stack[-1][1] += "\n"
            return
        if tag == "img":
            src = dict(attrs).get("src", "")
            self.blocks.append(("img", src))
            return
        if tag in BLOCK:
            self.stack.append([tag, ""])

    def handle_endtag(self, tag):
        if self.skip_depth:
            if tag in SKIP:
                self.skip_depth -= 1
            return
        if not self.capturing:
            return

        if tag in BLOCK and self.stack:
            for index in range(len(self.stack) - 1, -1, -1):
                if self.stack[index][0] == tag:
                    _, text = self.stack.pop(index)
                    self._flush(tag, text)
                    break

        if tag == "div":
            self.depth -= 1
            if self.depth <= 0:
                self.capturing = False

    def handle_data(self, data):
        if self.capturing and not self.skip_depth and self.stack:
            self.stack[-1][1] += data

    def _flush(self, tag, text):
        kind = "h2" if tag in HEADING else ("li" if tag == "li" else "p")
        for part in text.split("\n"):
            part = normalize(part)
            if part:
                self.blocks.append((kind, part))


def extract(path):
    parser = PostBodyExtractor()
    with open(path, encoding="utf-8") as handle:
        parser.feed(handle.read())

    blocks = parser.blocks
    cut = len(blocks)
    for index, (_, text) in enumerate(blocks):
        if text in CHROME:
            cut = min(cut, index)
    return blocks[:cut]


if __name__ == "__main__":
    for kind, text in extract(sys.argv[1]):
        print(f"[{kind}] {text}")
