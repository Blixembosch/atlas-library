"""Atlas Library için kalıcı veritabanı: GitHub `data` branch'inde SQL dökümü.

Streamlit Community Cloud'un diski geçicidir. Bu modül veritabanının kalıcı
kopyasını aynı deponun ayrı bir `data` branch'inde `db/atlas_library.sql`
(SQLite iterdump) olarak tutar. Cloud yalnızca main'i izlediği için bu
branch'e yazmak uygulamayı yeniden başlatmaz.

Açma anahtarı: st.secrets["github"]["db_sync"] = true. Yoksa uygulama eskisi
gibi yerel `atlas_library.db` dosyasıyla çalışır (yerel geliştirme).

Kullanım (Library.py):
    cloud_db.ensure_started()      # süreç başına bir kez
    DB_NAME = str(cloud_db.active_path())
"""

from __future__ import annotations

import atexit
import base64
import hashlib
import os
from pathlib import Path
import sqlite3
import tempfile
import threading
import time

try:  # Streamlit olmadan da (test) import edilebilsin
  import requests
except Exception:  # pragma: no cover
  requests = None

DB_FILE_NAME = "atlas_library.db"
REPO_PATH = "db/atlas_library.sql"
MAIN_TABLE = "books"
API = "https://api.github.com"

POLL_SECONDS = 1.0
QUIET_SECONDS = 1.5
BACKOFF_STEPS = (5, 10, 20, 40, 60)


class CloudSyncUnavailable(RuntimeError):
  """GitHub'a ulaşılamadı veya tohumlama doğrulanamadı; uygulama açılmamalı."""


class Conflict(Exception):
  """GitHub'daki dosya başka yerden değişmiş (409/422)."""


class NetworkError(Exception):
  """Ağ hatası veya geçici GitHub hatası."""


# --------------------------------------------------------------------------
# Döküm / geri yükleme
# --------------------------------------------------------------------------
def dump_db(path) -> str:
  """SQLite dosyasının tutarlı metin dökümü (önce backup ile anlık görüntü)."""
  src = sqlite3.connect(str(path))
  snap = sqlite3.connect(":memory:")
  try:
    src.backup(snap)
    return "\n".join(snap.iterdump()) + "\n"
  finally:
    snap.close()
    src.close()


def main_table_rows(path) -> int:
  con = sqlite3.connect(str(path))
  try:
    return con.execute(f"SELECT COUNT(*) FROM {MAIN_TABLE}").fetchone()[0]
  except sqlite3.Error:
    return 0
  finally:
    con.close()


def dump_has_records(text: str) -> bool:
  """Dökümde ana tabloya en az bir kayıt eklenmiş mi?"""
  return f'INSERT INTO "{MAIN_TABLE}"' in text or f"INSERT INTO {MAIN_TABLE}" in text


def restore_dump(text: str, target) -> None:
  """Dökümü geçici dosyaya kurar, sonra os.replace ile tek adımda yerine koyar."""
  target = Path(target)
  target.parent.mkdir(parents=True, exist_ok=True)
  fd, tmp = tempfile.mkstemp(prefix=target.name + ".", suffix=".tmp", dir=target.parent)
  os.close(fd)
  os.unlink(tmp)
  con = sqlite3.connect(tmp)
  try:
    con.executescript(text)
    con.commit()
  finally:
    con.close()
  os.replace(tmp, target)


def _sha256(text: str) -> str:
  return hashlib.sha256(text.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------
# GitHub (Contents API, yalnızca requests)
# --------------------------------------------------------------------------
class Remote:
  def __init__(self, token, repo, branch="data", base="main", session=None, path=REPO_PATH):
    self.repo = repo
    self.branch = branch
    self.base = base
    self.path = path
    self.s = session or requests.Session()
    self.s.headers.update({
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })

  # -- yardımcılar --
  def _req(self, method, url, **kw):
    try:
      r = self.s.request(method, url, timeout=20, **kw)
    except Exception as e:  # ağ/DNS/timeout
      raise NetworkError(str(e)) from e
    if r.status_code >= 500 or r.status_code == 429:
      raise NetworkError(f"GitHub {r.status_code}")
    return r

  def ensure_branch(self):
    r = self._req("GET", f"{API}/repos/{self.repo}/git/ref/heads/{self.branch}")
    if r.status_code == 200:
      return
    if r.status_code != 404:
      raise NetworkError(f"branch kontrolü {r.status_code}: {r.text[:120]}")
    b = self._req("GET", f"{API}/repos/{self.repo}/git/ref/heads/{self.base}")
    if b.status_code != 200:
      raise NetworkError(f"base branch okunamadı {b.status_code}: {b.text[:120]}")
    sha = b.json()["object"]["sha"]
    c = self._req(
        "POST", f"{API}/repos/{self.repo}/git/refs",
        json={"ref": f"refs/heads/{self.branch}", "sha": sha},
    )
    if c.status_code not in (200, 201, 422):  # 422: aynı anda başkası açmış
      raise NetworkError(f"branch açılamadı {c.status_code}: {c.text[:120]}")

  def get(self, path=None):
    """(metin, sha) döner; dosya yoksa (None, None)."""
    path = path or self.path
    url = f"{API}/repos/{self.repo}/contents/{path}"
    r = self._req("GET", url, params={"ref": self.branch})
    if r.status_code == 404:
      return None, None
    if r.status_code != 200:
      raise NetworkError(f"okuma {r.status_code}: {r.text[:120]}")
    j = r.json()
    sha = j.get("sha")
    content = j.get("content") or ""
    if j.get("encoding") == "base64" and content:
      text = base64.b64decode(content).decode("utf-8")
    else:  # 1 MB üstü: ham içerik
      raw = self._req(
          "GET", url, params={"ref": self.branch},
          headers={"Accept": "application/vnd.github.raw+json"},
      )
      if raw.status_code != 200:
        raise NetworkError(f"ham okuma {raw.status_code}")
      text = raw.text
    return text, sha

  def put(self, text, message, sha=None, path=None):
    """Yeni sha döner. Sha uyuşmazsa Conflict."""
    path = path or self.path
    body = {
        "message": message,
        "content": base64.b64encode(text.encode("utf-8")).decode("ascii"),
        "branch": self.branch,
    }
    if sha:
      body["sha"] = sha
    r = self._req("PUT", f"{API}/repos/{self.repo}/contents/{path}", json=body)
    if r.status_code in (409, 422):
      raise Conflict(r.text[:200])
    if r.status_code not in (200, 201):
      raise NetworkError(f"yazma {r.status_code}: {r.text[:120]}")
    return r.json()["content"]["sha"]


# --------------------------------------------------------------------------
# Senkron
# --------------------------------------------------------------------------
class Sync:
  def __init__(self, work_path, remote, clock=time.time, sleep=time.sleep,
               poll=POLL_SECONDS, quiet=QUIET_SECONDS, sha=None, last_hash=None):
    self.work = Path(work_path)
    self.remote = remote
    self.clock = clock
    self.sleep = sleep
    self.poll = poll
    self.quiet = quiet
    self.sha = sha
    self.last_hash = last_hash
    self.stopped = False
    self.message = ""          # uyarı metni
    self.last_ok = clock()
    self._seen = self._sig()
    self._changed_at = clock()
    self._dirty = False
    self._retry_at = 0.0
    self._fail_n = 0
    self._lock = threading.Lock()
    self._stop_evt = threading.Event()
    self._thread = None

  # -- durum --
  def _sig(self):
    try:
      st = self.work.stat()
      return (st.st_mtime_ns, st.st_size)
    except OSError:
      return None

  def status(self):
    """(düzey, metin): düzey ok | saving | warn"""
    if self.stopped:
      return "warn", self.message or "⚠️ Eşitleme durdu"
    if self.message:
      return "warn", self.message
    if self._dirty:
      return "saving", "☁️ Kaydediliyor…"
    mins = int((self.clock() - self.last_ok) // 60)
    when = "az önce" if mins < 1 else f"{mins} dk önce"
    return "ok", f"☁️ Veriler kaydedildi · {when}"

  # -- adımlar --
  def check(self):
    """Tek yoklama adımı: değişiklik var ve sakinleştiyse gönder."""
    if self.stopped:
      return
    now = self.clock()
    sig = self._sig()
    if sig != self._seen:
      self._seen = sig
      self._changed_at = now
      self._dirty = True
    if self._dirty and now - self._changed_at >= self.quiet and now >= self._retry_at:
      self.push()

  def push(self, force=False):
    """Çalışma dosyasının dökümünü gönderir. True: gönderildi/gerek yok."""
    with self._lock:
      if self.stopped:
        return False
      try:
        if main_table_rows(self.work) == 0:
          self.message = "⚠️ Veritabanı boş görünüyor; GitHub'a gönderilmedi"
          self._dirty = False
          return False
        text = dump_db(self.work)
      except sqlite3.Error as e:
        self.message = f"⚠️ Veritabanı okunamadı: {e}"
        return False
      if not dump_has_records(text):
        self.message = "⚠️ Döküm kayıt içermiyor; gönderilmedi"
        self._dirty = False
        return False
      digest = _sha256(text)
      if digest == self.last_hash:
        self._dirty = False
        self.message = ""
        return True
      msg = "db: kayıt güncellendi"
      try:
        self.sha = self.remote.put(text, msg, sha=self.sha)
      except Conflict:
        self._save_conflict(text)
        return False
      except NetworkError as e:
        delay = BACKOFF_STEPS[min(self._fail_n, len(BACKOFF_STEPS) - 1)]
        self._fail_n += 1
        self._retry_at = self.clock() + delay
        self.message = f"⚠️ GitHub'a ulaşılamadı, {delay} sn sonra tekrar denenecek"
        return False
      self.last_hash = digest
      self._dirty = False
      self._fail_n = 0
      self._retry_at = 0.0
      self.message = ""
      self.last_ok = self.clock()
      return True

  def _save_conflict(self, text):
    stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime(self.clock()))
    path = f"db/conflicts/{stamp}.sql"
    try:
      self.remote.put(text, "db: çakışma kopyası", path=path)
      where = f"GitHub'da {path}"
    except Exception:
      where = "kaydedilemedi"
    self.stopped = True
    self.message = (
        "⚠️ GitHub'daki veri başka yerden değişmiş; eşitleme durduruldu. "
        f"Yerel kopya: {where}. Uygulamayı yeniden başlatmadan önce yöneticiye haber verin."
    )

  def flush(self):
    """Kapanışta bekleyen değişikliği hemen gönder."""
    if self.stopped:
      return
    if self._sig() != self._seen:
      self._seen = self._sig()
      self._dirty = True
    if self._dirty:
      self.push(force=True)

  # -- arka plan --
  def start(self):
    if self._thread is not None:
      return
    self._thread = threading.Thread(target=self._loop, name="cloud-db-sync", daemon=True)
    self._thread.start()
    atexit.register(self._safe_flush)

  def _loop(self):
    while not self._stop_evt.is_set():
      try:
        self.check()
      except Exception as e:  # thread asla ölmesin
        self.message = f"⚠️ Eşitleme hatası: {e}"
      self.sleep(self.poll)

  def _safe_flush(self):
    try:
      self.flush()
    except Exception:
      pass

  def stop(self):
    self._stop_evt.set()


# --------------------------------------------------------------------------
# Süreç başına bir kez başlatma
# --------------------------------------------------------------------------
_STATE = {"sync": None, "path": None, "ready": False}
_LOCK = threading.Lock()


def _default_local_db():
  return Path(__file__).resolve().parent / DB_FILE_NAME


def _secrets_cfg():
  try:
    import streamlit as st
    g = st.secrets.get("github", None)
    return dict(g) if g else {}
  except Exception:
    return {}


def _work_path(home=None):
  return Path(home or Path.home()) / ".atlas_library" / DB_FILE_NAME


def ensure_started(cfg=None, local_db=None, session=None, clock=time.time,
                   sleep=time.sleep, home=None, start_thread=True):
  """Süreç başına bir kez: GitHub'daki dökümü çalışma dosyasına kurar."""
  with _LOCK:
    if _STATE["ready"]:
      return _STATE["sync"]
    cfg = cfg if cfg is not None else _secrets_cfg()
    local_db = Path(local_db) if local_db else _default_local_db()

    if not cfg.get("db_sync"):
      _STATE.update(sync=None, path=local_db, ready=True)
      return None

    for key in ("token", "repo"):
      if not cfg.get(key):
        raise CloudSyncUnavailable(f"[github] altında '{key}' tanımlı değil")

    remote = Remote(
        cfg["token"], cfg["repo"], cfg.get("branch", "data"),
        cfg.get("base", "main"), session=session,
    )
    work = _work_path(home)
    try:
      remote.ensure_branch()
      text, sha = remote.get()
      if text is None:
        text, sha = _seed_remote(remote, local_db)
    except NetworkError as e:
      raise CloudSyncUnavailable(f"GitHub'a ulaşılamadı: {e}") from e

    if not dump_has_records(text):
      raise CloudSyncUnavailable("GitHub'daki döküm kayıt içermiyor; güvenlik için açılmadı")

    if work.exists():
      try:
        if dump_db(work) != text:
          bak = work.with_name(work.name + ".before-sync.bak")
          bak.write_bytes(work.read_bytes())
      except sqlite3.Error:
        pass
    restore_dump(text, work)

    sync = Sync(work, remote, clock=clock, sleep=sleep, sha=sha, last_hash=_sha256(text))
    _STATE.update(sync=sync, path=work, ready=True)
    if start_thread:
      sync.start()
    return sync


def _seed_remote(remote, local_db):
  """İlk kurulum: depodaki .db dosyasını yükle, geri okuyup birebir doğrula."""
  if not Path(local_db).exists() or main_table_rows(local_db) == 0:
    raise CloudSyncUnavailable(
        "GitHub'da döküm yok ve tohumlanacak dolu bir atlas_library.db bulunamadı"
    )
  text = dump_db(local_db)
  try:
    remote.put(text, "db: ilk yükleme")
  except Conflict as e:
    raise CloudSyncUnavailable(f"ilk yükleme çakıştı: {e}") from e
  back, sha = remote.get()
  if back != text:
    raise CloudSyncUnavailable("ilk yükleme doğrulanamadı (geri okunan döküm farklı)")
  return back, sha


def active_path():
  if not _STATE["ready"]:
    raise RuntimeError("cloud_db.ensure_started() önce çağrılmalı")
  return _STATE["path"]


current_path = active_path


def status():
  """Kenar çubuğu için (düzey, metin) ya da yerel modda None."""
  s = _STATE["sync"]
  return s.status() if s else None


def reset_for_tests():
  s = _STATE["sync"]
  if s:
    s.stop()
  _STATE.update(sync=None, path=None, ready=False)
