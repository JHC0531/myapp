"""학생 등록·로그인

- Supabase 가 연결돼 있으면: 데이터베이스 함수(register_student / login_student)를 호출
  (비밀번호는 데이터베이스 안에서 암호화해서 저장, 학생 앱은 목록을 읽을 수 없음)
- 연결이 없으면(로컬 테스트): data/_local_students.json 에 저장
"""
import hashlib
import json
import re
from pathlib import Path

import requests

ID_RULE = re.compile(r"^[a-z0-9]{4,12}$")
PIN_RULE = re.compile(r"^\d{4}$")
LOCAL_FILE = Path(__file__).parent / "data" / "_local_students.json"


def check_format(user_id: str, pin: str):
    """형식이 틀리면 학생에게 보여 줄 안내 문장을, 맞으면 None 을 돌려줌."""
    if not ID_RULE.match(user_id):
        return "아이디는 영어 소문자와 숫자로 4~12자로 만들어 주세요. (이름은 쓰지 마세요)"
    if not PIN_RULE.match(pin):
        return "비밀번호는 숫자 4자리예요."
    return None


class Auth:
    def __init__(self, url: str = "", key: str = ""):
        self.url, self.key = url.rstrip("/"), key
        self.online = bool(url and key)

    # ---------- Supabase ----------
    def _rpc(self, fn, payload):
        r = requests.post(
            f"{self.url}/rest/v1/rpc/{fn}",
            headers={"apikey": self.key, "Authorization": f"Bearer {self.key}",
                     "Content-Type": "application/json"},
            json=payload, timeout=10,
        )
        r.raise_for_status()
        return r.json()

    # ---------- 로컬 테스트 ----------
    def _load(self):
        return json.loads(LOCAL_FILE.read_text(encoding="utf-8")) if LOCAL_FILE.exists() else {}

    def _save(self, d):
        LOCAL_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

    @staticmethod
    def _hash(user_id, pin):
        return hashlib.sha256(f"{user_id}:{pin}".encode()).hexdigest()

    # ---------- 공개 함수 ----------
    def register(self, user_id, cls, grp, pin):
        """성공하면 'ok', 아이디가 이미 있으면 'taken'."""
        if self.online:
            return self._rpc("register_student",
                             {"p_user_id": user_id, "p_class": int(cls), "p_grp": grp, "p_pin": pin})
        d = self._load()
        if user_id in d:
            return "taken"
        d[user_id] = {"class": int(cls), "grp": grp, "pin": self._hash(user_id, pin)}
        self._save(d)
        return "ok"

    def login(self, user_id, pin):
        """성공하면 {'class':..,'grp':..}, 실패하면 None."""
        if self.online:
            rows = self._rpc("login_student", {"p_user_id": user_id, "p_pin": pin})
            return rows[0] if rows else None
        s = self._load().get(user_id)
        if s and s["pin"] == self._hash(user_id, pin):
            return {"class": s["class"], "grp": s["grp"]}
        return None
