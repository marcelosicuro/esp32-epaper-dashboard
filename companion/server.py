#!/usr/bin/env python3
"""
Painel Companion — roda no Mac em segundo plano.

Lê Apple Reminders via AppleScript e e-mails via IMAP,
servindo um endpoint JSON local para o ESP32.

Uso:  python3 server.py
API:  GET http://<IP-DO-MAC>:8765/data.json
"""

import imaplib
import json
import logging
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import yaml  # pip install pyyaml

# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("companion")

CONFIG_PATH = Path(__file__).parent / "config.yaml"
REFRESH_INTERVAL = 120  # segundos entre atualizações de dados

# ---------------------------------------------------------------------------
# Estado compartilhado entre threads
_cache: dict = {"email_unread": -1, "tasks": [], "updated_at": ""}
_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Apple Reminders via AppleScript (só macOS)

def get_reminders(list_name: str = "Reminders") -> list[str]:
    script = f'''
    tell application "Reminders"
        try
            set rl to first list whose name is "{list_name}"
            set todo to {{}}
            repeat with t in (reminders of rl whose completed is false)
                set end of todo to name of t
            end repeat
            return todo
        on error
            return {{}}
        end try
    end tell
    '''
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            raw = result.stdout.strip()
            # AppleScript retorna lista separada por vírgulas
            items = [t.strip() for t in raw.split(",") if t.strip()]
            return items
    except Exception as e:
        log.warning("Reminders: %s", e)
    return []


# ---------------------------------------------------------------------------
# E-mail via IMAP

def get_email_unread(cfg: dict) -> int:
    try:
        host = cfg["imap_host"]
        user = cfg["imap_user"]
        pw   = cfg["imap_password"]
        folder = cfg.get("imap_folder", "INBOX")

        mail = imaplib.IMAP4_SSL(host, timeout=10)
        mail.login(user, pw)
        mail.select(folder, readonly=True)
        _, data = mail.search(None, "UNSEEN")
        count = len(data[0].split()) if data[0] else 0
        mail.logout()
        return count
    except Exception as e:
        log.warning("Email: %s", e)
        return -1


# ---------------------------------------------------------------------------
# Loop de atualização em background

def refresh_loop(cfg: dict):
    while True:
        tasks: list[str] = []

        # Reminders
        reminders_cfg = cfg.get("reminders", {})
        if reminders_cfg.get("enabled", True):
            list_name = reminders_cfg.get("list", "Reminders")
            tasks = get_reminders(list_name)
            log.info("Reminders: %d tarefa(s)", len(tasks))

        # E-mail
        email_unread = -1
        email_cfg = cfg.get("email", {})
        if email_cfg.get("enabled", False):
            email_unread = get_email_unread(email_cfg)
            log.info("Email não lidos: %d", email_unread)

        with _lock:
            _cache["tasks"]        = tasks[:5]  # máximo 5 tarefas
            _cache["email_unread"] = email_unread
            _cache["updated_at"]   = time.strftime("%H:%M")

        log.info("Cache atualizado às %s", _cache["updated_at"])
        time.sleep(REFRESH_INTERVAL)


# ---------------------------------------------------------------------------
# HTTP Server

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # silencia log padrão do HTTP server

    def do_GET(self):
        if self.path in ("/data.json", "/"):
            with _lock:
                payload = json.dumps(_cache, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(404)
            self.end_headers()


# ---------------------------------------------------------------------------

def load_config() -> dict:
    if not CONFIG_PATH.exists():
        log.error("config.yaml não encontrado. Copie config.yaml.example para config.yaml.")
        raise SystemExit(1)
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def main():
    cfg  = load_config()
    port = cfg.get("port", 8765)

    # Inicia loop de dados em background
    t = threading.Thread(target=refresh_loop, args=(cfg,), daemon=True)
    t.start()

    # Aguarda primeira coleta
    time.sleep(3)

    server = HTTPServer(("0.0.0.0", port), Handler)
    log.info("Companion rodando em http://0.0.0.0:%d/data.json", port)
    log.info("Use este IP no secrets.yaml do ESPHome: companion_url: http://<SEU-IP-DO-MAC>:%d", port)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Encerrando.")


if __name__ == "__main__":
    main()
