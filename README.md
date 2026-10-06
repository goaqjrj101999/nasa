# Naver Blog → Google Index Hub

네이버 블로그 RSS를 주기적으로 읽어 **GitHub Pages에 공개 인덱스/아카이브를 생성**하고, 각 글을 네이버 원문으로 정상 `<a href>` 링크하는 템플릿입니다.

이 템플릿은 네이버 URL을 자신의 `sitemap.xml`에 억지로 넣지 않습니다. 사이트맵에는 **본인이 소유한 GitHub Pages URL만** 넣고, Googlebot이 그 페이지에서 네이버 원문 링크를 발견하도록 구성합니다.

> 중요: 이 도구는 Google 색인을 보장하거나 강제하지 않습니다. Googlebot이 네이버 게시글을 발견할 수 있는 정상적인 링크 경로를 만드는 도구입니다.

## 1. 준비

1. GitHub에서 새 Public repository를 만듭니다. 예: `naver-google-index-hub`
2. 이 폴더의 모든 파일을 repository에 업로드합니다.
3. `config.json`을 수정합니다.

예시:

```json
{
  "blog_id": "my_naver_id",
  "site_title": "내 네이버 블로그 글 모음",
  "site_description": "최신 글을 주제별로 확인할 수 있는 공개 아카이브입니다.",
  "site_url": "https://GITHUB_ID.github.io/naver-google-index-hub/",
  "max_posts": 30,
  "excerpt_chars": 260,
  "google_site_verification": ""
}
```

### `site_url` 주의

Repository 이름이 `naver-google-index-hub`이면 일반적인 프로젝트 Pages URL은 다음 형태입니다.

```text
https://GITHUB_ID.github.io/naver-google-index-hub/
```

개인 도메인을 연결했다면 그 주소를 넣습니다. 반드시 마지막 `/`까지 넣는 것을 권장합니다.

## 2. GitHub Pages 활성화

GitHub repository에서:

1. **Settings**
2. **Pages**
3. **Build and deployment**
4. **Source → GitHub Actions** 선택

이후 `main` 브랜치에 push하면 자동 빌드/배포됩니다.

워크플로는 기본적으로 6시간마다 RSS를 다시 확인합니다. 필요하면 `.github/workflows/pages.yml`의 `cron`을 변경하세요.

## 3. Google Search Console 연결

### 방법 A — URL-prefix 속성 + HTML meta 태그

1. Search Console에서 GitHub Pages 사이트 URL을 URL-prefix 속성으로 추가합니다.
2. 인증 방식에서 **HTML 태그**를 선택합니다.
3. Google이 주는 태그가 예를 들어 아래와 같다면:

```html
<meta name="google-site-verification" content="abc123XYZ">
```

`config.json`에는 **content 값만** 넣습니다.

```json
"google_site_verification": "abc123XYZ"
```

4. GitHub에 commit/push합니다.
5. Pages 배포 후 Search Console에서 확인합니다.

### 방법 B — 개인 도메인 + DNS 인증

개인 도메인을 쓴다면 Search Console의 Domain property + DNS TXT 인증이 가장 깔끔합니다.

## 4. Sitemap 제출

배포 후 다음 URL을 엽니다.

```text
https://GITHUB_ID.github.io/naver-google-index-hub/sitemap.xml
```

Search Console → **Sitemaps**에 `sitemap.xml`을 제출합니다.

사이트맵에는 네이버 글 URL이 아니라 다음과 같이 본인 Pages URL만 들어갑니다.

- `/`
- `/archive.html`

이 두 페이지에서 네이버 원문으로 크롤링 가능한 일반 링크가 제공됩니다.

## 5. 네이버 블로그 설정

네이버 글은 최소한 다음 조건을 권장합니다.

- 전체 공개
- 검색 허용 ON
- RSS 전략을 사용할 경우 외부 보내기 허용 권장

RSS 주소는 다음 형식입니다.

```text
https://rss.blog.naver.com/블로그아이디.xml
```

## 6. 생성되는 파일

GitHub Actions 실행 시 `_site/`에 다음이 생성됩니다.

- `index.html` — 최신 게시글 링크
- `archive.html` — RSS에서 읽은 전체 게시글 링크
- `sitemap.xml` — 본인 GitHub Pages URL만 포함
- `robots.txt` — sitemap 위치 안내
- `status.json` — 마지막 생성 시각/글 개수 확인용
- `.nojekyll` — Jekyll 처리 없이 정적 파일 배포

## 7. 수동 실행

GitHub repository → **Actions** → `Build and Deploy Naver Index Hub` → **Run workflow**.

로컬에서는 Python 3.11+ 환경에서:

```bash
python build.py
```

실행 후 `_site/index.html`을 열어 확인합니다.

## 8. SEO 관련 주의사항

이 템플릿은 다음을 하지 않습니다.

- Google Indexing API를 일반 블로그 글에 오용하지 않음
- 네이버 URL을 소유권 없는 cross-site sitemap에 직접 삽입하지 않음
- 자동 댓글/대량 백링크/숨김 링크를 만들지 않음
- 네이버 글 전체를 복제하지 않음

RSS의 짧은 설명만 보여주고 원문으로 직접 연결하도록 기본 설계했습니다. Google 노출은 크롤링 가능성, 네이버의 접근 허용, 문서 품질, 중복성, 검색 의도 등 여러 요소에 의해 결정되므로 색인을 보장할 수 없습니다.

## 문제 해결

### Actions에서 `blog_id` 오류
`config.json`의 `YOUR_NAVER_BLOG_ID`를 실제 ID로 바꿉니다.

### `site_url` 오류
`YOUR_GITHUB_USERNAME`이 남아 있으면 빌드가 중단됩니다. 실제 Pages URL로 바꿉니다.

### RSS 426 또는 접속 오류
HTTPS RSS 주소를 사용해야 하며 오래된 HTTP/1.0 방식은 사용하지 않습니다. 이 템플릿은 Python의 현대 HTTP 클라이언트로 HTTPS 요청합니다.

### 새 글이 바로 안 나타남
GitHub Actions 예약 실행은 정확한 분 단위 실행을 보장하지 않습니다. Actions에서 수동 실행하면 즉시 다시 빌드할 수 있습니다.
