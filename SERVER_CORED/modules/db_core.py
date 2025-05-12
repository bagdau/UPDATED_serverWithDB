
import asyncio, sqlite3, bcrypt, secrets, datetime, shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Literal, Optional

MAX_FAILED = 5
TOKEN_LIFETIME = datetime.timedelta(minutes=30)

_QUEUE: 'asyncio.Queue[Task]' = asyncio.Queue()

def get_queue() -> asyncio.Queue:
    return _QUEUE

@dataclass
class Task:
    op: Literal["add", "get", "del", "set_role", "upd_pwd",
                "upd_contacts", "check", "auth", "backup",
                "confirm_email", "confirm_phone",
                "request_pwd_reset", "reset_password",
                "unblock", "restore_user"]
    payload: Dict[str, Any]
    fut: asyncio.Future

class DBProducer:
    def __init__(self):
        self._q = _QUEUE
        self._loop = asyncio.get_running_loop()

    async def _call(self, op: str, **kw):
        fut = self._loop.create_future()
        await self._q.put(Task(op, kw, fut))
        return await fut

    async def add_user(self, login: str, password: str, full_name: str,
                       phone: str, role: str = "", iin: str = ""):
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        return await self._call("add", login=login, pwd=pw_hash,
                                full_name=full_name, phone=phone,
                                role=role, iin=iin)

    async def get_user(self, login: str):
        return await self._call("get", login=login)

    async def del_user(self, login: str):
        return await self._call("del", login=login)

    async def restore_user(self, login: str):
        return await self._call("restore_user", login=login)

    async def set_role(self, login: str, role: str):
        return await self._call("set_role", login=login, role=role)

    async def update_password(self, login: str, new_password: str):
        pw_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        return await self._call("upd_pwd", login=login, pwd=pw_hash)

    async def update_contacts(self, login: str, *,
                              phone: Optional[str] = None,
                              iin: Optional[str] = None,
                              full_name: Optional[str] = None):
        return await self._call("upd_contacts", login=login,
                                phone=phone, iin=iin, full_name=full_name)

    async def check_free(self, *, login=None, phone=None, iin=None):
        return await self._call("check", login=login, phone=phone, iin=iin)

    async def auth(self, login: str, password: str):
        return await self._call("auth", login=login, password=password)

    async def confirm_email(self, login: str):
        return await self._call("confirm_email", login=login)

    async def confirm_phone(self, login: str):
        return await self._call("confirm_phone", login=login)

    async def request_pwd_reset(self, login: str):
        return await self._call("request_pwd_reset", login=login)

    async def reset_password(self, token: str, new_password: str):
        pw_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        return await self._call("reset_password", token=token, pwd=pw_hash)

    async def unblock(self, login: str):
        return await self._call("unblock", login=login)

    async def backup(self, note: str = ""):
        return await self._call("backup", note=note)

class DBWorker:
    def __init__(self, db_path="users.db", backup_dir="backups"):
        self._q = _QUEUE
        self._db_path = Path(db_path)
        self._backup_dir = Path(backup_dir)

    def _sync_open(self):
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""CREATE TABLE IF NOT EXISTS users(
            ALTER TABLE users ADD COLUMN is_deleted INTEGER DEFAULT 0;
            login TEXT PRIMARY KEY,
            full_name TEXT,
            iin TEXT UNIQUE DEFAULT '',
            pwd TEXT NOT NULL,
            phone TEXT UNIQUE,
            role TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_login_at TEXT,
            email_confirmed INTEGER DEFAULT 0,
            phone_confirmed INTEGER DEFAULT 0,
            failed_logins INTEGER DEFAULT 0,
            is_blocked INTEGER DEFAULT 0,
            is_deleted INTEGER DEFAULT 0
        );""")
        conn.execute("""CREATE TABLE IF NOT EXISTS reset_tokens(
            token TEXT PRIMARY KEY,
            login TEXT,
            expires_at TEXT
        );""")
        conn.commit()
        return conn

    def _sync_backup(self, note):
        t = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = self._backup_dir / f"{t}_{note or 'auto'}.db"
        shutil.copy2(self._db_path, dst)
        return dst

    async def run(self):
        conn = await asyncio.to_thread(self._sync_open)
        while True:
            t: Task = await self._q.get()
            try:
                await getattr(self, f"_op_{t.op}")(conn, t)
            except Exception as e:
                t.fut.set_exception(e)
            finally:
                self._q.task_done()

    async def _op_add(self, c, t):
        q = ("INSERT INTO users(login, full_name, iin, pwd, phone, role) "
             "VALUES(:login, :full_name, :iin, :pwd, :phone, :role);")
        await asyncio.to_thread(c.execute, q, t.payload)
        await asyncio.to_thread(c.commit)
        t.fut.set_result(True)

    async def _op_get(self, c, t):
        cur = await asyncio.to_thread(c.execute,
            "SELECT * FROM users WHERE login=? AND is_deleted=0", (t.payload["login"],))
        t.fut.set_result(cur.fetchone())

    async def _op_del(self, c, t):
        await asyncio.to_thread(c.execute,
            "UPDATE users SET is_deleted=1 WHERE login=?", (t.payload["login"],))
        await asyncio.to_thread(c.commit)
        t.fut.set_result(True)

    async def _op_restore_user(self, c, t):
        await asyncio.to_thread(c.execute,
            "UPDATE users SET is_deleted=0 WHERE login=?", (t.payload["login"],))
        await asyncio.to_thread(c.commit)
        t.fut.set_result(True)

    async def _op_set_role(self, c, t):
        await asyncio.to_thread(c.execute,
            "UPDATE users SET role=? WHERE login=?",
            (t.payload["role"], t.payload["login"]))
        await asyncio.to_thread(c.commit)
        t.fut.set_result(True)

    async def _op_upd_pwd(self, c, t):
        await asyncio.to_thread(c.execute,
            "UPDATE users SET pwd=? WHERE login=?",
            (t.payload["pwd"], t.payload["login"]))
        await asyncio.to_thread(c.commit)
        t.fut.set_result(True)

    async def _op_upd_contacts(self, c, t):
        sets, params = [], []
        for k in ("phone", "iin", "full_name"):
            v = t.payload.get(k)
            if v is not None:
                sets.append(f"{k}=?")
                params.append(v)
        if sets:
            params.append(t.payload["login"])
            sql = "UPDATE users SET " + ", ".join(sets) + " WHERE login=?"
            await asyncio.to_thread(c.execute, sql, params)
            await asyncio.to_thread(c.commit)
        t.fut.set_result(True)

    async def _op_check(self, c, t):
        login, phone, iin = t.payload.values()
        cond, prm = [], []
        if login: cond.append("login=?"); prm.append(login)
        if phone: cond.append("phone=?"); prm.append(phone)
        if iin: cond.append("iin=?"); prm.append(iin)
        if not cond:
            t.fut.set_result({})
            return
        sql = "SELECT login, phone, iin FROM users WHERE " + " OR ".join(cond)
        cur = await asyncio.to_thread(c.execute, sql, prm)
        row = cur.fetchone()
        busy = {"login": False, "phone": False, "iin": False}
        if row:
            busy["login"] = login and row[0] == login
            busy["phone"] = phone and row[1] == phone
            busy["iin"] = iin and row[2] == iin
        t.fut.set_result(busy)

    async def _op_backup(self, c, t):
        dst = await asyncio.to_thread(self._sync_backup, t.payload["note"])
        t.fut.set_result(dst)
