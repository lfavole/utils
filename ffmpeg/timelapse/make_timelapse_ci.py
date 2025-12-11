"""
Minimal wrapper: calls make_timelapse.py with the base input folder, output folder and date.
Then it creates a Freebox share (if available) and sends Telegram messages.

This file intentionally keeps logic minimal.
Always pass base-input/output as URIs (file:// for local).
"""

import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

# Configuration from environment
FTP_HOST = os.getenv("FTP_HOST")
REDO = os.getenv("REDO") == "true"
FTP_PORT = int(os.getenv("FTP_PORT") or "0")
FTP_TLS = os.getenv("FTP_TLS", "").lower() in ("1", "true")
FTP_PATH = os.getenv("FTP_PATH") or "/Disque dur/Camera"
FTP_USERNAME = os.getenv("FTP_USERNAME") or "freebox"
FTP_PASSWORD = os.getenv("FTP_PASSWORD", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_IDS = (os.getenv("TELEGRAM_CHAT_IDS") or os.getenv("TELEGRAM_CHAT_ID") or "").split(",")
TELEGRAM_CHAT_IDS = [c for c in TELEGRAM_CHAT_IDS if c]

OUTPUT_DIR = Path(__file__).parent / "videos"
OUTPUT_DIR.mkdir(exist_ok=True)

# Check for required variables
required_vars = ["FTP_USERNAME", "FTP_PASSWORD", "FTP_PATH", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_IDS"]
for var in required_vars:
    if not locals().get(var):
        raise ValueError(f"{var} is not set. Please set it.")

date = sys.argv[1] if len(sys.argv) > 1 else "yesterday"
if date == "yesterday":
    date_obj = datetime.now() - timedelta(days=1)
else:
    date_obj = datetime.strptime(date, "%Y-%m-%d")
yyyymmdd = date_obj.strftime("%Y%m%d")

french_months = [
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
]
if date_obj.day == 1:
    french_date = "1er"
else:
    french_date = str(date_obj.day)
french_date += f" {french_months[date_obj.month - 1]} {date_obj.year}"

# Build an ftp:// URI including username
host_port = f"{FTP_HOST}:{FTP_PORT}" if FTP_PORT else FTP_HOST
base_input = f"ftp://{FTP_USERNAME}@{host_port}{FTP_PATH}"

# Output path
output = base_input + "/videos"
output_video = output + "/" + yyyymmdd + ".mp4"

# Call make_timelapse.py (assumed next to this script)
create_script = Path(__file__).parent / "make_timelapse.py"
if not create_script.exists():
    print("make_timelapse.py not found next to this script. Aborting.", file=sys.stderr)
    sys.exit(1)

cmd = [
    *(["uv", "run"] if "UV" in os.environ or shutil.which("uv") else [sys.executable]),
    str(create_script),
    "--base-input",
    base_input,
    "--output",
    output,
    "--date",
    date,
    *(["--tls"] if FTP_TLS else []),
    *(["--redo"] if REDO else []),
]
if FTP_PASSWORD:
    cmd += ["--password", FTP_PASSWORD]
print("Calling make_timelapse")
proc = subprocess.run(cmd)
rc = proc.returncode


def send_telegram_message(chat_id, text):
    req = Request(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        data=urlencode({"chat_id": str(chat_id), "text": text, "parse_mode": "HTML"}).encode(),
        method="POST",
    )
    try:
        with urlopen(req) as f:
            data = json.load(f)
            if not data.get("ok"):
                print("Telegram API error:", data, file=sys.stderr)
    except Exception as e:
        print("Failed to send Telegram message:", e, file=sys.stderr)


if rc == 2:
    # no videos for that day
    for chat_id in TELEGRAM_CHAT_IDS:
        send_telegram_message(
            chat_id,
            f"Aucune vidéo n'a été enregistrée par la caméra pour le {french_date}.",
        )
    sys.exit(0)

if rc != 0:
    print("make_timelapse failed with code", rc, file=sys.stderr)
    sys.exit(rc)

# At this point video was created at output_video. Try to create a Freebox share and send Telegram messages.
FREEBOX_APP_TOKEN = os.getenv("FREEBOX_APP_TOKEN")
FREEBOX_TRACK_ID = (os.getenv("FREEBOX_TRACK_ID") or "").removeprefix("track_id_")
HTTP_PORT = int(os.getenv("HTTP_PORT") or "0")

try:
    from freebox_api import Freepybox  # type: ignore

    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "online"))
    from get_freebox_share_path import get_freebox_share_path  # type: ignore
except Exception:
    # fallback: send the video file directly to Telegram via sendVideo
    for chat_id in TELEGRAM_CHAT_IDS:
        subprocess.run(
            [
                "curl",
                "--fail-with-body",
                "-s",
                "-X",
                "POST",
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo",
                "-F",
                f"chat_id={chat_id}",
                "-F",
                f"video=@{output_video}",
                "-F",
                f"caption=Vidéo du {french_date}",
                "-F",
                "parse_mode=HTML",
            ],
            check=False,
        )
    sys.exit(0)


# If we can import freebox_api, try to produce a shareable URL
def new_readfile_app_token(self, _):
    return (FREEBOX_APP_TOKEN, FREEBOX_TRACK_ID, self.app_desc)


Freepybox._readfile_app_token = new_readfile_app_token
fbx = Freepybox(api_version="v8")
try:
    import asyncio

    async def get_url():
        await fbx.open(FTP_HOST, HTTP_PORT)
        try:
            return await get_freebox_share_path(
                fbx, f"{FTP_PATH}/videos/{Path(output_video).name}", f"{FTP_PATH}/videos"
            )
        finally:
            await fbx.close()

    url = asyncio.run(get_url())
except Exception as ex:
    print("Failed to create freebox share:", ex, file=sys.stderr)
    url = None

if url:
    for chat_id in TELEGRAM_CHAT_IDS:
        send_telegram_message(chat_id, f"Vidéo du {yyyymmdd}\n{url}")
