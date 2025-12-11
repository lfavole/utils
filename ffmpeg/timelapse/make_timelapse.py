# /// script
# dependencies = ["fsspec>=2025.12.0"]
# ///
"""
Create a timelapse video from a base input folder, an output folder and a date.

Usage:
  python create_video.py --base-input <base-input-uri-or-path> --output <output-uri-or-path> [--date YYYY-MM-DD]
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.request import urlopen

from fsspec.core import url_to_fs


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Create a timelapse video from a base input folder.")
    parser.add_argument(
        "--base-input",
        required=True,
        help="Base input folder (URI or local path). The script will look into base_input/YYYYMMDD",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output folder (URI or local path). The script will create output/YYYYMMDD.mp4",
    )
    parser.add_argument("--date", help="Date to process in YYYY-MM-DD format (default: yesterday).")
    parser.add_argument("--tls", action="store_true", help="Use TLS (especially FTPS) to access files")
    parser.add_argument("--redo", action="store_true", help="Process the _ok directory")
    parser.add_argument("--password", help="Password that will override the one in the paths")
    args = parser.parse_args(argv)

    # Resolve date (yesterday default)
    if not args.date or args.date == "yesterday":
        date_obj = date.today() - timedelta(days=1)
    else:
        date_obj = datetime.strptime(args.date, "%Y-%m-%d").date()
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

    with tempfile.TemporaryDirectory(prefix="timelapse_") as TMP_DIR:
        TMP_DIR = Path(TMP_DIR)

        fsspec_args = {}
        if args.password is not None:
            fsspec_args["password"] = args.password
        if args.tls:
            fsspec_args["tls"] = True

        fs, path = url_to_fs(args.base_input, **fsspec_args)
        # Ensure path has no trailing slash
        path = path.rstrip(fs.sep)

        input_dir = path + fs.sep + yyyymmdd + ("_ok" if args.redo else "")

        # Check existence of input folder
        if not fs.exists(input_dir):
            print(
                f"Input directory not found: {input_dir}",
                file=sys.stderr,
            )
            return 2

        # Find all MP4 files
        mp4_files = [*fs.glob(f"{input_dir}{fs.sep}*.mp4")]

        if not mp4_files:
            print(f"No .mp4 files found in {input_dir}", file=sys.stderr)
            return 2

        # Download (or copy) MP4 files to local tmp dir, keeping deterministic order
        local_inputs = []
        for i, remote in enumerate(sorted(mp4_files)):
            local_name = TMP_DIR / Path(remote).name
            fs.get(remote, str(local_name))
            local_inputs.append(local_name)

        # Prepare audio files (from env)
        AUDIO_FILES = (os.getenv("AUDIO_FILES") or os.getenv("AUDIO_FILE") or "").split(",")
        AUDIO_FILES = [a for a in AUDIO_FILES if a]
        if not AUDIO_FILES:
            # Check for files in the "music" directory
            if fs.exists(path + fs.sep + "music"):
                AUDIO_FILES = [*fs.glob(f"{path}{fs.sep}music{fs.sep}**{fs.sep}*.mp3")]
            else:
                AUDIO_FILES = [
                    "https://www.youtube.com/watch?v=gSTeTJvO7xg",
                    "https://www.youtube.com/watch?v=IhwfBq4cwCU",
                ]

        uv_installed = shutil.which("uv") is not None
        # Download or resolve audio files into TMP_DIR
        local_audios = []
        for file in AUDIO_FILES:
            if not file:
                continue

            # For youtube links, use uv/yt-dlp to download to TMP_DIR
            if any(text in file for text in ("youtube.com", "youtu.be")):
                if not uv_installed:
                    if sys.platform == "win32":
                        os.system('powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"')
                    else:
                        os.system("curl -LsSf https://astral.sh/uv/install.sh | sh")
                    uv_installed = True
                path = subprocess.check_output(
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
                        "--print",
                        "after_move:filepath",
                        "--no-simulate",
                        file,
                    ],
                    text=True,
                ).strip()
                local_audios.append(Path(path))
                continue

            # Otherwise, use fsspec to fetch
            dest = TMP_DIR / Path(file).name
            fs.get(file, str(dest))
            local_audios.append(dest)

        # Download Montserrat font (always)
        font_url = (
            "https://raw.githubusercontent.com/JulietaUla/Montserrat/refs/heads/master/fonts/ttf/Montserrat-Black.ttf"
        )
        font_path = TMP_DIR / Path(font_url).name
        with urlopen(font_url) as rf, open(font_path, "wb") as wf:
            shutil.copyfileobj(rf, wf)

        # Create ffmpeg filelist
        SINGLE_QUOTE = "'"
        SINGLE_QUOTE_ESCAPED = "'\\''"
        filelist = TMP_DIR / "filelist.txt"
        with filelist.open("w", encoding="utf-8") as f:
            for p in local_inputs[1:]:
                f.write(f"file '{str(p).replace(SINGLE_QUOTE, SINGLE_QUOTE_ESCAPED)}'\n")

        # Decide local output path first; always use fsspec for the output URI
        out_fs, out_path = url_to_fs(args.output, **fsspec_args)
        out_path = out_path.rstrip(out_fs.sep)
        out_path += out_fs.sep + yyyymmdd + ".mp4"

        local_output = TMP_DIR / Path(out_path).name

        # Build ffmpeg command
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-stats",
            "-f",
            "lavfi",
            "-t",
            "5",
            "-i",
            "color=c=black:s=1280x720",
            "-i",
            str(local_inputs[0]),
            "-safe",
            "0",
            "-f",
            "concat",
            "-i",
            str(filelist),
        ]

        for a in local_audios:
            ffmpeg_cmd += ["-i", str(a)]

        # Build filter_complex
        filter_complex = (
            f"[0:v]drawtext=fontfile='{str(font_path).replace(SINGLE_QUOTE, SINGLE_QUOTE_ESCAPED)}':text='{french_date.replace(SINGLE_QUOTE, SINGLE_QUOTE_ESCAPED)}':fontcolor=white:fontsize=96:x=(w-text_w)/2:y=(h-text_h)/2[text]; "
            "[text]split[text1][text2]; "
            "[text1]format=rgba,fade=t=out:st=0:d=1:alpha=1[fade]; "
            "[spedup][fade]overlay[transition]; "
            "[1:v]setpts=PTS/10,trim=start=1,setpts=PTS-STARTPTS[spedup_without_1s]; "
            "[2:v]setpts=PTS/10,setpts=PTS-STARTPTS[spedup]; "
            "[text2][transition][spedup_without_1s]concat=n=3:v=1:a=0[v]; "
        )

        if local_audios:
            i = 3
            for _ in local_audios:
                filter_complex += f"[{i}:a]"
                i += 1
            filter_complex += f"concat=n={len(local_audios)}:v=0:a=1[a]"
        else:
            filter_complex += "anullsrc=cl=stereo:r=44100[a]"

        ffmpeg_cmd += [
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-shortest",
            "-b:a",
            "96k",
            "-b:v",
            "1200k",
            "-pix_fmt",
            "yuv420p",
            str(local_output),
        ]

        # Run ffmpeg
        subprocess.run(ffmpeg_cmd, check=True)

        # Upload to destination
        out_fs.put(str(local_output), out_path, recursive=False)

        # Rename input directory to add _ok suffix if date is before today
        today = date.today()
        if date_obj < today:
            old_dir = input_dir
            new_dir = input_dir + "_ok"
            try:
                fs.mv(old_dir, new_dir)
            except Exception as exc:
                print("Failed to rename directory:", exc, file=sys.stderr)

        return 0


if __name__ == "__main__":
    sys.exit(main())
