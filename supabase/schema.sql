-- Supabase SQL Editor 에 붙여 넣고 한 번 실행하세요.
-- 학생 앱(anon key)은 "추가"만 할 수 있고, 읽기·수정·삭제는 못 합니다.
-- 데이터는 Supabase 대시보드(Table Editor)에서 교사만 보고 CSV로 내려받습니다.

create table if not exists item_responses (
  id            bigint generated always as identity primary key,
  run_id        uuid        not null,          -- 한 번 학습한 기록 묶음
  student_id    text        not null,
  grp           text,                          -- 집단 I / II
  session_id    text        not null,          -- 예: fake-01
  page_no       int,
  item_no       int,                           -- 화면에 나온 순서
  word          text        not null,
  word_type     text,                          -- unit(단원 단어) / set(실험 세트 단어)
  chosen        text,                          -- 최종 선택
  first_choice  text,                          -- 처음 고른 단어
  n_changes     int,                           -- 바꾼 횟수
  is_correct    boolean,
  play_count    int,                           -- 정답 확인 전 들은 횟수
  page_seconds  int,
  created_at    timestamptz default now()
);

create table if not exists replay_after_check (
  id          bigint generated always as identity primary key,
  run_id      uuid not null,
  student_id  text not null,
  session_id  text not null,
  page_no     int,
  word        text not null,
  play_count  int,                             -- 정답 확인 뒤 다시 들은 횟수
  created_at  timestamptz default now()
);

create table if not exists runs (
  run_id         uuid primary key,
  student_id     text not null,
  grp            text,
  session_id     text not null,
  n_items        int,
  n_correct      int,
  started_at     timestamptz,
  finished_at    timestamptz,
  total_seconds  int,
  user_agent     text
);

alter table item_responses     enable row level security;
alter table replay_after_check enable row level security;
alter table runs               enable row level security;

create policy "anon insert" on item_responses     for insert to anon with check (true);
create policy "anon insert" on replay_after_check for insert to anon with check (true);
create policy "anon insert" on runs               for insert to anon with check (true);

-- ============================================================
-- 학생 등록·로그인
-- 학생 앱은 students 표를 직접 읽거나 쓸 수 없고,
-- 아래 두 함수만 부를 수 있어요. 비밀번호는 암호화(bcrypt)해서 저장돼요.
-- ============================================================
create extension if not exists pgcrypto with schema extensions;

create table if not exists students (
  user_id     text primary key,                -- 학생이 만든 아이디 (소문자)
  class       int  not null,                   -- 등록할 때 고른 반
  grp         text not null,                   -- 집단 I / II
  pin_hash    text not null,
  student_no  text,                            -- 교사가 나중에 학번을 적어 넣는 칸 (대응표)
  created_at  timestamptz default now()
);
alter table students enable row level security;   -- 정책 없음 = anon 은 접근 불가

create or replace function register_student(p_user_id text, p_class int, p_grp text, p_pin text)
returns text
language plpgsql security definer set search_path = public, extensions
as $$
begin
  if p_user_id !~ '^[a-z0-9]{4,12}$' or p_pin !~ '^\d{4}$' or p_grp not in ('I','II') then
    raise exception 'invalid input';
  end if;
  insert into students(user_id, class, grp, pin_hash)
  values (p_user_id, p_class, p_grp, crypt(p_pin, gen_salt('bf')));
  return 'ok';
exception when unique_violation then
  return 'taken';
end $$;

create or replace function login_student(p_user_id text, p_pin text)
returns table(class int, grp text)
language sql security definer set search_path = public, extensions
as $$
  select s.class, s.grp from students s
  where s.user_id = p_user_id and s.pin_hash = crypt(p_pin, s.pin_hash);
$$;

revoke all on function register_student(text,int,text,text) from public;
revoke all on function login_student(text,text) from public;
grant execute on function register_student(text,int,text,text) to anon;
grant execute on function login_student(text,text) to anon;

-- 비밀번호를 잊은 학생: Table Editor 에서 그 줄을 지우고 다시 등록하게 하거나,
-- SQL Editor 에서 새 비밀번호로 바꿔 주세요.
--   update students set pin_hash = crypt('1234', gen_salt('bf')) where user_id = '아이디';
