from __future__ import annotations

import urllib.request
import zipfile
from pathlib import Path

TAILLARD_URL = 'http://mistic.heig-vd.ch/taillard/problemes.dir/ordonnancement.dir/flowshop.dir/flowshop.zip'
ORLIB_URLS = {
    'flowshop1.txt': 'http://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/flowshop1.txt',
    'flowshop2.txt': 'http://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/flowshop2.txt',
}


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)


def download_taillard(save_dir: str | Path) -> Path:
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    archive_path = save_dir / 'taillard_flowshop.zip'
    _download(TAILLARD_URL, archive_path)
    with zipfile.ZipFile(archive_path, 'r') as zf:
        zf.extractall(save_dir)
    return archive_path


def download_orlibrary(save_dir: str | Path) -> list[Path]:
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for name, url in ORLIB_URLS.items():
        dest = save_dir / name
        _download(url, dest)
        outputs.append(dest)
    return outputs
