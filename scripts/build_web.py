"""Build the in-browser (stlite) version of the app into docs/web/ for GitHub Pages.

Packs the app, the two pandas-only modules it imports, its data (Parquet converted to CSV, since
Pyodide has no pyarrow) and the report CSVs into docs/web/epilag_app.zip. docs/web/index.html
mounts it with stlite. Usage: python scripts/build_web.py
"""
import io
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "docs" / "web"


def main() -> None:
    WEB.mkdir(parents=True, exist_ok=True)
    out = WEB / "epilag_app.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in ["app/streamlit_app.py", "src/allocate.py", "src/thresholds.py", ".streamlit/config.toml"]:
            z.write(ROOT / path, path)
        for f in sorted((ROOT / "app" / "data").iterdir()):
            if f.suffix == ".parquet":
                buf = io.StringIO()
                pd.read_parquet(f).to_csv(buf, index=False, float_format="%.4g")
                z.writestr(f"app/data/{f.stem}.csv", buf.getvalue())
            else:
                z.write(f, f"app/data/{f.name}")
        for f in sorted((ROOT / "reports").glob("*.csv")):
            z.write(f, f"reports/{f.name}")
    print(f"{out.relative_to(ROOT)}: {out.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
