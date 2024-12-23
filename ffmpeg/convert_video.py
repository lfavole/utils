import sys
from pathlib import Path
from subprocess import run

for file in sys.argv[1:]:
    file = Path(file)
    final_location = file.with_suffix(".mkv")
    if final_location.exists():
        print(f"File {final_location.name!r} already exists, skipping")
        continue
    output = file.with_suffix(".temp.mkv")
    print(f"Converting {file.name!r} to {output.name!r}")
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
            "-r",
            "25",
            "-c:s",
            "srt",
            "-map_metadata",
            "0",
            str(output),
        ],
        check=True,
    )
    print(f"Moving {output.name!r} to {final_location.name!r}")
    output.replace(final_location)
    print()
