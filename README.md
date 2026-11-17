# 어휘 학습 앱 (시안: 가짜 리스트)

학생이 직접 만든 아이디로 들어와서 **영어 뜻풀이를 보고 단어 뱅크에서 단어를 고르고**, 🔊로 발음을 자유롭게 다시 들은 뒤 **정답을 한꺼번에 확인**하는 앱입니다. 수업 조건과 같은 구조예요.

## 폴더 구조

```
app.py                     Streamlit 런처 (등록·로그인 → 집단 판별 → 차시 선택)
auth.py                    학생 등록·로그인 (Supabase 함수 호출)
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

- **처음 한 번 등록:** 반을 고르고, 아이디(영어 소문자·숫자 4~12자, 실명 금지)와 비밀번호(숫자 4자리)를 만들어요. 중복 아이디는 막혀요.
- **다음부터 로그인:** 아이디와 비밀번호만 입력해요. 대문자로 쳐도 소문자로 바뀌어요.
- 등록할 때 고른 반으로 집단(I/II)이 정해지고, 그 집단의 `app_group` 차시만 보여요.
- **교사 미리보기:** `teacher_id` / `teacher_pin`(기본값 teacher / 0000)으로 들어가면 모든 차시가 보이고 기록은 저장되지 않아요. secrets에서 꼭 바꾸세요.
- **학번 대응표:** Supabase `students` 테이블의 `student_no` 칸에 교사가 학번을 적어 넣으면, 사전·사후 검사와 연결할 수 있어요. 첫 시간에 학생들이 아이디를 종이에 적어 내게 하면 편해요.
- **비밀번호를 잊은 학생:** `supabase/schema.sql` 맨 아래 주석에 있는 SQL 한 줄로 바꿔 줄 수 있어요.
- Supabase가 연결되지 않은 로컬 테스트에서는 등록 정보가 `data/_local_students.json`에 저장돼요. 이 파일은 GitHub에 올라가지 않아요.

## Supabase 연결

1. Supabase에서 새 프로젝트를 만들어요.
2. SQL Editor에서 `supabase/schema.sql`을 실행해요.
3. Project Settings → API에서 Project URL과 anon public key를 복사해요.
4. 로컬에서는 `.streamlit/secrets.toml`을 만들고, Streamlit Cloud에서는 앱 Settings → Secrets에 넣어요. 형식은 `secrets.toml.example`을 보세요.

학생 앱은 기록을 **추가만** 할 수 있고, `students` 표는 읽을 수 없어요(RLS와 등록·로그인 함수로만 접근). 확인과 다운로드는 Supabase Table Editor에서 해요.

| 테이블 | 한 줄 = | 주요 열 |
|---|---|---|
| `students` | 학생 1명 | 아이디, 반, 집단, 암호화된 비밀번호, 학번(교사 입력) |
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
