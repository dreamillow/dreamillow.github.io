# Dreamillow 홈페이지 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `dreamillow.github.io`에 단일 페이지 랜딩과 독립 URL을 가진 개인정보처리방침·이용약관 페이지, 그리고 `app-ads.txt`를 배포한다.

**Architecture:** 빌드 단계가 없는 정적 HTML 사이트. 랜딩은 앵커로 이동하는 원페이지, 법률 문서는 각각 독립 페이지. 법률 본문은 Blogger HTML에서 파이썬 스크립트로 추출해 시맨틱 HTML로 변환하며, 원문과의 일치를 자동 검증한다. `tools/` 아래 스크립트는 빌드 도구가 아니라 일회성 이전 도구이자 검증기이며, 배포되는 사이트는 저장소 루트의 정적 파일뿐이다.

**Tech Stack:** HTML5, CSS3, 바닐라 JS(`IntersectionObserver`), Python 3 표준 라이브러리(`html.parser`, `difflib`), GitHub Pages

**Spec:** `docs/superpowers/specs/2026-09-21-dreamillow-homepage-design.md`

## Global Constraints

- 사이트 콘텐츠 언어는 **영어 단일**. 한국어 문구를 페이지에 넣지 않는다
- 회사명은 정확히 `Dreamillow`, 연락처는 정확히 `dreamillowgames@gmail.com`
- **외부 의존성 0개**: CDN, 웹폰트, 분석 스크립트, 아이콘 라이브러리를 참조하지 않는다. 페이지의 모든 `href`/`src`는 상대 경로이거나 `mailto:`여야 한다
- 방침·약관 본문 텍스트는 **한 글자도 수정하지 않는다**. 오타로 보이는 것도 그대로 옮긴다
- 다크 단일 테마. 라이트 모드 대응을 하지 않는다
- 빌드 도구·패키지 매니저·CI 워크플로를 도입하지 않는다
- 모든 텍스트 파일은 개행으로 끝난다
- `app-ads.txt`는 `OWNERDOMAIN` 줄을 제거한 127줄이며, `DIRECT` 3줄이 정확히 보존되어야 한다

---

### Task 1: 저장소 골격과 app-ads.txt

**Files:**
- Create: `.nojekyll`
- Create: `app-ads.txt`
- Create: `tools/check_app_ads.py`

**Interfaces:**
- Consumes: 없음 (최초 태스크)
- Produces: 루트에 `app-ads.txt`, `.nojekyll`. 검증기 `tools/check_app_ads.py`는 인자 없이 실행하며 성공 시 exit 0, 실패 시 exit 1과 함께 `FAIL:` 로 시작하는 줄들을 출력한다

- [ ] **Step 1: 검증기를 먼저 작성한다**

`tools/check_app_ads.py`:

```python
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
```

- [ ] **Step 2: 검증기를 실행해 실패를 확인한다**

Run: `python3 tools/check_app_ads.py`
Expected: FAIL — `FAIL: app-ads.txt does not exist`, exit 1

- [ ] **Step 3: app-ads.txt를 생성한다**

Blogger가 서빙하던 파일에서 `OWNERDOMAIN` 줄만 제거한다. 줄 끝 공백도 정리한다.

```bash
curl -sSL https://dreamillow.blogspot.com/app-ads.txt \
  | grep -viE '^[[:space:]]*OWNERDOMAIN[[:space:]]*=' \
  | sed -e 's/[[:space:]]*$//' \
  > app-ads.txt
```

`grep`은 원본 마지막 줄에 개행이 없어도 출력에 개행을 붙이므로 파일은 개행으로 끝난다.

- [ ] **Step 4: 검증기를 실행해 통과를 확인한다**

Run: `python3 tools/check_app_ads.py`
Expected: PASS — `OK: app-ads.txt has 127 lines, 3 DIRECT, no OWNERDOMAIN`, exit 0

원격 파일이 바뀌어 실패하면 임의로 검증기를 고치지 말 것. AdMob 콘솔 내용이 최종 근거이므로 사용자에게 보고하고 멈춘다.

- [ ] **Step 5: .nojekyll을 만든다**

GitHub Pages가 파일을 Jekyll로 가공하지 않고 그대로 서빙하게 한다.

```bash
touch .nojekyll
```

- [ ] **Step 6: 커밋**

```bash
git add .nojekyll app-ads.txt tools/check_app_ads.py
git commit -m "Add app-ads.txt without Blogger OWNERDOMAIN line"
```

---

### Task 2: 페이지 셸 — 스타일, 랜딩, 404

**Files:**
- Create: `assets/style.css`
- Create: `index.html`
- Create: `404.html`
- Create: `tools/check_site.py`

**Interfaces:**
- Consumes: Task 1의 저장소 골격
- Produces:
  - CSS 클래스 `nav`, `wordmark`, `hero`, `section`, `prose`, `footer`, `reveal`, `mail-button`. Task 4의 법률 페이지가 `nav`, `prose`, `footer`를 그대로 쓴다
  - `<html class="js">`가 붙었을 때만 `.reveal`을 숨기는 CSS 규칙. Task 3의 `main.js`가 이 클래스를 붙인다
  - `tools/check_site.py`: 인자 없이 실행. 저장소 루트의 모든 `*.html`을 검사해 exit 0/1

- [ ] **Step 1: 사이트 검증기를 먼저 작성한다**

`tools/check_site.py`:

```python
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

    # no external resources
    for value in parser.sources + parser.links:
        if value.startswith(("http://", "https://", "//")):
            errors.append(f"{name}: external reference not allowed: {value}")
        elif ":" in value.split("/")[0] and not value.startswith(ALLOWED_SCHEMES):
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


def check_links(pages, errors):
    for path, parser in pages.items():
        for href in parser.links:
            if href.startswith(ALLOWED_SCHEMES):
                continue
            target, _, fragment = href.partition("#")
            if target:
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

    check_links(pages, errors)

    css = pathlib.Path("assets/style.css")
    if css.exists():
        text = css.read_text(encoding="utf-8")
        if ".reveal" in text and not re.search(r"\.js\s+\.reveal", text):
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
```

- [ ] **Step 2: 검증기를 실행해 실패를 확인한다**

Run: `python3 tools/check_site.py`
Expected: FAIL — `FAIL: no HTML files found in repository root`, exit 1

- [ ] **Step 3: 스타일시트를 작성한다**

`assets/style.css`:

```css
:root {
  --bg: #0d0f12;
  --surface: #15181d;
  --text: #e8eaed;
  --muted: #a3a9b3;
  --accent: #7aa2ff;
  --line: #262b33;
  --measure: 720px;
}

*, *::before, *::after { box-sizing: border-box; }

html { scroll-behavior: smooth; }

body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
    "Helvetica Neue", Arial, sans-serif;
  font-size: 17px;
  line-height: 1.7;
  -webkit-text-size-adjust: 100%;
}

a { color: var(--accent); }

a:focus-visible, button:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 3px;
}

/* ---------- nav ---------- */

.nav {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1.5rem;
  align-items: baseline;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  background: rgba(13, 15, 18, 0.9);
  border-bottom: 1px solid var(--line);
}

.wordmark {
  font-weight: 700;
  font-size: 1.05rem;
  letter-spacing: 0.02em;
  color: var(--text);
  text-decoration: none;
}

.nav nav { display: flex; gap: 1.25rem; }

.nav nav a {
  color: var(--muted);
  text-decoration: none;
  font-size: 0.95rem;
}

.nav nav a:hover { color: var(--text); }

/* ---------- layout ---------- */

.hero, .section, .prose {
  max-width: var(--measure);
  margin: 0 auto;
  padding: 0 1.25rem;
}

.hero {
  min-height: 70vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding-top: 3rem;
  padding-bottom: 3rem;
}

.hero h1 {
  margin: 0 0 0.75rem;
  font-size: clamp(2.25rem, 8vw, 3.5rem);
  line-height: 1.15;
  letter-spacing: -0.02em;
}

.hero p {
  margin: 0;
  color: var(--muted);
  font-size: clamp(1.05rem, 3.5vw, 1.3rem);
}

.section { padding-top: 3.5rem; padding-bottom: 3.5rem; }

.section h2 {
  margin: 0 0 1rem;
  font-size: 1.5rem;
  letter-spacing: -0.01em;
}

.mail-button {
  display: inline-block;
  margin-top: 0.5rem;
  padding: 0.7rem 1.4rem;
  border: 1px solid var(--accent);
  border-radius: 6px;
  color: var(--accent);
  text-decoration: none;
  font-size: 1rem;
}

.mail-button:hover { background: var(--surface); }

/* ---------- legal pages ---------- */

.prose { padding-top: 3rem; padding-bottom: 4rem; }

.prose h1 {
  font-size: 1.9rem;
  line-height: 1.25;
  margin: 0 0 2rem;
}

.prose h2 {
  font-size: 1.25rem;
  margin: 2.5rem 0 0.75rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--line);
}

.prose p { margin: 0 0 1rem; }

.prose ul { margin: 0 0 1.25rem; padding-left: 1.4rem; }

.prose li { margin-bottom: 0.4rem; }

/* ---------- footer ---------- */

.footer {
  max-width: var(--measure);
  margin: 0 auto;
  padding: 2rem 1.25rem 3rem;
  border-top: 1px solid var(--line);
  color: var(--muted);
  font-size: 0.9rem;
}

.footer p { margin: 0 0 0.5rem; }

.footer nav { display: flex; flex-wrap: wrap; gap: 1.25rem; }

/* ---------- scroll reveal ---------- */
/* Hidden only when main.js has run, so no-JS visitors still see everything. */

.js .reveal {
  opacity: 0;
  transform: translateY(16px);
  transition: opacity 0.5s ease, transform 0.5s ease;
}

.js .reveal.is-visible {
  opacity: 1;
  transform: none;
}

@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  .js .reveal {
    opacity: 1;
    transform: none;
    transition: none;
  }
}
```

- [ ] **Step 4: 랜딩 페이지를 작성한다**

`index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dreamillow</title>
<meta name="description" content="Dreamillow is an independent game studio developing mobile games.">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>

<header class="nav">
  <a class="wordmark" href="index.html">Dreamillow</a>
  <nav>
    <a href="#about">About</a>
    <a href="#contact">Contact</a>
  </nav>
</header>

<main>
  <section class="hero">
    <h1>Dreamillow</h1>
    <p>An independent game studio.</p>
  </section>

  <section class="section reveal" id="about">
    <h2>About</h2>
    <p>Dreamillow is an independent game studio developing mobile games.</p>
    <p>We publish our titles on Google Play and the App Store for players around the world.</p>
  </section>

  <section class="section reveal" id="contact">
    <h2>Contact</h2>
    <p>Questions about our games, or about this site? Write to us.</p>
    <p><a class="mail-button" href="mailto:dreamillowgames@gmail.com">dreamillowgames@gmail.com</a></p>
  </section>
</main>

<footer class="footer">
  <p>&copy; Dreamillow</p>
  <nav>
    <a href="privacy.html">Privacy Policy</a>
    <a href="terms.html">Terms of Service</a>
  </nav>
</footer>

<script src="assets/main.js"></script>
</body>
</html>
```

푸터의 `privacy.html`·`terms.html`은 Task 4에서 생성한다. 그 전까지 `tools/check_site.py`는 링크 대상 없음으로 실패하는 것이 정상이며, Step 6에서 이를 확인한다.

- [ ] **Step 5: 404 페이지를 작성한다**

`404.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page not found — Dreamillow</title>
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
  <h1>Page not found</h1>
  <p>The page you were looking for is not here.</p>
  <p><a href="index.html">Go to the home page</a></p>
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
```

- [ ] **Step 6: 검증기를 실행해 남은 실패가 링크 대상 누락뿐인지 확인한다**

Run: `python3 tools/check_site.py`
Expected: FAIL — `privacy.html`, `terms.html` 링크 대상 누락 4건만 출력된다. 다른 오류(외부 참조, heading 건너뜀, lang 누락, 앵커 누락)가 하나라도 나오면 그것을 먼저 고친다.

- [ ] **Step 7: 커밋**

```bash
git add assets/style.css index.html 404.html tools/check_site.py
git commit -m "Add landing page, 404 page, and site checker"
```

---

### Task 3: 스크롤 리빌 스크립트

**Files:**
- Create: `assets/main.js`

**Interfaces:**
- Consumes: Task 2의 `.reveal` / `.js` / `.is-visible` CSS 계약
- Produces: `assets/main.js`. `index.html`만 로드한다. 법률 페이지와 404 페이지는 로드하지 않는다

- [ ] **Step 1: 스크립트를 작성한다**

`assets/main.js`:

```javascript
(function () {
  "use strict";

  var root = document.documentElement;
  var targets = document.querySelectorAll(".reveal");

  if (!targets.length) {
    return;
  }

  var reduced =
    window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Only claim the .js contract when we can actually reveal the elements again.
  if (reduced || !("IntersectionObserver" in window)) {
    return;
  }

  root.classList.add("js");

  var observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { rootMargin: "0px 0px -10% 0px" }
  );

  Array.prototype.forEach.call(targets, function (target) {
    observer.observe(target);
  });
})();
```

핵심은 `.js` 클래스를 **되돌릴 능력이 확인된 뒤에만** 붙이는 것이다. `IntersectionObserver`가 없거나 사용자가 모션 감소를 켠 브라우저에서는 클래스를 붙이지 않으므로 `.reveal` 요소가 숨겨진 채 남는 일이 없다.

- [ ] **Step 2: 스크립트가 없어도 내용이 보이는지 확인한다**

Run:
```bash
python3 - <<'PY'
import pathlib, re
css = pathlib.Path("assets/style.css").read_text(encoding="utf-8")
hidden = re.findall(r"([^{}]*)\{[^{}]*opacity:\s*0\b", css)
bad = [s.strip() for s in hidden if ".js" not in s]
print("selectors hiding content without .js:", bad)
assert not bad, bad
print("OK: content is only hidden under the .js class")
PY
```
Expected: PASS — `OK: content is only hidden under the .js class`

- [ ] **Step 3: 사이트 검증기를 실행한다**

Run: `python3 tools/check_site.py`
Expected: Task 2 Step 6과 동일하게 `privacy.html`·`terms.html` 링크 누락 4건만 출력

- [ ] **Step 4: 브라우저로 눈으로 확인한다**

```bash
python3 -m http.server 8000
```

`http://localhost:8000/` 에서 확인할 것:
1. About·Contact 섹션이 스크롤하면 페이드인된다
2. 네비의 `About`·`Contact`를 누르면 해당 섹션으로 부드럽게 이동한다
3. 개발자도구에서 JavaScript를 끄고 새로고침해도 About·Contact 본문이 보인다
4. 개발자도구 Rendering 패널에서 `prefers-reduced-motion: reduce`를 켜고 새로고침해도 본문이 보인다
5. 폭 360px에서 가로 스크롤이 생기지 않는다

- [ ] **Step 5: 커밋**

```bash
git add assets/main.js
git commit -m "Add scroll reveal that degrades safely without JS"
```

---

### Task 4: 방침·약관 페이지 이전

**Files:**
- Create: `tools/fixtures/blogger-privacy.html`
- Create: `tools/fixtures/blogger-terms.html`
- Create: `tools/extract_blogspot.py`
- Create: `tools/build_legal.py`
- Create: `tools/check_legal.py`
- Create: `privacy.html`
- Create: `terms.html`

**Interfaces:**
- Consumes: Task 2의 `nav` / `prose` / `footer` CSS 클래스와 `tools/check_site.py`
- Produces:
  - `tools/extract_blogspot.py`의 `extract(path) -> list[tuple[str, str]]` — `("h2" | "p" | "li", text)` 블록을 문서 순서로 반환. `tools/check_legal.py`가 이 함수와 `normalize(text) -> str`를 import 한다
  - `privacy.html`, `terms.html` — `<main class="prose">` 안에 본문이 들어간다

- [ ] **Step 1: Blogger 원문을 고정 파일로 내려받는다**

검증을 재현 가능하게 하려고 원본 HTML을 저장소에 넣는다. Blogger 페이지가 바뀌거나 사라져도 검증이 계속 동작한다.

```bash
mkdir -p tools/fixtures
curl -sSL https://dreamillow.blogspot.com/p/dreamillow-privacy-policy.html \
  -o tools/fixtures/blogger-privacy.html
curl -sSL https://dreamillow.blogspot.com/p/dreamillow-terms-of-service.html \
  -o tools/fixtures/blogger-terms.html
wc -c tools/fixtures/blogger-privacy.html tools/fixtures/blogger-terms.html
```

Expected: 각각 약 120KB, 114KB

- [ ] **Step 2: 추출기를 작성한다**

`tools/extract_blogspot.py`:

```python
"""Extract ordered content blocks from a saved Blogger page."""
import re
import sys
from html.parser import HTMLParser

BLOCK = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "div", "li"}
SKIP = {"script", "style", "svg", "button", "noscript", "form"}
HEADING = {"h1", "h2", "h3", "h4", "h5", "h6"}
CHROME = {"Share this post", "Get link", "Report Abuse", "Comments"}


def normalize(text):
    text = text.replace(" ", " ")
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
```

- [ ] **Step 3: 추출 결과를 눈으로 확인한다**

Run:
```bash
python3 tools/extract_blogspot.py tools/fixtures/blogger-privacy.html | head -8
python3 tools/extract_blogspot.py tools/fixtures/blogger-privacy.html | wc -l
python3 tools/extract_blogspot.py tools/fixtures/blogger-terms.html | wc -l
```

Expected:
- 첫 줄이 `[h2] Dreamillow Privacy Policy`
- 둘째 줄이 `[h2] Intro`
- 방침 74줄, 약관 79줄
- 공유 버튼·프로필 같은 Blogger UI 문구나 한국어가 섞여 나오지 않는다

- [ ] **Step 4: 일치 검증기를 작성한다**

`tools/check_legal.py`:

```python
"""Verify the generated legal pages carry the Blogger text verbatim."""
import difflib
import html
import pathlib
import re
import sys
from html.parser import HTMLParser

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from extract_blogspot import extract, normalize  # noqa: E402

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
    """Collect the text inside <main class="prose">."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.inside = False
        self.depth = 0
        self.text = []

    def handle_starttag(self, tag, attrs):
        if tag == "main" and "prose" in dict(attrs).get("class", ""):
            self.inside = True
            self.depth = 0
            return
        if self.inside and tag == "main":
            self.depth += 1

    def handle_endtag(self, tag):
        if self.inside and tag == "main":
            if self.depth == 0:
                self.inside = False
            else:
                self.depth -= 1

    def handle_data(self, data):
        if self.inside:
            self.text.append(data)


def prose_words(page):
    parser = ProseParser()
    parser.feed(pathlib.Path(page).read_text(encoding="utf-8"))
    return normalize(" ".join(parser.text).replace("\n", " ")).split()


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

    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        return 1
    print("OK: legal pages match the Blogger source")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

`ratio` 임계값 0.995와 "누락 덩어리 1개 이하"는 검증된 기준이다. 참조 텍스트는 태그 경계에서 단어가 갈라지는 아티팩트가 1건 생기는데(이메일 주소가 태그로 쪼개져 있다), 그것 하나까지만 허용한다.

- [ ] **Step 5: 검증기를 실행해 실패를 확인한다**

Run: `python3 tools/check_legal.py`
Expected: FAIL — `privacy.html does not exist`, `terms.html does not exist`, exit 1

- [ ] **Step 6: 페이지 생성기를 작성한다**

`tools/build_legal.py`:

```python
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
```

- [ ] **Step 7: 페이지를 생성한다**

Run: `python3 tools/build_legal.py`
Expected:
```
wrote privacy.html from 74 blocks
wrote terms.html from 79 blocks
```

- [ ] **Step 8: 일치 검증기를 실행해 통과를 확인한다**

Run: `python3 tools/check_legal.py`
Expected: PASS — 두 페이지 모두 ratio 0.995 이상, 마지막 줄 `OK: legal pages match the Blogger source`, exit 0

- [ ] **Step 9: 사이트 검증기가 이제 완전히 통과하는지 확인한다**

Run: `python3 tools/check_site.py`
Expected: PASS — `OK: 4 page(s) checked, no issues`, exit 0

Task 2 Step 6에서 남아 있던 링크 누락 4건이 사라져야 한다.

- [ ] **Step 10: 브라우저로 확인한다**

```bash
python3 -m http.server 8000
```

`http://localhost:8000/privacy.html` 과 `/terms.html` 에서 확인할 것:
1. 제목이 `<h1>`으로 한 번만 나오고 섹션 제목이 `<h2>`로 구분된다
2. 목록이 불릿으로 렌더링된다
3. 푸터의 상호 링크가 동작한다
4. 폭 360px에서 가로 스크롤이 생기지 않는다

- [ ] **Step 11: 커밋**

```bash
git add tools/fixtures tools/extract_blogspot.py tools/build_legal.py \
        tools/check_legal.py privacy.html terms.html
git commit -m "Migrate privacy policy and terms of service from Blogger"
```

---

### Task 5: 배포와 배포 후 검증

**Files:**
- Modify: 없음 (검증과 배포만)

**Interfaces:**
- Consumes: Task 1~4의 모든 산출물
- Produces: `https://dreamillow.github.io` 에서 동작하는 사이트

- [ ] **Step 1: 모든 검증기를 한 번에 돌린다**

Run:
```bash
python3 tools/check_app_ads.py && \
python3 tools/check_site.py && \
python3 tools/check_legal.py && \
echo "ALL CHECKS PASSED"
```
Expected: PASS — 마지막 줄 `ALL CHECKS PASSED`

하나라도 실패하면 여기서 멈추고 고친다.

- [ ] **Step 2: 작업 트리가 깨끗한지 확인한다**

Run: `git status --short`
Expected: 출력 없음

- [ ] **Step 3: 푸시한다**

```bash
git push -u origin main
```

저장소가 비어 있었으므로 이것이 첫 푸시다.

- [ ] **Step 4: GitHub Pages를 설정한다 (사용자 직접 수행)**

저장소 `Settings` → `Pages`:

| 항목 | 값 |
|---|---|
| Source | `Deploy from a branch` |
| Branch | `main` |
| Folder | `/ (root)` |
| Custom domain | 비워둠 |
| Enforce HTTPS | 켬 |

저장소가 `public`인지도 확인한다. `Save` 후 배포까지 1~2분 걸리며 `Actions` 탭의 `pages build and deployment`에서 진행을 볼 수 있다.

- [ ] **Step 5: 배포된 URL을 검증한다**

Run:
```bash
for path in / /privacy.html /terms.html /app-ads.txt /nope; do
  printf '%-16s ' "$path"
  curl -s -o /dev/null -w '%{http_code} %{content_type}\n' \
    "https://dreamillow.github.io$path"
done
```

Expected:
```
/                200 text/html; charset=utf-8
/privacy.html    200 text/html; charset=utf-8
/terms.html      200 text/html; charset=utf-8
/app-ads.txt     200 text/plain; charset=utf-8
/nope            404 text/html; charset=utf-8
```

`/app-ads.txt`가 `text/plain`이 아니거나 404면 `.nojekyll`이 커밋되었는지 확인한다.

- [ ] **Step 6: 배포된 app-ads.txt가 로컬과 동일한지 확인한다**

Run:
```bash
curl -sSL https://dreamillow.github.io/app-ads.txt | diff - app-ads.txt && \
  echo "app-ads.txt matches"
```
Expected: 차이 없음, `app-ads.txt matches`

- [ ] **Step 7: 사용자에게 인계 체크리스트를 보고한다**

구현 범위 밖이며 사용자가 직접 수행해야 한다. 이 목록을 그대로 전달한다:

1. 각 앱의 스토어 등록 정보에서 개인정보처리방침 URL을 `https://dreamillow.github.io/privacy.html`로 교체
2. 스토어 "개발자 웹사이트"를 `https://dreamillow.github.io`로 교체 — app-ads.txt 크롤링 기준이므로 필수
3. AdMob → 앱 → app-ads.txt에서 인식 여부 확인. 인식되지 않으면 커스텀 도메인 연결이 해결책이다
4. Blogger의 방침·약관 페이지에 새 URL 안내를 남기거나 정리

함께 보고할 것: 방침 원문의 `Information Collection` 항목에 있는 다음 문장은 수집 항목 예시 자리에 연락처 이메일이 들어가 있어 원문 오타로 보이며, 스펙에 따라 **수정하지 않고 그대로 이전**했다.

> "Your information is collected at the start of using our games and/or other Services, such as dreamillowgames@gmail.com."

- [ ] **Step 8: 커밋할 변경이 있으면 커밋한다**

이 태스크는 파일을 바꾸지 않는다. `git status --short`가 비어 있어야 한다.

---

## 자체 검토 결과

**스펙 커버리지**

| 스펙 요구사항 | 구현 태스크 |
|---|---|
| 단일 페이지 랜딩 (Hero/About/Contact/Footer) | Task 2 Step 4 |
| 방침 페이지 독립 URL | Task 4 |
| 약관 페이지 독립 URL | Task 4 |
| app-ads.txt, OWNERDOMAIN 제거 | Task 1 |
| `.nojekyll` | Task 1 Step 5 |
| 404 페이지 | Task 2 Step 5 |
| 법률 원문 무수정 이전 | Task 4 Step 4·8 (자동 검증) |
| 원문 오타 보고 | Task 5 Step 7 |
| 이메일 평문 + mailto | Task 2 Step 4 |
| 다크 단일 테마 | Task 2 Step 3 |
| 시스템 폰트, 외부 의존성 0개 | Task 2 Step 3·Step 1 (검증기가 강제) |
| 본문 최대 폭 720px | Task 2 Step 3 (`--measure`) |
| CSS 스무스 스크롤 | Task 2 Step 3 |
| `prefers-reduced-motion` 존중 | Task 3 Step 1·2 |
| heading 레벨 건너뛰지 않음 | Task 2 Step 1 (검증기가 강제) |
| 포커스 표시 유지 | Task 2 Step 3 (`:focus-visible`) |
| 로컬 서버 확인 | Task 3 Step 4, Task 4 Step 10 |
| 이전 정확성 diff | Task 4 Step 8 |
| 배포 후 URL·content-type 확인 | Task 5 Step 5 |
| AdMob 인식 확인 | Task 5 Step 7 |
| Pages 설정 | Task 5 Step 4 |
| 인계 체크리스트 | Task 5 Step 7 |

누락 없음.

**미해결 입력 1건**

Task 2 Step 4의 Hero 태그라인과 About 문구는 스펙의 초안 그대로다. 사용자가 다른 문구를 주면 `index.html`의 해당 두 섹션만 교체하면 되며 다른 태스크에 영향이 없다.
