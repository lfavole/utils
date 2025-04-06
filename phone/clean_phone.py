# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "tqdm",
# ]
# ///
"""
Remove unnecessary files created by apps.
"""
import logging
import os
import shutil
from glob import glob
from pathlib import Path

from tqdm import tqdm

logger = logging.getLogger(__name__)


def main():
    logger.info("Removing .albumthumbs folder")
    shutil.rmtree("/storage/emulated/0/.albumthumbs", True)

    logger.info("Removing .face folder")
    shutil.rmtree("/storage/emulated/0/.face", True)

    logger.info("Removing BaiduMapSDKNew folder")
    shutil.rmtree("/storage/emulated/0/BaiduMapSDKNew", True)

    logger.info("Removing .thumbnails folder")
    shutil.rmtree("/storage/emulated/0/DCIM/.thumbnails", True)

    logger.info("Removing Termux cache")
    shutil.rmtree(Path.home() / ".cache", True)

    android = "/storage/emulated/0/Android/data"

    logger.info("Removing album thumbnails")
    shutil.rmtree(android + "/com.android.providers.media/albumthumbs", True)

    logger.info("Removing VeryFitPro logs")
    shutil.rmtree(android + "/com.veryfit2hr.second/files/VeryFitPro/log", True)

    logger.info("Removing visible cache")
    for path in tqdm(glob(android + "/*/cache") + glob(android + "/*/.cache")):
        shutil.rmtree(path)

    logger.info("Removing ads cache (il2cpp)")
    for path in tqdm(glob(android + "/*/files/il2cpp")):
        shutil.rmtree(path)

    logger.info("Removing ads cache (Unity)")
    for path in tqdm(glob(android + "/*/files/Unity")):
        shutil.rmtree(path)

    logger.info("Removing Android app logs")
    for path in tqdm(glob(android + "/**/*.log", recursive=True)):
        os.unlink(path)

    logger.info("Removing empty files and directories")

    def check(dir):
        empty = True
        for item in dir.iterdir():
            if item.is_file():
                if os.path.getsize(item) == 0:
                    print("File", item, "is empty, removing it")
                    item.unlink()
                else:
                    empty = False
            else:
                if not check(item):
                    empty = False

        if empty:
            print("Directory", dir, "is empty, removing it")
            dir.rmdir()

        return empty

    check(Path("/storage/emulated/0"))


if __name__ == "__main__":
    logging.basicConfig()
    logging.root.setLevel(logging.INFO)
    main()

