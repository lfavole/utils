import sys
from pathlib import Path
from subprocess import run

for file in sys.argv[1:]:
    file = Path(file)
    orig_file = file.with_suffix(".mp4")
    if not orig_file.exists():
        orig_file = Path("mp4") / orig_file
    if not orig_file.exists():
        print(f"Original file {orig_file.name!r} doesn't exist, skipping")
        continue
    output = file.with_suffix(".temp.mkv")
    print(f"Converting {orig_file.name!r} to {output.name!r}")
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "0",
            "-stats",
            "-y",
            "-i",
            str(file),
            "-i",
            str(orig_file),
            "-map",
            "0:a",
            "-map",
            "0:v",
            "-map",
            "1:s:1",
            "-c:v",
            "copy",
            "-c:s",
            "srt",
            str(output),
        ],
        check=True,
    )
    print(f"Replacing {file.name!r} by {orig_file.name!r}")
    output.replace(file)
    print()
