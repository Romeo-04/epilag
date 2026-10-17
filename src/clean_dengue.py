"""Clean the HDX DOH dengue file into a province-week panel.

Unit = OCHA COD-AB admin-2 (province, NCR district, or Isabela City), keyed by PSGC-based pcode.
Independent/highly urbanized cities are summed into the admin-2 unit that contains them.
Maguindanao (split in 2022) is kept as one merged unit, MAG, for the 2016-2020 data.

Output: data/processed/dengue_unit_week.parquet
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "processed"

MAGUINDANAO = "MAG"  # merged unit: PH19087 + PH19088 + PH19099 (+ Cotabato City)
MAG_PARTS = {"PH19087", "PH19088", "PH19099"}

# HDX location name -> admin-2 pcode, for names that do not match an admin-2 name directly.
NAME_TO_PCODE = {
    "ANGELES CITY": "PH03054",          # Pampanga
    "BACOLOD CITY": "PH06045",          # Negros Occidental
    "BAGUIO CITY": "PH14011",           # Benguet
    "BASILIG CITY": "PH16068",          # typo for Bislig City, Surigao del Sur
    "BAYUGAN CITY": "PH16003",          # Agusan del Sur
    "BUTUAN CITY": "PH16002",           # Agusan del Norte
    "CABADBARAN CITY": "PH16002",
    "CAGAYAN DE ORO CITY": "PH10043",   # Misamis Oriental
    "CALOOCAN CITY": "PH13075",         # NCR 3rd district
    "CEBU CITY": "PH07022",
    "COTABATO CITY": MAGUINDANAO,
    "DAGUPAN CITY": "PH01055",          # Pangasinan
    "DAVAO CITY": "PH11024",            # Davao del Sur
    "DAVAO DE ORO": "PH11082",
    "GENERAL SANTOS CITY": "PH12063",   # South Cotabato
    "ILIGAN CITY": "PH10035",           # Lanao del Norte
    "ILOILO CITY": "PH06030",
    "ISABELA CITY": "PH09097",          # own admin-2 unit
    "LAPU-LAPU CITY": "PH07022",
    "LAS PINAS CITY": "PH13076",        # NCR 4th district
    "LUCENA CITY": "PH04056",           # Quezon
    "MAGUINDANAO": MAGUINDANAO,
    "MAKATI CITY": "PH13076",
    "MALABON CITY": "PH13075",
    "MANDALUYONG CITY": "PH13074",      # NCR 2nd district
    "MANDAUE CITY": "PH07022",
    "MANILA CITY": "PH13039",           # NCR 1st district
    "MARIKINA CITY": "PH13074",
    "MUNTINLUPA CITY": "PH13076",
    "NAGA CITY": "PH05017",             # Camarines Sur (Bicol)
    "NAVOTAS CITY": "PH13075",
    "NORTH COTABATO": "PH12047",
    "NUEVA VISCAYA": "PH02050",
    "OLONGAPO CITY": "PH03071",         # Zambales
    "ORMOC CITY": "PH08037",            # Leyte
    "PARANAQUE CITY": "PH13076",
    "PASAY CITY": "PH13076",
    "PASIG CITY": "PH13074",
    "PATEROS": "PH13076",
    "PUERTO PRINCESA CITY": "PH17053",  # Palawan
    "QUEZON CITY": "PH13074",
    "SAMAR": "PH08060",
    "SAN JUAN CITY": "PH13074",
    "SANTIAGO CITY": "PH02031",         # Isabela province
    "SISQUIJOR": "PH07061",
    "SURIGAO CITY": "PH16067",
    "TACLOBAN": "PH08037",
    "TAGUIG CITY": "PH13076",
    "TANDAG CITY": "PH16068",
    "VALENZUELA CITY": "PH13075",
    "ZAMBOANGA CITY": "PH09073",        # Zamboanga del Sur
}


def load_units() -> pd.DataFrame:
    a2 = pd.read_excel(RAW / "phl_admin_boundaries.xlsx", sheet_name="phl_admin2")
    units = a2[["adm2_pcode", "adm2_name", "adm1_pcode", "adm1_name", "center_lat", "center_lon", "area_sqkm"]]
    units = units.rename(columns={"adm2_pcode": "unit_id", "adm2_name": "unit_name",
                                  "adm1_pcode": "region_id", "adm1_name": "region_name"})
    mag = units[units.unit_id.isin(MAG_PARTS)]
    merged = pd.DataFrame([{
        "unit_id": MAGUINDANAO, "unit_name": "Maguindanao (pre-2022)",
        "region_id": "PH19", "region_name": mag.region_name.iloc[0],
        "center_lat": np.average(mag.center_lat, weights=mag.area_sqkm),
        "center_lon": np.average(mag.center_lon, weights=mag.area_sqkm),
        "area_sqkm": mag.area_sqkm.sum(),
    }])
    units = pd.concat([units[~units.unit_id.isin(MAG_PARTS)], merged], ignore_index=True)
    units = units.merge(load_population(), left_on="unit_id", right_index=True, how="left")
    if units.population.isna().any():
        raise ValueError(f"no population for: {units[units.population.isna()].unit_name.tolist()}")
    return units


# NCR comes as one row in the population table. Split it by district using 2020 census city
# populations (PSA 2020 CPH; the four sums add up to the NCR total, 13,484,462).
NCR_2020 = {
    "PH13039": 1_846_513,  # Manila
    "PH13074": 4_771_371,  # Mandaluyong, Marikina, Pasig, Quezon City, San Juan
    "PH13075": 3_004_627,  # Caloocan, Malabon, Navotas, Valenzuela
    "PH13076": 3_861_951,  # Las Pinas, Makati, Muntinlupa, Paranaque, Pasay, Pateros, Taguig
}


def load_population() -> pd.Series:
    """2022 population per unit_id (OCHA COD-PS, PSA-based projections)."""
    p = pd.read_csv(RAW / "phl_admpop_adm2_2022.csv")

    def new_code(old: str) -> str:  # PH012800000 -> PH01028; ARMM (15) became BARMM (19)
        region = "19" if old[2:4] == "15" else old[2:4]
        return f"PH{region}0{old[4:6]}"

    p["unit_id"] = p.ADM2_PCODE.map(new_code)
    pop = p.groupby("unit_id").T_TL.sum()
    pop[MAGUINDANAO] = pop.pop("PH19038") + pop.pop("PH12098")  # Maguindanao + Cotabato City
    ncr = pop.pop("PH13000")
    total = sum(NCR_2020.values())
    for unit_id, n in NCR_2020.items():
        pop[unit_id] = round(ncr * n / total)
    return pop.rename("population")


def load_dengue() -> pd.DataFrame:
    d = pd.read_csv(RAW / "doh_dengue_2016_2021.csv", skiprows=[1])  # row 2 is HXL tags
    d["loc"] = d["loc"].str.strip().str.upper()
    d["week"] = pd.to_datetime(d["date"], format="%m/%d/%Y")
    return d[["loc", "week", "cases", "deaths"]]


def map_locations(d: pd.DataFrame, units: pd.DataFrame) -> pd.DataFrame:
    by_name = dict(zip(units.unit_name.str.upper(), units.unit_id))
    d["unit_id"] = d["loc"].map(lambda n: NAME_TO_PCODE.get(n, by_name.get(n)))
    unmapped = sorted(d.loc[d.unit_id.isna(), "loc"].unique())
    if unmapped:
        raise ValueError(f"unmapped locations: {unmapped}")
    return d


def build_panel(d: pd.DataFrame, units: pd.DataFrame) -> pd.DataFrame:
    weeks = pd.date_range(d.week.min(), d.week.max(), freq="W-SUN")

    # Deaths: drop impossible rows (deaths > cases) and all of 2016-2017 (systematic errors).
    bad = (d.deaths > d.cases) | (d.week.dt.year < 2018)
    d.loc[bad, "deaths"] = np.nan

    # Full loc x week grid, so a missing report stays NaN instead of silently becoming 0.
    grid = pd.MultiIndex.from_product([d["loc"].unique(), weeks], names=["loc", "week"])
    full = d.set_index(["loc", "week"]).reindex(grid).reset_index()
    full["unit_id"] = full["loc"].map(d.drop_duplicates("loc").set_index("loc").unit_id)

    panel = full.groupby(["unit_id", "week"]).agg(
        cases=("cases", lambda s: s.sum(min_count=1)),
        deaths=("deaths", lambda s: s.sum(min_count=1)),
        n_sources=("loc", "nunique"),
        n_missing=("cases", lambda s: int(s.isna().sum())),
    ).reset_index()
    # A unit-week is only trusted if every source location reported.
    panel.loc[panel.n_missing > 0, "cases"] = np.nan
    return panel.merge(units, on="unit_id", how="left")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    units = load_units()
    panel = build_panel(map_locations(load_dengue(), units), units)
    panel.to_parquet(OUT / "dengue_unit_week.parquet", index=False)
    units[units.unit_id.isin(panel.unit_id)].to_csv(OUT / "units.csv", index=False)

    print(f"units: {panel.unit_id.nunique()}, weeks: {panel.week.nunique()} "
          f"({panel.week.min().date()} to {panel.week.max().date()})")
    print(f"unit-weeks with missing cases: {panel.cases.isna().sum()} of {len(panel)}")
    print("cases per year:", panel.groupby(panel.week.dt.year).cases.sum().astype(int).to_dict())
    no_data = set(units.unit_id) - set(panel.unit_id)
    print("admin-2 units with no dengue data:", sorted(units[units.unit_id.isin(no_data)].unit_name))


if __name__ == "__main__":
    main()
