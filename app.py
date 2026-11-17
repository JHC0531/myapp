"""어휘 학습 앱 런처 (Streamlit)

- 학번으로 로그인 → 반으로 집단(I/II) 결정 → 그 집단이 앱으로 배우는 차시만 보여 줌
- 차시를 고르면 static/learn/index.html 학습 화면을 띄움
- 단어 리스트는 data/wordlists/*.csv, 차시 구성은 data/sessions.csv 만 바꾸면 됨
"""
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).parent
DATA = ROOT / "data"
def secret(key, default):
    try:
        return st.secrets.get(key, default)
    except Exception:  # secrets.toml 이 없을 때 (로컬 테스트)
        return default


TEACHER_CODE = secret("teacher_code", "00000")  # 교사 미리보기용 학번

st.set_page_config(page_title="단어 학습", page_icon="📘", layout="centered")


@st.cache_data
def load_sessions():
    return pd.read_csv(DATA / "sessions.csv", encoding="utf-8-sig", dtype=str)


@st.cache_data
def load_groups():
    g = pd.read_csv(DATA / "groups.csv", encoding="utf-8-sig", dtype=str)
    return dict(zip(g["class"], g["group"]))


@st.cache_data
def load_words(file):
    df = pd.read_csv(DATA / "wordlists" / file, encoding="utf-8-sig", dtype=str).fillna("")
    return df[["word", "definition", "type"]].to_dict("records")


# HTML 학습 화면을 Streamlit 컴포넌트로 등록 (화면 높이가 내용에 맞게 자동 조절됨)
learn_screen = components.declare_component("learn_screen", path=str(ROOT / "static" / "learn"))


def group_of(student_id: str):
    """학번 1반번호 형식(예: 10312 = 1학년 3반 12번)에서 반을 읽어 집단을 찾음."""
    if student_id == TEACHER_CODE:
        return "T"
    if len(student_id) != 5 or not student_id.isdigit():
        return None
    return load_groups().get(str(int(student_id[1:3])))


# ---------------- 로그인 ----------------
if "sid" not in st.session_state:
    st.title("📘 단어 학습")
    sid = st.text_input("학번 5자리를 입력하세요 (예: 10312)", max_chars=5)
    if st.button("시작하기", type="primary"):
        grp = group_of(sid.strip())
        if grp is None:
            st.error("학번을 다시 확인해 주세요.")
        else:
            st.session_state.sid, st.session_state.grp = sid.strip(), grp
            st.rerun()
    st.stop()

sid, grp = st.session_state.sid, st.session_state.grp

# ---------------- 차시 선택 ----------------
sessions = load_sessions()
mine = sessions if grp == "T" else sessions[sessions["app_group"] == grp]

with st.sidebar:
    st.write(f"**{sid}**" + (" (교사 미리보기)" if grp == "T" else ""))
    if st.button("로그아웃"):
        st.session_state.clear()
        st.rerun()

if mine.empty:
    st.info("지금은 앱으로 학습하는 차시가 없어요. 수업 시간에 선생님과 함께 공부해요!")
    st.stop()

labels = mine["title"].tolist()
choice = st.selectbox("오늘 학습할 차시", labels, index=len(labels) - 1)
row = mine[mine["title"] == choice].iloc[0]

sb = secret("supabase", {})
config = {
    "student_id": sid if grp != "T" else f"T-{sid}",
    "group": grp,
    "session_id": row["session_id"],
    "session_title": row["title"],
    "page_size": int(row.get("page_size") or 0) or None,
    "words": load_words(row["file"]),
    # 교사 미리보기는 저장하지 않음
    "supabase": {} if grp == "T" else {"url": sb.get("url", ""), "key": sb.get("anon_key", "")},
}

# key 에 차시를 넣어서 차시를 바꾸면 새 화면으로 시작
learn_screen(config=config, key=f"learn-{row['session_id']}")
