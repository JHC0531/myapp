# 어휘 학습 앱 (시안: 가짜 리스트)

학생이 학번으로 들어와서 **영어 뜻풀이를 보고 단어 뱅크에서 단어를 고르고**, 🔊로 발음을 자유롭게 다시 들은 뒤 **정답을 한꺼번에 확인**하는 앱입니다. 수업 조건과 같은 구조예요.

## 폴더 구조

```
app.py                     Streamlit 런처 (로그인 → 집단 판별 → 차시 선택)
static/learn/index.html    학습 화면 (HTML)
data/sessions.csv          차시 목록: session_id, title, file, phase, app_group, page_size
data/groups.csv            반 → 집단(I/II)
data/wordlists/*.csv       단어 리스트: word, definition, type(unit/set)
supabase/schema.sql        기록 테이블 만들기
.streamlit/secrets.toml.example
```

## 리스트를 확정했을 때 바꿀 것

1. `data/wordlists/`에 진짜 리스트 CSV를 넣어요. 열 이름은 `word, definition, type`이에요.
2. `data/sessions.csv`에서 `file`과 `title`을 바꾸고, 차시 줄을 추가해요.
   - `app_group`: 그 차시를 앱으로 배우는 집단(I 또는 II)
   - `page_size`: 한 화면 문제 수. 비워 두면 한 화면에 전부 나와요. 30~40개 차시는 10 정도를 권장해요.
3. `data/groups.csv`에서 반별 집단을 실제 배정에 맞게 바꿔요.

코드는 고치지 않아도 돼요.

## 로그인 규칙

- 학번 5자리(예: 10312 = 1학년 3반 12번)에서 반을 읽어 집단을 정해요.
- 그 집단의 `app_group` 차시만 보여요.
- `teacher_code`(기본값 00000)로 들어가면 모든 차시를 미리 볼 수 있어요. 이때는 기록이 저장되지 않아요.

## Supabase 연결

1. Supabase에서 새 프로젝트를 만들어요.
2. SQL Editor에서 `supabase/schema.sql`을 실행해요.
3. Project Settings → API에서 Project URL과 anon public key를 복사해요.
4. 로컬에서는 `.streamlit/secrets.toml`을 만들고, Streamlit Cloud에서는 앱 Settings → Secrets에 넣어요. 형식은 `secrets.toml.example`을 보세요.

학생 앱은 기록을 **추가만** 할 수 있어요(RLS). 확인과 다운로드는 Supabase Table Editor에서 해요.

| 테이블 | 한 줄 = | 주요 열 |
|---|---|---|
| `item_responses` | 문항 1개 | 정답 여부, 최종·처음 선택, 바꾼 횟수, **정답 확인 전 듣기 횟수**, 화면 소요 시간 |
| `replay_after_check` | 정답 확인 뒤 다시 들은 단어 | 단어, 횟수 |
| `runs` | 차시 1회 완료 | 총 정답 수, 시작·끝 시각, 총 시간, 기기 정보 |

`word_type`(unit/set)으로 단원 단어와 실험 세트 단어를 나눠서 분석할 수 있어요.

## 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 참고

- 발음은 브라우저 TTS(en-US)라서 기기마다 목소리가 달라요. 실험에서 소리 조건을 통일하려면 나중에 mp3 파일로 바꾸는 걸 권장해요.
- 문제 순서와 단어 뱅크 순서는 학생마다 무작위예요. 화면에 나온 순서는 `item_no`에 기록돼요.
