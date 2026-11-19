#!/usr/bin/env bash
# Prepare the boundary files for scripts/drill_map/build.py into one folder (default /tmp/ph-geo).
# Source: faeldon/philippines-json-maps v1.1.1 hi-res TopoJSON (PSA PSGC shapefiles, MIT licence).
# Provinces are built by merging their municipalities, which keeps far more detail than the
# per-region province files (CAR provinces drop to 5-20 points there). Needs node (npx mapshaper).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; OUT="${1:-/tmp/ph-geo}"; MS="npx -y mapshaper@0.6.102"
mkdir -p "$OUT" && cd "$OUT"
[ -d topojson ] || { curl -sL -o topo.zip https://github.com/faeldon/philippines-json-maps/releases/download/v1.1.1/topojson-hires.zip && unzip -q topo.zip; }
# provinces from municipalities, uniform 250 m simplification; Quezon City stays its own shape (it is a forecast
# unit with barangays), cut out of the Second District so the two never overlap and share one border
$MS -i topojson/provdists/hires/*.json combine-files snap snap-interval=0.00005 -merge-layers force \
    -each 'if (adm3_psgc == 1381300000) adm2_psgc = 1381300000' \
    -dissolve adm2_psgc copy-fields=adm1_psgc -filter-islands min-area=3km2 remove-empty \
    -simplify interval=250 keep-shapes -o prov_250.json format=geojson precision=0.00001
# tag each province with the forecast unit and the region it belongs to in the data (pre-2024 regions)
python3 "$HERE/tag_units.py" prov_250.json prov_tag.json
# close slivers between provinces that came from different files, then dissolve
$MS -i prov_tag.json -clean gap-fill-area=8km2 snap-interval=0.0002 -o prov_clean.json format=geojson precision=0.00001
$MS -i prov_clean.json -dissolve unit copy-fields=region -o prov_u.json format=geojson precision=0.00001
$MS -i prov_clean.json -dissolve region -o reg_u.json format=geojson precision=0.00001
$MS -i reg_u.json -simplify interval=4000 keep-shapes -filter-islands min-area=40km2 -o reg_mini.json format=geojson precision=0.001
$MS -i topojson/municities/hires/bgysubmuns-municity-1381300000.topo.0.1.json -filter-fields adm4_psgc,adm4_en -o bgy_full.json format=geojson precision=0.000001
echo "boundaries ready in $OUT"
