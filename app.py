"""어휘 학습 앱 런처 (Streamlit)

- 처음엔 반·아이디·비밀번호(숫자 4자리)로 등록, 다음부터 아이디·비밀번호로 로그인
- 등록할 때 고른 반으로 집단(I/II) 결정 → 그 집단이 앱으로 배우는 차시만 보여 줌
- 차시를 고르면 static/learn/index.html 학습 화면을 띄움
- 단어 리스트는 data/wordlists/*.csv, 차시 구성은 data/sessions.csv 만 바꾸면 됨
"""
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from auth import Auth, check_format

ROOT = Path(__file__).parent
DATA = ROOT / "data"


def secret(key, default):
    try:
        return st.secrets.get(key, default)
    except Exception:  # secrets.toml 이 없을 때 (로컬 테스트)
        return default


# 교사 미리보기 계정 (모든 차시가 보이고 기록은 저장 안 됨) — secrets 에서 꼭 바꾸세요
TEACHER_ID = str(secret("teacher_id", "teacher")).lower()
TEACHER_PIN = str(secret("teacher_pin", "0000"))

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


sb = secret("supabase", {})
auth = Auth(sb.get("url", ""), sb.get("anon_key", ""))


def enter(user_id, grp):
    st.session_state.sid, st.session_state.grp = user_id, grp
    st.rerun()


# ---------------- 로그인 / 처음 등록 ----------------
if "sid" not in st.session_state:
    st.title("📘 단어 학습")
    if not auth.online:
        st.caption("⚙️ 테스트 모드: Supabase 가 연결되지 않아 이 컴퓨터에만 저장돼요.")
    tab_login, tab_join = st.tabs(["로그인", "처음 왔어요 (등록)"])

    with tab_login:
        with st.form("login"):
            uid = st.text_input("아이디").strip().lower()
            pin = st.text_input("비밀번호 (숫자 4자리)", type="password", max_chars=4).strip()
            go = st.form_submit_button("시작하기", type="primary")
        if go:
            if uid == TEACHER_ID and pin == TEACHER_PIN:
                enter(uid, "T")
            try:
                me = auth.login(uid, pin) if uid and pin else None
            except Exception:
                st.error("연결에 문제가 있어요. 잠시 뒤에 다시 해 보세요.")
                st.stop()
            if me:
                enter(uid, me["grp"])
            st.error("아이디나 비밀번호가 맞지 않아요. 잊어버렸으면 선생님께 말해 주세요.")

    with tab_join:
        st.write("처음 한 번만 등록해요. **아이디와 비밀번호를 꼭 기억하세요!**")
        classes = list(load_groups().keys())
        with st.form("join"):
            cls = st.selectbox("반", classes, format_func=lambda c: f"{c}반", index=None,
                               placeholder="반을 고르세요")
            uid = st.text_input("만들 아이디 (영어 소문자·숫자 4~12자, 이름은 쓰지 마세요)").strip().lower()
            pin = st.text_input("비밀번호 (숫자 4자리)", type="password", max_chars=4).strip()
            pin2 = st.text_input("비밀번호 한 번 더", type="password", max_chars=4).strip()
            go = st.form_submit_button("등록하기", type="primary")
        if go:
            msg = "반을 골라 주세요." if cls is None else check_format(uid, pin)
            if not msg and pin != pin2:
                msg = "비밀번호 두 개가 달라요."
            if not msg and uid == TEACHER_ID:
                msg = "다른 아이디를 써 주세요."
            if msg:
                st.error(msg)
                st.stop()
            grp = load_groups()[cls]
            try:
                res = auth.register(uid, cls, grp, pin)
            except Exception:
                st.error("연결에 문제가 있어요. 잠시 뒤에 다시 해 보세요.")
                st.stop()
            if res == "taken":
                st.error("이미 누가 쓰는 아이디예요. 다른 아이디를 만들어 주세요.")
            else:
                st.session_state.flash = f"등록 완료! 내 아이디는 **{uid}** 예요. 학습지에 적어 두세요."
                enter(uid, grp)
    st.stop()

sid, grp = st.session_state.sid, st.session_state.grp
if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

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
