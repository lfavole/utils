"""Create a timelapse for a given day."""
import asyncio
import atexit
import ftplib
import itertools
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

print("Starting the script...")

AUDIO_FILES = (os.getenv("AUDIO_FILES") or os.getenv("AUDIO_FILE") or "").split(",")
FTP_HOST = os.getenv("FTP_HOST")
FTP_PORT = int(os.getenv("FTP_PORT") or "0")
HTTP_PORT = int(os.getenv("HTTP_PORT") or "0")
FREEBOX_APP_TOKEN = os.getenv("FREEBOX_APP_TOKEN")
FREEBOX_TRACK_ID = (os.getenv("FREEBOX_TRACK_ID") or "").removeprefix("track_id_")
FTP_USERNAME = os.getenv("FTP_USERNAME") or "freebox"
FTP_PASSWORD = os.getenv("FTP_PASSWORD", "")
FTP_PATH = os.getenv("FTP_PATH") or "/Disque dur/Camera"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_IDS = (os.getenv("TELEGRAM_CHAT_IDS") or os.getenv("TELEGRAM_CHAT_ID") or "").split(",")

TELEGRAM_CHAT_IDS = [id for id in TELEGRAM_CHAT_IDS if id]
AUDIO_FILES = [file for file in AUDIO_FILES if file] or [
    "https://www.youtube.com/watch?v=gSTeTJvO7xg",
    "https://www.youtube.com/watch?v=IhwfBq4cwCU",
]

# Check required variables
required_vars = ['FTP_USERNAME', 'FTP_PASSWORD', 'FTP_PATH', 'AUDIO_FILES', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_IDS']
for var in required_vars:
    if not locals().get(var):
        raise ValueError(f"{var} is not set. Please set it.")

OUTPUT_DIR = Path(__file__).parent / "videos"
OUTPUT_DIR.mkdir(exist_ok=True)

date = sys.argv[1] if len(sys.argv) > 1 else "yesterday"

french_months = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

# Get the date in YYYYMMDD format
if date == "yesterday":
    date_obj = datetime.now() - timedelta(days=1)
else:
    date_obj = datetime.strptime(date, "%Y-%m-%d")

yyyymmdd = date_obj.strftime("%Y%m%d")
print(f"Date: {yyyymmdd}")

# Get the French date
if date_obj.day == 1:
    french_date = "1er"
else:
    french_date = str(date_obj.day)
french_date += f" {french_months[date_obj.month - 1]} {date_obj.year}"
print(f"Formatted date: {french_date}")

def send_telegram_message(chat_id, text):
    request = Request(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        data=urlencode({
            "chat_id": f"{chat_id}",
            "text": text,
            "parse_mode": "HTML",
        }).encode(),
        method="POST",
    )
    error = None
    try:
        with urlopen(request) as f:
            data = json.load(f)
    except HTTPError as e:
        error = e
        data = json.load(e.file)

    if not data["ok"] or error:
        msg = f"Failed to call Telegram API: {data['description']}"
        if error:
            new_error = RuntimeError(msg)
            new_error.data = data
            raise new_error from error
        raise RuntimeError(msg)

#########################################
# 1. Copy the files from the FTP server #
#########################################

# Define source FTP directory
source_ftp = f"{FTP_PATH}/{yyyymmdd}"

# Check if the source FTP directory exists
print(f"Checking if the directory {source_ftp} exists...")
try:
    # Connect to the FTP server
    with ftplib.FTP_TLS() as ftp:
        ftp.connect(FTP_HOST, FTP_PORT)
        ftp.login(FTP_USERNAME, FTP_PASSWORD)
        # Attempt to change to the specified directory
        ftp.cwd(source_ftp)
        print(f"Directory {source_ftp} exists on the FTP server.")
except ftplib.error_perm as e:
    # If we get a permission error, the directory does not exist
    if str(e).startswith('550 '):
        print(f"Source FTP directory {source_ftp} does not exist.")
        print("Sending message on Telegram...")
        for chat_id in TELEGRAM_CHAT_IDS:
            send_telegram_message(chat_id, f"Aucune vidéo n'a été enregistrée par la caméra pour le {french_date}.")
            print("Message sent to Telegram.")

        sys.exit()
    else:
        raise

# Temporary directory with random name
TMP_DIR = Path(tempfile.mkdtemp())
print(f"Temporary directory: {TMP_DIR}")

# Function to clean up the temporary directory
def cleanup():
    shutil.rmtree(TMP_DIR)
    print(f"Deleted temp working directory {TMP_DIR}")

atexit.register(cleanup)

uv_installed = False

other_audio_files = []

def download_ftp_file(file):
    print(f"Downloading {file} from FTP server...")
    with ftplib.FTP_TLS() as ftp:
        ftp.connect(FTP_HOST, FTP_PORT)
        ftp.login(FTP_USERNAME, FTP_PASSWORD)
        ftp.cwd(FTP_PATH)
        # Download the file on the FTP server
        ret = TMP_DIR / f"{uuid.uuid4()}{Path(file).suffix}"
        try:
            print(f"Downloading files in directory {file}...")
            for subfile in ftp.nlst(file):
                if subfile in (".", ".."):
                    continue
                yield from download_ftp_file(file + "/" + subfile)
            return
        except ftplib.error_perm as e:
            if "Not a directory" not in str(e):
                raise
            with ret.open("wb") as f:
                ftp.retrbinary(f"RETR {file}", f.write)
        print(f"File {file} downloaded to {ret} from the FTP server.")
        yield ret

for i, file in enumerate(AUDIO_FILES):
    if file[:4] == "ftp/":
        AUDIO_FILES[i] = None
        other_audio_files.append(list(download_ftp_file(file[4:])))

    if any(text in file for text in ("youtube.com", "youtu.be")):
        print(f"Audio file {file} needs to be downloaded.")
        if not uv_installed:
            print("Installing uv...")
            os.system(
                'powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"'
                if sys.platform == "win32"
                else "curl -LsSf https://astral.sh/uv/install.sh | sh"
            )

        print(f"Downloading {file}...")
        AUDIO_FILES[i] = subprocess.check_output(
            [
                "uv",
                "tool",
                "run",
                "yt-dlp",
                "--no-config",
                "--extract-audio",
                "--audio-format",
                "mp3",
                "--audio-quality",
                "128k",
                "--output",
                str(TMP_DIR / "%(id)s.%(ext)s"),
                # https://github.com/yt-dlp/yt-dlp#outtmpl-postprocess-note
                "--print",
                "after_move:filepath",
                "--no-simulate",
                file,
            ],
            text=True,
        ).strip()
        print(f"{file} has been downloaded to {AUDIO_FILES[i]}")

AUDIO_FILES = [*itertools.chain(
    *(
        other_audio_files.pop(0) if file is None else [file]
        for file in AUDIO_FILES
    )
)]
# if there are remaining files, add them
AUDIO_FILES.extend(other_audio_files)

# Define destination local directory
destination_local = TMP_DIR / yyyymmdd

# Create the destination directory if it doesn't exist
destination_local.mkdir(exist_ok=True)
print(f"Destination directory created: {destination_local}")
print()

# Copy files from the FTP directory to the local directory
print(f"Copying files from FTP server from {source_ftp} to {destination_local}...")
with ftplib.FTP_TLS() as ftp:
    ftp.connect(FTP_HOST, FTP_PORT)
    ftp.login(FTP_USERNAME, FTP_PASSWORD)
    ftp.cwd(source_ftp)
    files = ftp.nlst()  # Get a list of file names
    # Download each file
    for filename in files:
        if filename in (".", "..") or not filename.endswith(".mp4"):
            continue
        local_file_path = destination_local / filename
        with open(local_file_path, 'wb') as local_file:
            ftp.retrbinary(f"RETR {filename}", local_file.write)
            print(f"Downloaded: {filename} to {local_file_path}")

print(f"Files copied from {source_ftp} to {destination_local}\n")

#############################################
# 2. Concatenate and speed up all the files #
#############################################

# Create a file list
filelist = TMP_DIR / "filelist.txt"
with filelist.open('w') as f:
    for video_file in sorted(destination_local.iterdir()):
        if video_file.name.endswith('.mp4'):
            f.write(f"file '{destination_local / video_file}'\n")
print(f"File list created: {filelist}\n")

#########################################
# 3. Add the title and transition pages #
#########################################

# Download Montserrat font
font_path = os.path.join(TMP_DIR, "Montserrat-Black.ttf")
print(f"Downloading Montserrat font into {font_path}...")
font_url = "https://raw.githubusercontent.com/JulietaUla/Montserrat/refs/heads/master/fonts/ttf/Montserrat-Black.ttf"
with urlopen(font_url) as rf, open(font_path, 'wb') as f:
    shutil.copyfileobj(rf, f)
print(f"Font downloaded: {font_path}\n")

# Concatenate the text page (without the last second) and the transition with the input video
output_video = OUTPUT_DIR / f"{yyyymmdd}.mp4"
print(f"Concatenating everything into {output_video}...")

# Initialize the ffmpeg command with input files
ffmpeg_cmd = [
    'ffmpeg', '-y', '-hide_banner', '-stats', '-safe', '0', '-f', 'concat', '-i', filelist,
    '-i', os.path.join(destination_local, os.listdir(destination_local)[0]),
    '-f', 'lavfi', '-t', '5', '-i', 'color=c=black:s=1280x720'
]

# Add audio files to the command
for audio_file in AUDIO_FILES:
    ffmpeg_cmd += ['-i', os.path.expanduser(audio_file)]

# Build the filter_complex string
filter_complex = (
    "[0:v]setpts=PTS/10[spedup]; "
    f"[2:v]drawtext=fontfile={font_path}:text='{french_date}':fontcolor=white:fontsize=96:x=(w-text_w)/2:y=(h-text_h)/2[text]; "
    "[text]split[text1][text2]; "
    "[text1]format=rgba,fade=t=out:st=0:d=1:alpha=1[fade]; "
    "[spedup][fade]overlay[transition]; "
    "[1:v]setpts=PTS/10,trim=start=1,setpts=PTS-STARTPTS[spedup_without_1s]; "
    "[text2][transition][spedup_without_1s]concat=n=3:v=1:a=0[v];"
)

# Add audio concat filter
i = 3
for _ in AUDIO_FILES:
    filter_complex += f"[{i}:a]"
    i += 1
filter_complex += f"concat=n={len(AUDIO_FILES)}:v=0:a=1[a]"

# Complete the ffmpeg command
# Convert to yuv420p color space thanks to https://superuser.com/a/705070
ffmpeg_cmd += ['-filter_complex', filter_complex, '-map', '[v]', '-map', '[a]', '-shortest', '-b:a', '96k', '-b:v', '1200k', '-pix_fmt', 'yuv420p', output_video]

# Execute the ffmpeg command
subprocess.run(ffmpeg_cmd, check=True)
print(f"Final video created: {output_video}\n")

#############################################
# 4. Rename the directory on the FTP server #
#############################################

# Directories
old_dir = source_ftp
new_dir = f"{source_ftp}_ok"

# If the date is before today, rename the directory
today = datetime.now()
if date_obj < today:
    print(f"Renaming {old_dir} directory to {new_dir} on FTP server...")

    with ftplib.FTP_TLS() as ftp:
        ftp.connect(FTP_HOST, FTP_PORT)
        ftp.login(FTP_USERNAME, FTP_PASSWORD)
        ftp.rename(old_dir, new_dir)
    print("Directory renamed.")
else:
    print("Date is today or future. Skipping directory rename.")

print()

##########################################
# 5. Back up the video to the FTP server #
##########################################

video_dir_ftp = f"{FTP_PATH}/videos"
print(f"Backing up {output_video.name} to {video_dir_ftp}...")

with ftplib.FTP_TLS() as ftp:
    ftp.connect(FTP_HOST, FTP_PORT)
    ftp.login(FTP_USERNAME, FTP_PASSWORD)
    try:
        # Attempt to change to the specified directory
        ftp.cwd(video_dir_ftp)
    except ftplib.error_perm as e:
        # If we get a permission error, the directory does not exist
        if str(e).startswith('550 '):
            ftp.mkd(video_dir_ftp)
            ftp.cwd(video_dir_ftp)
        else:
            raise
    with output_video.open("rb") as f:
        ftp.storbinary(f"STOR {output_video.name}", f)

print("File backed up.")

#################################
# 6. Send the video to Telegram #
#################################

try:
    from freebox_api import Freepybox
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "online"))
    from get_freebox_share_path import get_freebox_share_path
except ModuleNotFoundError as e:
    print(f"{type(e).__name__}: {e}")
    print("Sending video file to Telegram...")
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
            check=True,
        )
        print()
        print("Video sent to Telegram.")
else:
    async def get_url():
        def new_readfile_app_token(self, _):
            return (FREEBOX_APP_TOKEN, FREEBOX_TRACK_ID, self.app_desc)

        Freepybox._readfile_app_token = new_readfile_app_token
        fbx = Freepybox(api_version="v8")
        try:
            await fbx.open(FTP_HOST, HTTP_PORT)
            return await get_freebox_share_path(fbx, f"{video_dir_ftp}/{output_video.name}", video_dir_ftp)
        finally:
            await fbx.close()

    url = asyncio.run(get_url())

    print("Sending video link to Telegram...")
    for chat_id in TELEGRAM_CHAT_IDS:
        send_telegram_message(chat_id, f"Vidéo du {french_date}\n{url}")
        print("Message sent to Telegram.")

print()

print("Script completed.")
