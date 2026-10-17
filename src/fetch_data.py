"""Download raw inputs into data/raw. Safe to re-run: skips files that exist."""
import io
import zipfile
from pathlib import Path

import requests

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"

SOURCES = {
    # DOH Epidemiology Bureau via HDX, weekly province/city cases and deaths, 2016-01 to 2021-01
    "doh_dengue_2016_2021.csv": "https://data.humdata.org/dataset/ac63a95e-7296-42fb-802b-7f7541c73e45/resource/9e839677-3ff0-44b3-992c-1a99e68df515/download/doh-epi-dengue-data-2016-2021.csv",
    # OCHA COD-AB admin boundaries attribute table (PSGC-based pcodes, centroids)
    "phl_admin_boundaries.xlsx": "https://data.humdata.org/dataset/caf116df-f984-4deb-85ca-41b349d3f313/resource/159ffd3d-679f-431c-812f-b6d6f957045e/download/phl_admin_boundaries.xlsx",
    # OCHA COD-PS population by admin-2, 2022 (PSA-based)
    "phl_admpop_adm2_2022.csv": "https://data.humdata.org/dataset/5a466c38-32a2-47de-ba36-70530505df98/resource/04cad68c-f7fb-43b0-94bf-af78eea7f982/download/phl_admpop_adm2_2022_v2.csv",
}

# UPRI-NOAH dengue-rainfall dataset (Zenodo 19448695, ODC-ODbL): weekly regional and Quezon City data.
NOAH_URL = "https://zenodo.org/api/records/19448695/files/pelitro-rcw/dengue-rainfall-dataset-v1.0.0.zip/content"
NOAH_FILES = ["Dengue-Rainfall_Dataset.xlsx", "QC_YearlyData-Barangay(CSV).csv",
              "PH_REGIONS-DC.csv", "LICENSE", "README.md"]


def download(name: str, url: str) -> None:
    out = RAW / name
    if out.exists():
        print(f"skip {name}")
        return
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)
    print(f"got  {name} ({out.stat().st_size:,} bytes)")


def download_resumable(url: str, out: Path, tries: int = 20) -> None:
    """Zenodo often drops long downloads; resume with HTTP Range until complete."""
    for _ in range(tries):
        have = out.stat().st_size if out.exists() else 0
        headers = {"Range": f"bytes={have}-"} if have else {}
        try:
            with requests.get(url, headers=headers, stream=True, timeout=120) as r:
                if r.status_code == 416:  # already complete
                    return
                r.raise_for_status()
                total = have + int(r.headers.get("Content-Length", 0))
                with out.open("ab" if have and r.status_code == 206 else "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
            if out.stat().st_size >= total:
                return
        except requests.RequestException as e:
            print(f"  resume after {type(e).__name__} at {out.stat().st_size if out.exists() else 0:,} bytes")
    raise RuntimeError("download did not complete")


def fetch_noah() -> None:
    dest = RAW / "upri_noah"
    if (dest / NOAH_FILES[0]).exists():
        print("skip upri_noah")
        return
    dest.mkdir(parents=True, exist_ok=True)
    zpath = RAW / "upri_noah.zip"
    download_resumable(NOAH_URL, zpath)
    with zipfile.ZipFile(zpath) as z:
        for info in z.infolist():
            name = Path(info.filename).name
            if name in NOAH_FILES:
                (dest / name).write_bytes(z.read(info))
    zpath.unlink()
    print("got  upri_noah")


if __name__ == "__main__":
    RAW.mkdir(parents=True, exist_ok=True)
    for name, url in SOURCES.items():
        download(name, url)
    fetch_noah()
