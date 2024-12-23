import logging
import os
import shutil
from pathlib import Path

from packaging.version import Version
from tqdm import tqdm

logger = logging.getLogger(__name__)


def main():
    python_dirs = list((Path.home().parent / "usr/lib").glob("python*"))
    python_dirs.sort(key=lambda x: Version(x.name.removeprefix("python")))

    if not python_dirs:
        logger.info("No Python installation to clean")
        return

    *dirs_to_remove, BASE = python_dirs
    if dirs_to_remove:
        logger.info("%d old Python installation%s found", len(dirs_to_remove), "s" if len(dirs_to_remove) == 1 else "")
        pb = tqdm(total=len(dirs_to_remove))
        for dir in dirs_to_remove:
            prefix = dir.name.removeprefix("python") + ": "
            if (dir / "site-packages").exists():
                pb.set_description(prefix + "Moving site-packages")
                pb.refresh()
                shutil.move(dir / "site-packages", BASE)
            pb.set_description(prefix + "Removing")
            shutil.rmtree(dir)
            pb.update()
        pb.close()

    logger.info("Removing __pycache__ directories")
    pb = tqdm(total=0)

    def iterate(base_dir: Path):
        dirs = []
        recursive = []
        for path in base_dir.iterdir():
            if not path.is_dir():
                continue
            if path.name == "__pycache__":
                dirs.append(path)
            else:
                recursive.append(path)

        pb.total += len(dirs)
        pb.refresh()

        for dir in dirs:
            dir_repr = str(dir.parent).replace(str(BASE), "").lstrip(os.sep) or "."
            if dir_repr.startswith("site-packages" + os.sep):
                dir_repr = "SP" + dir_repr.removeprefix("site-packages")
            if dir_repr == "site-packages":
                dir_repr = "SP"
            pb.set_description(dir_repr)
            shutil.rmtree(dir)
            pb.update()

        for dir in recursive:
            iterate(dir)

    iterate(BASE)
    pb.close()

if __name__ == "__main__":
    logging.basicConfig()
    logging.root.setLevel(logging.INFO)
    main()
