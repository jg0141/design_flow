# Design Flow

비밀번호로 여는 Physical Implementation 학습 마인드맵. GitHub Pages로 배포하는 정적 사이트이며 특정 AI 서비스에 묶여 있지 않습니다.

## 파일 구성

| 파일 | 역할 |
|---|---|
| `index.html` | 화면·편집기 전체 (HTML/CSS/JS 한 파일, 외부 의존성 없음). 내용은 들어 있지 않음 |
| `data.json` | 마인드맵 내용. 비밀번호로 암호화되어 있음 |
| `tools/crypt.py` | `data.json` 복호화/암호화 도구 (다른 도구·AI로 내용을 고칠 때 사용) |
| `.nojekyll` | GitHub Pages가 파일을 그대로 서비스하도록 하는 설정 |

## 보는 사람

사이트 주소를 열고 비밀번호 입력 → 보기 전용. 카드 클릭 = 내용 보기, 더블클릭 = 하위 항목 접기/펼치기.

## 편집 (사이트에서)

1. 사이트 상단 `편집 모드` → 저장소(`owner/repo`)와 GitHub 토큰 입력
2. 수정 후 `변경사항 게시` → `data.json`이 새 커밋으로 갱신 → 1~2분 뒤 사이트 반영
3. `편집 종료`로 브라우저에 저장된 토큰 삭제

토큰: GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens** →
Repository access: 이 저장소만 / Permissions: **Contents: Read and write**. 토큰은 브라우저에만 저장되고 저장소 파일에는 들어가지 않습니다.

## 편집 (다른 도구·AI로)

```bash
pip install cryptography
python tools/crypt.py decrypt data.json plain.json   # 비밀번호 입력
# plain.json 수정 (아래 구조 참고) — plain.json은 절대 커밋하지 않기 (.gitignore 처리됨)
python tools/crypt.py encrypt plain.json data.json
git add data.json && git commit -m "Update content" && git push
```

화면·기능을 바꿀 때는 `index.html`만 수정하면 됩니다 (내용과 분리되어 있음).

### 내용 구조 (`plain.json`)

```
{ "root": Node, "links": [ {id, from, to, label, color, dash, arrow, shape} ], "version": 2 }
Node = {
  id, title, memo, status ("" | 예정 | 진행 중 | 완료 | 보류), color ("#rrggbb", 선택),
  collapsed (bool: 처음 화면에서 접힘), children: [Node],
  images: [ {id, name, caption, src: "data:image/..."} ],
  record: { goal, action, evidence, outcome, learning },   // 작업 근거 · 지원서 기록
  edge: { shape, dash, arrow, color, width, label, hidden } // 상위 연결선 모양
}
```
카드 위치(x, y)는 저장하지 않아도 됩니다. 없으면 열 때 원형으로 자동 배치됩니다.

## 암호화 형식

`data.json` = `{v, iter, salt, iv, ct}` (base64) ·
key = PBKDF2-HMAC-SHA256(password, salt, iter=250000) · ct = AES-256-GCM(gzip(JSON))

## 보안 메모

- 저장소가 공개여도 내용은 비밀번호 없이는 읽을 수 없습니다. 강도는 비밀번호 길이·복잡도에 달려 있습니다.
- 비밀번호를 바꿔도 git 기록에 남은 예전 `data.json`은 예전 비밀번호로 열립니다. 예전 비밀번호가 노출됐다면 저장소를 새로 만들어 최신 `data.json`만 올리세요.
