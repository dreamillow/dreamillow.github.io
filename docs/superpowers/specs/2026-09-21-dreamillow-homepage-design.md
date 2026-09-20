# Dreamillow 홈페이지 설계

작성일: 2026-09-21

## 배경

`dreamillow.github.io` 저장소는 비어 있다. Dreamillow는 광고(AdMob, ironSource/LevelPlay, Vungle)와 인앱 결제를 붙인 모바일 게임을 스토어에 배포하고 있고, 현재 개인정보처리방침·이용약관·app-ads.txt를 모두 Blogger(`dreamillow.blogspot.com`)에 두고 있다.

이 사이트의 목적은 **스토어와 광고 네트워크 심사가 요구하는 URL을 직접 통제하는 도메인에서 안정적으로 제공하는 것**이다. 마케팅 사이트가 아니다. 이 판단이 아래 모든 기술 선택의 근거다.

## 범위

**포함**

- 단일 페이지 랜딩 (`index.html`)
- 개인정보처리방침 페이지 — Blogger 원문 이전
- 이용약관 페이지 — Blogger 원문 이전
- `app-ads.txt` — Blogger 파일에서 `OWNERDOMAIN` 줄 제거
- GitHub Pages 배포 설정

**제외**

- 앱 목록/포트폴리오 섹션
- 다국어 — 영어 단일
- 서버 기능 일체. 문의는 `mailto:`로 처리한다
- 빌드 도구, 패키지 매니저, CI 워크플로
- Blogger 페이지 정리와 스토어 등록 URL 교체 (사용자 직접 수행, 마지막 체크리스트로 안내)

## 결정과 근거

### 정적 HTML, 빌드 없음

페이지 3개에 빌드 파이프라인을 두면 얻는 것보다 깨질 것이 많다. 파일을 브라우저로 열면 그것이 최종 결과물이다. Jekyll은 페이지가 10개를 넘어 헤더·푸터 중복이 실제 비용이 될 때 검토한다.

### 랜딩은 단일 페이지, 법률 문서는 별도 페이지

랜딩은 앵커로 이동하는 원페이지로 만든다. 반면 방침·약관은 `#privacy` 앵커가 아니라 독립 URL을 갖는다:

- 스토어 심사자가 마케팅 섹션 사이에 끼인 앵커를 "방침 페이지"로 인정하지 않을 위험이 있다
- 두 문서는 각각 2만 자가 넘는 법률 텍스트라 원페이지의 흐름과 맞지 않는다

### app-ads.txt: Blogger 파일에서 OWNERDOMAIN만 제거

Blogger가 제공하던 파일은 `ads.txt`와 바이트 단위로 동일한 128줄이며, 첫 줄이 `OWNERDOMAIN=blogger.com`이다. 이 줄은 인벤토리 소유 도메인을 blogger.com으로 선언하므로 새 도메인에서는 검증을 실패시킬 수 있다. 제거한다.

나머지 127줄(`DIRECT` 3줄 + `RESELLER` 124줄)은 그대로 유지한다. 이 목록이 실제 앱 인벤토리와 일치하는지는 AdMob 콘솔이 최종 근거이며, 배포 후 AdMob의 app-ads.txt 상태로 검증한다.

`DIRECT` 3줄:

```
ironsrc.com, 631887, DIRECT
vungle.com, 6aab47ebadbd10019b9a09cd, DIRECT, c107d686becd2d77
google.com, pub-8558658162311217, DIRECT, f08c47fec0942fa0
```

### 법률 문서 원문 보존

방침·약관 본문은 한 글자도 바꾸지 않는다. 법률 효력이 있는 문서이므로 문구 개선은 설계자가 임의로 판단할 영역이 아니다. Blogger HTML에서 본문을 추출해 시맨틱 HTML(`<h2>`, `<p>`, `<ul>`)로 재구성하는 것까지가 작업 범위다.

원문에서 발견된 이상 1건은 고치지 않고 이전한 뒤 사용자에게 보고한다:

> `Information Collection` 항목의 "Your information is collected at the start of using our games and/or other Services, such as dreamillowgames@gmail.com." — 수집 항목 예시 자리에 연락처 이메일이 들어가 있어 원문 오타로 보인다.

### 이메일 난독화하지 않음

`dreamillowgames@gmail.com`은 이미 Blogger 두 페이지에 평문으로 공개되어 있다. 새 사이트에서만 난독화해도 수집을 막지 못하므로 복잡도만 늘린다. 평문으로 표기하고 `mailto:` 링크를 건다.

## 파일 구조

```
/
├── index.html          단일 페이지: Hero → About → Contact
├── privacy.html        Blogger 원문 이전
├── terms.html          Blogger 원문 이전
├── app-ads.txt         127줄
├── 404.html
├── .nojekyll           Jekyll 처리 비활성화
├── assets/
│   ├── style.css
│   └── main.js         스크롤 리빌 전용
└── docs/superpowers/specs/
```

`.nojekyll`은 GitHub Pages가 파일을 Jekyll로 처리하지 않고 그대로 서빙하도록 보장한다. `app-ads.txt`가 손상 없이 평문으로 전달되어야 하므로 필요하다.

## index.html 구성

| 순서 | 섹션 | 내용 |
|---|---|---|
| 1 | 상단 고정 네비 | `Dreamillow` 워드마크, `About` · `Contact` 앵커 |
| 2 | Hero | 스튜디오명 + 한 줄 태그라인 |
| 3 | About | 스튜디오 소개 2~3문장 |
| 4 | Contact | 이메일 평문 표기 + `mailto:` 버튼 |
| 5 | Footer | © Dreamillow, `Privacy Policy` · `Terms of Service` 링크 |

`privacy.html`과 `terms.html`은 동일한 네비·푸터를 쓰되 네비의 앵커 링크는 `index.html#about` 형태의 절대 경로로 둔다.

### 본문 초안 (검토 필요)

사용자 확인 후 확정한다. 검증 불가능한 주장(팀 규모, 수상 이력, 출시작 수)은 넣지 않았다.

**Hero 태그라인**

> An independent game studio.

**About**

> Dreamillow is an independent game studio developing mobile games.
>
> We publish our titles on Google Play and the App Store for players around the world.

**Contact**

> Questions about our games, or about this site? Write to us.
>
> dreamillowgames@gmail.com

## 스타일과 기술 제약

- **테마**: 다크 단일. 라이트 모드 대응은 하지 않는다 — 방문자 대부분이 심사자·크롤러이고, 두 테마를 유지할 이유가 없다
- **폰트**: 시스템 폰트 스택. 외부 폰트를 불러오지 않는다 (요청 0건, 렌더 차단 없음)
- **레이아웃**: 모바일 우선 단일 컬럼. 본문 최대 폭 `720px`
- **앵커 이동**: CSS `scroll-behavior: smooth`만 사용. JS 불필요
- **main.js**: `IntersectionObserver` 기반 페이드인만 담당. `prefers-reduced-motion: reduce`이면 동작하지 않는다. `index.html`에서만 로드하고 법률 페이지는 로드하지 않는다
- **접근성**: heading 레벨을 건너뛰지 않는다. 포커스 표시를 제거하지 않는다. 본문 대비 4.5:1 이상
- **외부 의존성 0개**: CDN, 분석 스크립트, 폰트, 아이콘 라이브러리 전부 사용하지 않는다

## 검증

**로컬**

1. `python3 -m http.server`로 띄운다
2. 내부 링크·앵커가 전부 목적지에 도달하는지 확인
3. 뷰포트 폭 360px에서 가로 스크롤이 생기지 않는지 확인
4. `prefers-reduced-motion`을 켠 상태에서 모든 콘텐츠가 보이는지 확인 — 페이드인이 꺼졌을 때 요소가 투명한 채 남으면 안 된다

**콘텐츠 이전 정확성**

5. 추출한 방침·약관 평문을 Blogger 원문 평문과 `diff`로 비교해 공백 외 차이가 없음을 확인
6. `app-ads.txt`가 127줄이고 `OWNERDOMAIN`이 없으며 `DIRECT` 3줄이 그대로인지 확인

**배포 후**

7. `/`, `/privacy.html`, `/terms.html`, `/app-ads.txt` 네 URL이 200으로 응답하는지 `curl`로 확인
8. `/app-ads.txt`의 `content-type`이 `text/plain`인지 확인
9. AdMob 콘솔에서 app-ads.txt가 인식되는지 확인 — 실패 시 커스텀 도메인 연결이 해결책이다

## 배포 설정

GitHub `Settings` → `Pages`:

- Source: `Deploy from a branch`
- Branch: `main` / `/ (root)`
- Enforce HTTPS: 켬
- Custom domain: 비워둠

저장소는 public이어야 한다.

## 이후 사용자가 직접 할 일

설계 범위 밖이며, 배포가 확인된 뒤 체크리스트로 안내한다.

1. 각 앱의 스토어 등록 정보에서 개인정보처리방침 URL을 `https://dreamillow.github.io/privacy.html`로 교체
2. 스토어 "개발자 웹사이트"를 `https://dreamillow.github.io`로 교체 — app-ads.txt 크롤링의 기준이 되므로 필수
3. AdMob에서 app-ads.txt 인식 확인
4. Blogger 두 페이지에 새 URL 안내를 남기거나 정리

## 알려진 리스크

**app-ads.txt 크롤링** — `github.io`는 공개 접미사 목록에 있어 `dreamillow.github.io`가 등록 가능 도메인으로 취급되며 일반적으로 정상 동작한다. 다만 광고 네트워크 크롤러 동작을 보장할 수는 없다. 인식 실패 시 커스텀 도메인 연결이 확실한 해결책이다.

**RESELLER 목록의 정확성** — 127줄이 실제 앱 인벤토리와 일치하는지는 확인되지 않았다. AdMob 콘솔 내용과 다르면 그쪽을 따른다.
