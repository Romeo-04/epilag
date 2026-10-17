"""EpiLag-PH: climate-informed dengue early warning for Philippine LGUs."""
import json
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP = Path(__file__).resolve().parent
DATA = APP / "data"
sys.path.insert(0, str(APP.parent / "src"))
from allocate import Action, allocate, expected_cases_8wk  # noqa: E402
from thresholds import thresholds  # noqa: E402

st.set_page_config(page_title="EpiLag-PH", page_icon=":material/coronavirus:", layout="wide")

LEVELS = ["normal", "above usual", "watch", "outbreak warning"]
LEVEL_COLOR = {"normal": "#D3DBD6", "above usual": "#F2C14E", "watch": "#EE8A2A", "outbreak warning": "#D23B30"}
LEVEL_INK = {"normal": "#2B3A33", "above usual": "#3D2F05", "watch": "#3A1E04", "outbreak warning": "#FFFFFF"}
ACCENT, ACCENT_DARK, MUTED, BAND = "#12804A", "#0B5E36", "#7E8C85", "rgba(18,128,74,0.16)"
FONT = "Plus Jakarta Sans, Segoe UI, system-ui, sans-serif"

PANELS = {
    "region_qc": {"label": {"en": "Regions + Quezon City", "fil": "Mga rehiyon + Quezon City"},
                  "note": {"en": "latest data: Dec 2025", "fil": "pinakabagong datos: Dis 2025"},
                  "geo": "region.geojson"},
    "province": {"label": {"en": "Provinces", "fil": "Mga lalawigan"},
                 "note": {"en": "historical replay: Jan 2021", "fil": "pagbabalik-tanaw: Ene 2021"},
                 "geo": "province.geojson"},
}

T = {
    "en": {
        "tagline": "Dengue early warning from rain, heat and recent cases. Act weeks before hospitals fill.",
        "nav_home": "Overview", "nav_map": "Forecast map", "nav_unit": "Area detail", "nav_proof": "Did it work?",
        "nav_budget": "Action plan", "nav_qc": "QC barangays", "nav_about": "Data & limits",
        "dataset": "Data", "horizon": "Weeks ahead", "lang": "Language",
        "mode": "Forecast", "mode_latest": "Latest", "mode_replay": "Replay a past week",
        "origin": "Forecast made in the week ending", "actual_col": "What happened",
        "replay_note": ("Replay: these forecasts were made by models trained only on earlier years, "
                        "so they show what EpiLag would have said at the time."),
        "hits": "Areas that actually crossed the epidemic threshold", "caught": "flagged in advance (watch or warning)",
        "as_of": "Forecast made from the week ending", "for_week": "for the week ending",
        "warning_n": "Outbreak warning", "watch_n": "Watch", "above_n": "Above usual", "normal_n": "Normal",
        "warning_d": "Middle forecast above the epidemic threshold", "watch_d": "Upper forecast above the epidemic threshold",
        "above_d": "Higher than usual for this time of year", "normal_d": "No unusual rise expected",
        "rank": "Priority list", "rank_sub": "Forecast cases per 100,000 people, highest first",
        "all_areas": "All areas (table)", "area": "Area", "level": "Alert level",
        "cases": "Forecast cases", "range": "Likely range", "per100k": "Per 100,000",
        "pick": "Choose an area", "history": "Weekly cases, forecasts and thresholds",
        "actual": "Reported cases", "fc4": "Forecast made 4 weeks earlier", "fcnow": "Latest forecast",
        "epi_line": "Epidemic threshold", "why": "Why this forecast",
        "why_note": "Contribution to the forecast (log scale). Positive pushes the forecast up.",
        "up": "pushes the forecast up", "down": "pulls the forecast down",
        "budget": "Budget (PHP)", "cost": "Cost per person covered (PHP, example value)",
        "effect": "Effect on cases: low / high", "plan": "Funded actions",
        "averted": "Cases averted in 8 weeks", "averted_range": "low–high",
        "qc_head": "Quezon City barangays", "qc_muted": "where to look first",
        "qc_note": ("Weekly forecasts are city-wide. Barangay data is yearly only, so the city forecast "
                    "is shared out by each barangay's share of cases in 2022-2025."),
        "hello": "Dengue outlook,", "weeks_ahead": "weeks ahead",
        "act_now": "Areas to act on now", "quiet": "Quiet week: no area needs outbreak action.",
        "replay_story": "Replay the June 2019 outbreak", "open_map": "Open the forecast map",
        "then": "What happened next", "of": "of",
        "then_line": "areas that crossed the epidemic threshold were flagged {h} weeks ahead.",
        "story_head": "Why weeks matter",
        "story": [("Rain and heat", "week 0"), ("Mosquitoes multiply", "+1–2 weeks"),
                  ("People get sick", "+2–4 weeks"), ("Hospitals report", "+4–8 weeks")],
        "story_note": ("EpiLag-PH reads this week's rain and cases and warns at week 0, "
                       "so LGUs can clean up and stock supplies before the peak."),
        "features_head": "What you can do here", "features_sub": "Each tool, what it does, and why it matters.",
        "does": "What it does", "why_h": "Why it matters", "you": "You can", "open": "Open",
        "brief_head": "Action brief", "brief_sub": "Areas on watch or warning, highest risk per 100,000 first.",
        "brief_empty": "No area is on watch or warning for this week. Keep routine surveillance; the areas above usual are listed for follow-up.",
        "peak": "peak forecast in the week ending", "prepare": "Plan for up to {n} cases in the next 8 weeks",
        "download_brief": "Download action brief", "download_plan": "Download funded plan (CSV)",
        "todo": "What to do now", "when": "When", "do": "Do this", "gives": "EpiLag-PH gives you",
        "replay_banner": "Replay mode", "result": "Result",
        "proof_head": "Did it work?", "proof_muted": "honest tests",
        "proof_sub": "Each test year was forecast only from earlier years (no peeking). Lower error is better.",
        "beat": "test sets where it beat both simple rules {h} weeks ahead",
        "caught_share": "of outbreak starts caught {h} weeks ahead (watch level)",
        "coverage": "of real values inside the likely range (target 80%)",
        "err_chart": "Average error per area-week, {h} weeks ahead", "ew_chart": "Early warning, {h} weeks ahead",
        "weather_head": "Does weather help?",
        "weather_note": ("Honest result: most of the skill comes from recent cases and season. Weather adds a modest "
                         "gain at 4-8 weeks in some years and none in others, so EpiLag works with data LGUs already have."),
        "tables": "Full results (tables)",
        "plan_head": "Action plan", "plan_muted": "where each peso works hardest",
        "plan_sub": ("Ranks where each peso prevents the most forecast cases over the next 8 weeks. "
                     "Costs are example values: replace them with your LGU's own costs."),
        "per_case": "Pesos per case averted", "people": "People reached", "spend_chart": "Spend by area",
        "plan_gives": ("EpiLag-PH supplies the forecast and the ranking; you supply the costs. "
                       "Effects are cautious ranges from published trials (Bowman et al. 2016)."),
        "city_fc": "City-wide forecast, next 8 weeks", "brgy_chart": "Expected cases in the next 8 weeks, top 20 barangays",
        "switch_qc": "This view uses the 'Regions + Quezon City' data.", "switch_btn": "Switch to Regions + Quezon City",
        "about_head": "Data & limits", "about_muted": "read before use",
    },
    "fil": {
        "tagline": "Maagang babala sa dengue mula sa ulan, init at mga bagong kaso. Kumilos bago mapuno ang ospital.",
        "nav_home": "Buod", "nav_map": "Mapa ng forecast", "nav_unit": "Detalye ng lugar", "nav_proof": "Gumana ba?",
        "nav_budget": "Plano ng aksyon", "nav_qc": "Barangay ng QC", "nav_about": "Datos at limitasyon",
        "dataset": "Datos", "horizon": "Ilang linggo pa", "lang": "Wika",
        "mode": "Forecast", "mode_latest": "Pinakabago", "mode_replay": "Balikan ang nakaraang linggo",
        "origin": "Forecast na ginawa sa linggong nagtapos noong", "actual_col": "Ang nangyari",
        "replay_note": ("Pagbabalik-tanaw: ginawa ang mga forecast na ito ng modelong sinanay lamang sa mga naunang "
                        "taon, kaya ipinapakita nito ang sasabihin sana ng EpiLag noon."),
        "hits": "Mga lugar na talagang lumampas sa threshold ng epidemya", "caught": "nababalaan nang maaga (bantayan o babala)",
        "as_of": "Forecast mula sa linggong nagtapos noong", "for_week": "para sa linggong magtatapos sa",
        "warning_n": "Babala ng outbreak", "watch_n": "Bantayan", "above_n": "Mas mataas sa karaniwan", "normal_n": "Normal",
        "warning_d": "Lampas sa threshold ng epidemya ang gitnang forecast", "watch_d": "Lampas sa threshold ang mataas na forecast",
        "above_d": "Mas mataas kaysa karaniwan sa panahong ito", "normal_d": "Walang di-pangkaraniwang pagtaas",
        "rank": "Listahan ng prayoridad", "rank_sub": "Forecast na kaso bawat 100,000 tao, pinakamataas muna",
        "all_areas": "Lahat ng lugar (talahanayan)", "area": "Lugar", "level": "Antas ng babala",
        "cases": "Forecast na kaso", "range": "Malamang na saklaw", "per100k": "Bawat 100,000",
        "pick": "Pumili ng lugar", "history": "Lingguhang kaso, forecast at threshold",
        "actual": "Naiulat na kaso", "fc4": "Forecast 4 na linggo bago", "fcnow": "Pinakabagong forecast",
        "epi_line": "Threshold ng epidemya", "why": "Bakit ganito ang forecast",
        "why_note": "Ambag sa forecast (log scale). Positibo = nagpapataas ng forecast.",
        "up": "nagpapataas ng forecast", "down": "nagpapababa ng forecast",
        "budget": "Budget (PHP)", "cost": "Gastos bawat taong maaabot (PHP, halimbawa lamang)",
        "effect": "Epekto sa kaso: mababa / mataas", "plan": "Mga gawaing popondohan",
        "averted": "Kasong maiiwasan sa 8 linggo", "averted_range": "mababa–mataas",
        "qc_head": "Mga barangay ng Quezon City", "qc_muted": "saan unang titingin",
        "qc_note": ("Ang lingguhang forecast ay para sa buong lungsod. Taunan lang ang datos ng barangay, kaya "
                    "hinati ang forecast ayon sa bahagi ng bawat barangay sa mga kaso noong 2022-2025."),
        "hello": "Lagay ng dengue,", "weeks_ahead": "linggo mula ngayon",
        "act_now": "Mga lugar na dapat kumilos na", "quiet": "Tahimik na linggo: walang lugar na kailangan ng aksyon sa outbreak.",
        "replay_story": "Balikan ang outbreak ng Hunyo 2019", "open_map": "Buksan ang mapa",
        "then": "Ang sumunod na nangyari", "of": "sa",
        "then_line": "lugar na lumampas sa threshold ang nababalaan {h} linggo bago.",
        "story_head": "Bakit mahalaga ang ilang linggo",
        "story": [("Ulan at init", "linggo 0"), ("Dumarami ang lamok", "+1–2 linggo"),
                  ("Nagkakasakit ang tao", "+2–4 linggo"), ("Nag-uulat ang ospital", "+4–8 linggo")],
        "story_note": ("Binabasa ng EpiLag-PH ang ulan at kaso ngayong linggo at nagbababala sa linggo 0, "
                       "kaya makapaglilinis at makapaghahanda ng gamit ang LGU bago ang rurok."),
        "features_head": "Ano ang magagawa mo rito", "features_sub": "Bawat kasangkapan, ang ginagawa nito, at kung bakit mahalaga.",
        "does": "Ginagawa nito", "why_h": "Bakit mahalaga", "you": "Magagawa mo", "open": "Buksan",
        "brief_head": "Buod ng aksyon", "brief_sub": "Mga lugar na bantayan o may babala, pinakamataas na panganib bawat 100,000 muna.",
        "brief_empty": "Walang lugar na bantayan o may babala ngayong linggo. Ituloy ang karaniwang pagbabantay; nakalista ang mga lugar na mas mataas sa karaniwan.",
        "peak": "rurok ng forecast sa linggong magtatapos sa", "prepare": "Maghanda para sa hanggang {n} kaso sa susunod na 8 linggo",
        "download_brief": "I-download ang buod ng aksyon", "download_plan": "I-download ang plano (CSV)",
        "todo": "Ano ang gagawin ngayon", "when": "Kailan", "do": "Gawin ito", "gives": "Ibinibigay ng EpiLag-PH",
        "replay_banner": "Pagbabalik-tanaw", "result": "Resulta",
        "proof_head": "Gumana ba?", "proof_muted": "tapat na pagsubok",
        "proof_sub": "Bawat taon ay hinulaan gamit lamang ang mga naunang taon. Mas mababang error ay mas mabuti.",
        "beat": "pagsubok kung saan tinalo nito ang dalawang simpleng tuntunin, {h} linggo bago",
        "caught_share": "ng simula ng outbreak ang nahuli {h} linggo bago (bantayan)",
        "coverage": "ng totoong bilang ang nasa loob ng malamang na saklaw (target 80%)",
        "err_chart": "Karaniwang error bawat lugar-linggo, {h} linggo bago", "ew_chart": "Maagang babala, {h} linggo bago",
        "weather_head": "Nakakatulong ba ang panahon?",
        "weather_note": ("Tapat na resulta: karamihan ng galing ay mula sa mga bagong kaso at panahon ng taon. Maliit lang ang "
                         "dagdag ng lagay ng panahon, kaya gumagana ang EpiLag sa datos na mayroon na ang LGU."),
        "tables": "Buong resulta (talahanayan)",
        "plan_head": "Plano ng aksyon", "plan_muted": "kung saan pinakamabisa ang bawat piso",
        "plan_sub": ("Inuuna kung saan pinakamaraming kaso ang naiiwasan ng bawat piso sa susunod na 8 linggo. "
                     "Halimbawa lamang ang mga gastos: palitan ng sariling gastos ng LGU."),
        "per_case": "Piso bawat kasong naiwasan", "people": "Taong maaabot", "spend_chart": "Gastos bawat lugar",
        "plan_gives": ("Ang EpiLag-PH ang nagbibigay ng forecast at pagkakasunod-sunod; ikaw ang naglalagay ng gastos. "
                       "Maingat na saklaw ang epekto, mula sa mga nailathalang pag-aaral (Bowman et al. 2016)."),
        "city_fc": "Forecast sa buong lungsod, susunod na 8 linggo", "brgy_chart": "Inaasahang kaso sa susunod na 8 linggo, nangungunang 20 barangay",
        "switch_qc": "Ginagamit ng view na ito ang datos na 'Mga rehiyon + Quezon City'.", "switch_btn": "Lumipat sa Mga rehiyon + Quezon City",
        "about_head": "Datos at limitasyon", "about_muted": "basahin bago gamitin",
    },
}

ALERT_TEXT = {
    "en": {
        "outbreak warning": "Outbreak warning: cases are forecast above the epidemic threshold. Start clean-up drives now, pre-position test kits, and alert hospitals.",
        "watch": "Watch: an outbreak is possible. Check breeding sites this week and prepare teams.",
        "above usual": "Above usual: cases are forecast higher than normal for this time of year. Keep watch.",
        "normal": "Normal: no unusual rise expected.",
    },
    "fil": {
        "outbreak warning": "Babala ng outbreak: inaasahang lalampas ang kaso sa threshold ng epidemya. Simulan na ang paglilinis, ihanda ang test kits, at abisuhan ang mga ospital.",
        "watch": "Bantayan: posible ang outbreak. Suriin ang mga pinamumugaran ng lamok ngayong linggo at ihanda ang mga team.",
        "above usual": "Mas mataas sa karaniwan: mas maraming kaso ang inaasahan kaysa karaniwan sa panahong ito. Patuloy na magbantay.",
        "normal": "Normal: walang inaasahang di-pangkaraniwang pagtaas.",
    },
}

LEVEL_NAME = {"en": dict(zip(LEVELS, ["Normal", "Above usual", "Watch", "Outbreak warning"])),
              "fil": dict(zip(LEVELS, ["Normal", "Mas mataas sa karaniwan", "Bantayan", "Babala ng outbreak"]))}

# What to do at each alert level: (when, do this, what EpiLag-PH contributes). {n} = upper 8-week forecast.
PLAYBOOK = {
    "en": {
        "outbreak warning": [
            ("Today", "Convene the local dengue task force and barangay health teams; issue a public advisory.",
             "Which areas, how many cases (with a range), and the week of the peak."),
            ("Weeks 1–2", "Run clean-up drives and cover water containers in the top barangays; larvicide where needed.",
             "The budget split by cases averted per peso, and the QC barangay shortlist."),
            ("Weeks 2–4", "Stock NS1 rapid tests and IV fluids; ask hospitals to open dengue fast lanes.",
             "The upper forecast to size supplies: up to {n} cases in 8 weeks."),
        ],
        "watch": [
            ("This week", "Inspect and destroy breeding sites; check test-kit and IV-fluid stocks.",
             "An early signal weeks ahead, before reported cases rise."),
            ("Weeks 1–3", "Prepare clean-up teams and messages so they can start within days.",
             "The likely range, so you can plan for the high case: up to {n} cases in 8 weeks."),
            ("Every week", "Re-check the forecast. If the middle forecast passes the threshold, escalate to outbreak response.",
             "A weekly update with the reasons behind any change."),
        ],
        "above usual": [
            ("This week", "Remind households of the DOH 4S: search and destroy breeding sites, self-protect, "
                          "seek early consultation, support fogging only in hotspots.",
             "Which areas are trending above their usual level."),
            ("Every week", "Watch for a move to 'watch'.", "The forecast, range and threshold in one chart."),
        ],
        "normal": [
            ("Routine", "Keep routine surveillance and community clean-ups.",
             "Confirmation that no unusual rise is expected."),
        ],
    },
    "fil": {
        "outbreak warning": [
            ("Ngayon", "Tipunin ang dengue task force at mga barangay health team; maglabas ng abiso sa publiko.",
             "Aling mga lugar, ilang kaso (may saklaw), at kailan ang rurok."),
            ("Linggo 1–2", "Maglinis at takpan ang mga lalagyan ng tubig sa mga nangungunang barangay; maglagay ng larvicide kung kailangan.",
             "Ang hati ng budget ayon sa kasong naiiwasan bawat piso, at ang listahan ng barangay sa QC."),
            ("Linggo 2–4", "Mag-imbak ng NS1 rapid test at IV fluids; hilingin sa mga ospital na magbukas ng dengue fast lane.",
             "Ang mataas na forecast para sukatin ang gamit: hanggang {n} kaso sa 8 linggo."),
        ],
        "watch": [
            ("Ngayong linggo", "Suriin at sirain ang mga pinamumugaran ng lamok; tingnan ang stock ng test kit at IV fluids.",
             "Maagang senyales ilang linggo bago tumaas ang naiulat na kaso."),
            ("Linggo 1–3", "Ihanda ang mga team sa paglilinis at ang mga mensahe para makapagsimula sa loob ng ilang araw.",
             "Ang malamang na saklaw para makapaghanda sa pinakamataas: hanggang {n} kaso sa 8 linggo."),
            ("Bawat linggo", "Balikan ang forecast. Kapag lumampas sa threshold ang gitnang forecast, itaas sa outbreak response.",
             "Lingguhang update kasama ang dahilan ng anumang pagbabago."),
        ],
        "above usual": [
            ("Ngayong linggo", "Ipaalala sa mga tahanan ang 4S ng DOH: hanapin at sirain ang pinamumugaran, protektahan ang sarili, "
                               "magpakonsulta agad, suportahan ang fogging sa hotspot lamang.",
             "Aling mga lugar ang mas mataas kaysa karaniwan."),
            ("Bawat linggo", "Bantayan kung lilipat sa 'bantayan'.", "Ang forecast, saklaw at threshold sa iisang tsart."),
        ],
        "normal": [
            ("Karaniwan", "Ituloy ang karaniwang pagbabantay at paglilinis ng komunidad.",
             "Kumpirmasyon na walang inaasahang di-pangkaraniwang pagtaas."),
        ],
    },
}

FEATURES = {
    "en": {
        "map": ("Colours every area by alert level 2–8 weeks ahead, with a likely range.",
                "Dengue rises 4–8 weeks after the rains, and case reports arrive late.",
                "Pick the areas that need action first."),
        "unit": ("Shows the forecast against the epidemic threshold, the history, and the reasons.",
                 "A clear reason makes an alert easier to trust and to defend to the mayor.",
                 "Follow a week-by-week checklist and download a brief."),
        "budget": ("Splits your budget across areas and actions by cases averted per peso.",
                   "Money is limited; acting where risk is highest prevents the most cases.",
                   "Get a funded plan you can export and present."),
        "qc": ("Turns the Quezon City forecast into a barangay shortlist.",
               "Clean-up teams work barangay by barangay.",
               "Send teams to the top barangays first."),
        "proof": ("Forecasts past years using only earlier years, against simple rules.",
                  "Trust is earned with honest tests, including what did not work.",
                  "Check hit rates and false alarms before relying on it."),
        "about": ("Lists every data source, the method and the known limits.",
                  "Decisions need to know what the numbers can and cannot say.",
                  "Cite the sources and explain the caveats."),
    },
    "fil": {
        "map": ("Kinukulayan ang bawat lugar ayon sa antas ng babala, 2–8 linggo bago, may malamang na saklaw.",
                "Tumataas ang dengue 4–8 linggo matapos ang ulan, at huli dumating ang ulat ng kaso.",
                "Piliin ang mga lugar na unang kikilusan."),
        "unit": ("Ipinapakita ang forecast laban sa threshold ng epidemya, ang kasaysayan, at ang mga dahilan.",
                 "Mas madaling pagkatiwalaan at ipagtanggol sa alkalde ang babalang may malinaw na dahilan.",
                 "Sundin ang checklist bawat linggo at i-download ang buod."),
        "budget": ("Hinahati ang budget sa mga lugar at gawain ayon sa kasong naiiwasan bawat piso.",
                   "Limitado ang pondo; mas maraming kaso ang naiiwasan kung uunahin ang pinakamapanganib.",
                   "Kumuha ng planong may pondo na maaaring i-export at iharap."),
        "qc": ("Ginagawang listahan ng barangay ang forecast ng Quezon City.",
               "Bawat barangay ang pinupuntahan ng mga team sa paglilinis.",
               "Ipadala muna ang mga team sa mga nangungunang barangay."),
        "proof": ("Hinuhulaan ang mga nakaraang taon gamit lamang ang mga naunang taon, laban sa simpleng tuntunin.",
                  "Nakukuha ang tiwala sa tapat na pagsubok, kasama ang hindi gumana.",
                  "Tingnan ang tama at maling babala bago umasa rito."),
        "about": ("Nakalista ang bawat pinagkunan ng datos, ang pamamaraan at ang mga limitasyon.",
                  "Kailangang alam ng nagpapasya kung ano ang kaya at hindi kayang sabihin ng numero.",
                  "Banggitin ang pinagkunan at ipaliwanag ang mga paalala."),
    },
}

# Lucide icons (ISC licence), drawn inline so they recolour with the text.
ICON = {
    "map": '<path d="M14.1 5.55a2 2 0 0 0 1.8 0l3.66-1.83A1 1 0 0 1 21 4.62v12.76a1 1 0 0 1-.55.9l-4.56 2.27a2 2 0 0 1-1.78 0l-4.22-2.1a2 2 0 0 0-1.78 0l-3.66 1.83A1 1 0 0 1 3 19.38V6.62a1 1 0 0 1 .55-.9l4.56-2.27a2 2 0 0 1 1.78 0z"/><path d="M15 5.76v15"/><path d="M9 3.24v15"/>',
    "unit": '<path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"/>',
    "budget": '<path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/>',
    "qc": '<path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/><path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/><path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/><path d="M10 6h4M10 10h4M10 14h4M10 18h4"/>',
    "proof": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
    "about": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>',
    "rain": '<path d="M4 14.9A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.24"/><path d="M16 14v6M8 14v6M12 16v6"/>',
    "bug": '<path d="M12 20c-3.3 0-6-2.7-6-6v-3a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v3c0 3.3-2.7 6-6 6"/><path d="M12 20v-9M9 7.13v-1a3 3 0 1 1 6 0v1M6.53 9C4.6 8.8 3 7.1 3 5M6 13H2M3 21c0-2.1 1.7-3.9 3.8-4M20.97 5c0 2.1-1.6 3.8-3.5 4M22 13h-4M17.2 17c2.1.1 3.8 1.9 3.8 4"/>',
    "sick": '<path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/>',
    "hospital": '<path d="M12 6v4M14 14h-4M14 18h-4M14 8h-4"/><path d="M18 12h2a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-9a2 2 0 0 1 2-2h2"/><path d="M18 22V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v18"/>',
    "bell": '<path d="M10.27 21a2 2 0 0 0 3.46 0"/><path d="M3.26 15.33A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.67C19.41 13.96 18 12.5 18 8A6 6 0 0 0 6 8c0 4.5-1.41 5.96-2.74 7.33"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
}
PAGE_ICON = {"home": ":material/space_dashboard:", "map": ":material/map:", "unit": ":material/monitoring:",
             "budget": ":material/payments:", "qc": ":material/location_city:", "proof": ":material/verified:",
             "about": ":material/info:"}


def icon(name: str, size: int = 20) -> str:
    return (f'<svg class="ic" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICON[name]}</svg>')


LOGO = ('<svg width="40" height="40" viewBox="0 0 40 40" aria-hidden="true"><rect width="40" height="40" rx="12" '
        f'fill="{ACCENT}"/><path d="M7 22h6l3-8 5 14 4-10 2 4h6" fill="none" stroke="#fff" stroke-width="2.6" '
        'stroke-linecap="round" stroke-linejoin="round"/></svg>')

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
:root {
  --bg: #ECEFED; --surface: #FFFFFF; --surface-2: #F3F6F4; --line: #E2E8E4; --ink: #14211B; --muted: #5B6B63;
  --accent: #12804A; --accent-dark: #0B5E36; --accent-soft: #E2F2E9; --radius: 24px;
  --ease: cubic-bezier(.2, .7, .2, 1);
}
html, body, [data-testid="stAppViewContainer"], .stMarkdown, button, input, textarea, select, label, p, li, h1, h2, h3, h4 {
  font-family: 'Plus Jakarta Sans', 'Segoe UI', system-ui, sans-serif !important;
}
[data-testid="stAppViewContainer"] { background: var(--bg); }
[data-testid="stHeader"] { background: transparent; height: 0; }
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stSidebarNav"] { display: none; }
[data-testid="stMainBlockContainer"] { max-width: 1400px; padding: 20px clamp(16px, 3vw, 40px) 64px; }
[data-testid="stMainBlockContainer"] > div { animation: fade .45s var(--ease) both; }
h1, h2, h3 { color: var(--ink); letter-spacing: -0.02em; }
p, li { color: var(--ink); }

/* cards */
div[class*="st-key-card"], div[class*="st-key-feat"] {
  background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius);
  padding: 22px 24px; box-shadow: 0 1px 2px rgba(16, 24, 20, .04);
  animation: rise .6s var(--ease) both; transition: box-shadow .25s var(--ease), transform .25s var(--ease);
}
div[class*="st-key-feat"]:hover { transform: translateY(-4px); box-shadow: 0 18px 40px -18px rgba(11, 94, 54, .35); }
[data-testid="stColumn"]:nth-child(2) [class*="st-key-"] { animation-delay: .08s; }
[data-testid="stColumn"]:nth-child(3) [class*="st-key-"] { animation-delay: .16s; }
[data-testid="stColumn"]:nth-child(4) [class*="st-key-"] { animation-delay: .24s; }

/* green hero card */
div[class*="st-key-hero"] {
  position: relative; overflow: hidden; border-radius: var(--radius); padding: 26px 28px; color: #fff;
  background: radial-gradient(120% 120% at 100% 0%, #1FA463 0%, #12804A 45%, #0A4F2E 100%);
  box-shadow: 0 24px 48px -24px rgba(11, 94, 54, .6); animation: rise .6s var(--ease) both;
}
div[class*="st-key-hero"]::before, div[class*="st-key-hero"]::after {
  content: ""; position: absolute; border-radius: 50%; border: 1.5px solid rgba(255, 255, 255, .14); pointer-events: none;
}
div[class*="st-key-hero"]::before { width: 340px; height: 340px; right: -120px; top: -150px; animation: spin 24s linear infinite; }
div[class*="st-key-hero"]::after { width: 220px; height: 220px; right: -40px; top: -60px; border-style: dashed; animation: spin 18s linear infinite reverse; }
div[class*="st-key-hero"] p, div[class*="st-key-hero"] span, div[class*="st-key-hero"] div { color: #fff; }
div[class*="st-key-hero"] [data-testid="stPageLink"] a, div[class*="st-key-hero"] button {
  background: #fff !important; border-radius: 999px; padding: 6px 16px; border: 0; width: fit-content;
}
div[class*="st-key-hero"] [data-testid="stPageLink"] a *, div[class*="st-key-hero"] button * { color: var(--accent-dark) !important; font-weight: 700; }

/* top bar + pill navigation */
div.st-key-topbar { background: var(--surface); border-radius: 999px; padding: 10px 14px 10px 18px; border: 1px solid var(--line);
  box-shadow: 0 1px 2px rgba(16, 24, 20, .04); margin-bottom: 8px; animation: drop .5s var(--ease) both; }
div.st-key-topbar [data-testid="stHorizontalBlock"] { align-items: center; }
div.st-key-topnav { background: var(--surface-2); border-radius: 999px; padding: 4px; }
div.st-key-topnav [data-testid="stHorizontalBlock"] { gap: 2px; flex-wrap: nowrap; }
div.st-key-topnav [data-testid="stPageLink"] a { border-radius: 999px; padding: 7px 10px; justify-content: center;
  transition: background .2s var(--ease), box-shadow .2s var(--ease); white-space: nowrap; }
div.st-key-topnav [data-testid="stPageLink"] a:hover { background: rgba(255, 255, 255, .7); }
div.st-key-topnav [data-testid="stPageLink"] a p { font-size: 13.5px; font-weight: 500; color: var(--muted); }
div[class*="st-key-navon"] [data-testid="stPageLink"] a { background: var(--surface); box-shadow: 0 2px 8px rgba(16, 24, 20, .08); }
div[class*="st-key-navon"] [data-testid="stPageLink"] a p, div[class*="st-key-navon"] [data-testid="stPageLink"] a span { color: var(--ink); font-weight: 700; }
.brand { display: flex; align-items: center; gap: 10px; font-weight: 800; font-size: 20px; color: var(--ink); letter-spacing: -.02em; }
.brand small { display: block; font-size: 12px; font-weight: 500; color: var(--muted); letter-spacing: 0; }

/* segmented controls built from radios (both the newer react-aria and older baseweb markup) */
[data-testid="stRadio"] [role="radiogroup"] { background: var(--surface-2); border-radius: 999px; padding: 4px; gap: 2px; display: inline-flex; flex-wrap: nowrap; }
[data-testid="stRadio"] label:is([data-baseweb="radio"], [data-testid="stRadioOption"]) { margin: 0; padding: 6px 14px; border-radius: 999px; cursor: pointer;
  transition: background .2s var(--ease), color .2s var(--ease), box-shadow .2s var(--ease); white-space: nowrap; }
[data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child,
[data-testid="stRadio"] label[data-testid="stRadioOption"] > div > div:not([data-testid="stMarkdownContainer"]) { display: none; }
[data-testid="stRadio"] label:is([data-baseweb="radio"], [data-testid="stRadioOption"]):hover { background: rgba(18, 128, 74, .08); }
[data-testid="stRadio"] label:is([data-baseweb="radio"], [data-testid="stRadioOption"]):has(input:checked) { background: var(--accent); box-shadow: 0 4px 10px -4px rgba(20, 33, 27, .3); }
[data-testid="stRadio"] label:has(input:checked) p { color: #fff; font-weight: 600; }
[data-testid="stRadio"] label:has(input:focus-visible) { outline: 3px solid rgba(18, 128, 74, .35); outline-offset: 1px; }
[data-testid="stRadio"] label p { font-size: 14px; }
[data-testid="stWidgetLabel"] p { font-size: 12px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: .06em; }
div.st-key-ctx { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); padding: 12px 20px 14px;
  animation: drop .55s var(--ease) .05s both; }
div.st-key-topnav [data-testid="stColumn"] { flex: 0 1 auto !important; width: auto !important; min-width: 0; }
[data-testid="stToolbar"], [data-testid="stDecoration"] { display: none; }

/* page titles */
.hero-title { font-size: clamp(30px, 3.4vw, 46px); font-weight: 600; letter-spacing: -.035em; line-height: 1.1; color: var(--ink); margin: 18px 0 4px; }
.hero-title span { color: #8A9891; font-weight: 500; }
.hero-sub { color: var(--muted); font-size: 15px; margin-bottom: 8px; }
.kicker { font-size: 12px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
.card-title { display: flex; align-items: center; gap: 12px; font-size: 17px; font-weight: 700; color: var(--ink); }
.card-title .ic-wrap { width: 40px; height: 40px; border-radius: 50%; background: var(--surface-2); display: grid; place-items: center; color: var(--ink); flex: none; }
.card-sub { color: var(--muted); font-size: 13px; margin: 2px 0 12px 52px; }
.card-sub.flush { margin-left: 0; }

/* numbers */
@property --n { syntax: '<integer>'; inherits: false; initial-value: 0; }
.count { --n: var(--to); counter-reset: n var(--n); animation: count 1.4s var(--ease) both; }
.count::after { content: counter(n); }
@keyframes count { from { --n: 0; } to { --n: var(--to); } }
.big { font-size: 64px; font-weight: 700; letter-spacing: -.04em; line-height: 1; }
.mid { font-size: 34px; font-weight: 700; letter-spacing: -.03em; line-height: 1.1; color: var(--ink); }
.mid small { font-size: 18px; color: #8A9891; font-weight: 600; }
.chip { display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; border-radius: 999px; font-size: 13px; font-weight: 600;
  background: rgba(255, 255, 255, .16); color: #fff; margin: 4px 6px 0 0; }
.dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; flex: none; }
.pill { display: inline-flex; align-items: center; gap: 6px; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; white-space: nowrap; }
.pulse { position: relative; }
.pulse::after { content: ""; position: absolute; inset: 0; border-radius: inherit; box-shadow: 0 0 0 0 rgba(210, 59, 48, .55); animation: pulse 1.8s ease-out infinite; }

/* KPI tiles */
.kpi { display: flex; flex-direction: column; gap: 6px; }
.kpi .lab { display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 600; color: var(--muted); }
.kpi .val { font-size: 40px; font-weight: 700; letter-spacing: -.03em; color: var(--ink); line-height: 1; }
.kpi .desc { font-size: 12.5px; color: var(--muted); }

/* priority rows */
.rows { display: flex; flex-direction: column; gap: 6px; }
.row { display: grid; grid-template-columns: 28px minmax(0, 1.4fr) auto minmax(0, 1fr) 64px; align-items: center; gap: 12px;
  padding: 10px 12px; border-radius: 16px; transition: background .2s var(--ease); animation: rise .5s var(--ease) both; }
.row:hover { background: var(--surface-2); }
.row .rk { width: 28px; height: 28px; border-radius: 50%; background: var(--surface-2); display: grid; place-items: center; font-size: 12px; font-weight: 700; color: var(--muted); }
.row .nm { font-weight: 600; font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.row .nm small { display: block; font-weight: 500; color: var(--muted); font-size: 12px; }
.bar { height: 10px; border-radius: 999px; background: var(--surface-2); overflow: hidden; }
.bar i { display: block; height: 100%; border-radius: 999px; transform-origin: left; animation: grow 1s var(--ease) both;
  background: repeating-linear-gradient(135deg, rgba(255,255,255,.25) 0 4px, transparent 4px 8px), var(--c, var(--accent)); }
.row .num { text-align: right; font-weight: 700; font-size: 14px; }

/* feature cards */
.feat-ic { width: 48px; height: 48px; border-radius: 16px; display: grid; place-items: center; background: var(--accent-soft); color: var(--accent-dark);
  transition: transform .3s var(--ease); }
div[class*="st-key-feat"]:hover .feat-ic { transform: rotate(-8deg) scale(1.08); }
.feat-name { font-size: 18px; font-weight: 700; margin: 14px 0 10px; color: var(--ink); }
.feat dl { margin: 0; display: grid; gap: 8px; }
.feat dt { font-size: 11px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
.feat dd { margin: 0; font-size: 14px; color: var(--ink); line-height: 1.45; }
.feat dd.you { color: var(--accent-dark); font-weight: 600; }
div[class*="st-key-feat"] [data-testid="stPageLink"] a { border-radius: 999px; background: var(--surface-2); padding: 6px 14px; width: fit-content; transition: background .2s; }
div[class*="st-key-feat"] [data-testid="stPageLink"] a:hover { background: var(--accent-soft); }

/* story timeline */
.story { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; position: relative; margin-top: 18px; }
.story::before { content: ""; position: absolute; left: 24px; right: 24px; top: 24px; height: 4px; border-radius: 4px; background: var(--surface-2); }
.story::after { content: ""; position: absolute; left: 24px; right: 24px; top: 24px; height: 4px; border-radius: 4px; transform-origin: left;
  background: linear-gradient(90deg, var(--accent), #F2C14E, #EE8A2A, #D23B30); animation: grow 2.2s var(--ease) .3s both; }
.step { position: relative; z-index: 1; animation: rise .6s var(--ease) both; }
.step:nth-child(2) { animation-delay: .5s; } .step:nth-child(3) { animation-delay: .9s; } .step:nth-child(4) { animation-delay: 1.3s; }
.step .bub { width: 52px; height: 52px; border-radius: 50%; background: var(--surface); border: 2px solid var(--line); display: grid; place-items: center; color: var(--ink); }
.step:first-child .bub { background: var(--accent); border-color: var(--accent); color: #fff; box-shadow: 0 0 0 6px var(--accent-soft); }
.step b { display: block; margin-top: 10px; font-size: 14px; }
.step span { font-size: 12.5px; color: var(--muted); }
.warn-here { display: inline-flex; align-items: center; gap: 6px; margin-top: 14px; padding: 6px 12px; border-radius: 999px; background: var(--accent-soft); color: var(--accent-dark); font-size: 13px; font-weight: 600; }

/* action brief + checklist */
.brief { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.3fr); gap: 16px; padding: 14px 4px; border-top: 1px solid var(--line); animation: rise .5s var(--ease) both; }
.brief:first-child { border-top: 0; }
.brief .nm { font-weight: 700; font-size: 15px; }
.brief .meta { color: var(--muted); font-size: 13px; margin-top: 4px; }
.brief .next { font-size: 13.5px; line-height: 1.45; }
.brief .next b { color: var(--accent-dark); }
.todo { display: grid; grid-template-columns: 110px minmax(0, 1.2fr) minmax(0, 1fr); gap: 14px; padding: 14px 0; border-top: 1px solid var(--line); animation: rise .5s var(--ease) both; }
.todo:nth-child(2) { animation-delay: .1s; } .todo:nth-child(3) { animation-delay: .2s; } .todo:nth-child(4) { animation-delay: .3s; }
.todo.head { border-top: 0; padding-top: 0; font-size: 11px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
.todo .when { display: inline-flex; align-items: center; gap: 6px; font-weight: 700; font-size: 13px; color: var(--ink); }
.todo .do { font-size: 14px; line-height: 1.45; }
.todo .gives { font-size: 13.5px; line-height: 1.45; color: var(--accent-dark); background: var(--accent-soft); border-radius: 12px; padding: 8px 12px; }
.alertbar { display: flex; gap: 12px; align-items: flex-start; padding: 14px 16px; border-radius: 16px; font-size: 14px; line-height: 1.45; }
.legend { display: flex; flex-wrap: wrap; gap: 14px; font-size: 13px; color: var(--muted); margin-top: 8px; }
.legend span { display: inline-flex; align-items: center; gap: 6px; }
.why-list { display: grid; gap: 8px; margin-bottom: 8px; }
.why-list div { display: flex; gap: 10px; align-items: center; font-size: 14px; }

/* widgets */
.stButton button, .stDownloadButton button { border-radius: 999px; font-weight: 600; transition: transform .15s var(--ease), box-shadow .2s var(--ease); }
.stButton button:hover, .stDownloadButton button:hover { transform: translateY(-1px); box-shadow: 0 8px 18px -10px rgba(20, 33, 27, .35); }
[data-testid="stDataFrame"] { border-radius: 16px; overflow: hidden; }
[data-testid="stExpander"] details { border-radius: 16px; border-color: var(--line); background: var(--surface); }
[data-testid="stPlotlyChart"] { animation: fade .8s var(--ease) both; }
div[data-baseweb="select"] > div, [data-testid="stNumberInputContainer"] { border-radius: 12px; }

@keyframes rise { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }
@keyframes drop { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: none; } }
@keyframes fade { from { opacity: 0; } to { opacity: 1; } }
@keyframes grow { from { transform: scaleX(0); } to { transform: scaleX(1); } }
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(210, 59, 48, .55); } 100% { box-shadow: 0 0 0 10px rgba(210, 59, 48, 0); } }
@media (max-width: 900px) { .story { grid-template-columns: repeat(2, 1fr); } .story::before, .story::after { display: none; }
  .brief, .todo { grid-template-columns: 1fr; } .row { grid-template-columns: 28px minmax(0, 1fr) auto 56px; } .row .bar { display: none; } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; transition: none !important; } }
</style>
"""


# ------------------------------------------------------------------ data

def read_table(stem: Path) -> pd.DataFrame:
    """Parquet locally; CSV in the in-browser (stlite) build, which has no pyarrow."""
    if stem.with_suffix(".parquet").exists():
        return pd.read_parquet(stem.with_suffix(".parquet"))
    df = pd.read_csv(stem.with_suffix(".csv"))
    for col in ("week", "target_week"):
        if col in df:
            df[col] = pd.to_datetime(df[col])
    return df


@st.cache_data
def load(panel: str) -> dict:
    d = {name: read_table(DATA / f"{panel}_{name}")
         for name in ("forecast", "drivers", "thresholds", "history", "backtest")}
    d["geo"] = json.loads((DATA / PANELS[panel]["geo"]).read_text())
    return d


@st.cache_data
def load_reports(panel: str) -> dict:
    rep = APP.parent / "reports"
    files = {"backtest": f"backtest_{panel}.csv", "backtest_noweather": f"backtest_{panel}_noweather.csv",
             "alerts": f"alerts_{panel}.csv"}
    return {name: pd.read_csv(rep / f) for name, f in files.items() if (rep / f).exists()}


def fmt(x: float) -> str:
    return f"{x:,.0f}"


def alert_level(q50: pd.Series, q90: pd.Series, alert: pd.Series, epidemic: pd.Series) -> pd.Series:
    lvl = pd.Series(LEVELS[0], index=q50.index)
    lvl[q50 > alert] = LEVELS[1]
    lvl[q90 > epidemic] = LEVELS[2]
    lvl[q50 > epidemic] = LEVELS[3]
    return lvl


@st.cache_data
def replay_origins(panel: str) -> pd.Series:
    """Weeks from which both the 4- and 8-week out-of-sample forecasts exist."""
    b = load(panel)["backtest"]
    b = b.assign(origin=b.target_week - pd.to_timedelta(b.horizon * 7, unit="D"))
    both = b.groupby("origin").horizon.nunique()
    return pd.Series(sorted(both[both == 2].index))


@st.cache_data
def replay_forecast(panel: str, origin: pd.Timestamp) -> pd.DataFrame:
    """Out-of-sample forecasts made at a past week (models trained only on earlier years),
    shaped like the latest-forecast table, plus what actually happened."""
    d = load(panel)
    b = d["backtest"].assign(origin=lambda x: x.target_week - pd.to_timedelta(x.horizon * 7, unit="D"))
    f = b[b.origin == origin].copy()
    static = d["forecast"].drop_duplicates("unit_id")[["unit_id", "unit_name", "population"]]
    f = f.merge(static, on="unit_id").rename(columns={"origin": "week"})
    f["woy"] = f.target_week.dt.isocalendar().week.astype(int).clip(upper=52)
    # Thresholds from years before the forecast, as the backtest used.
    hist = d["history"][d["history"].week < f"{origin.year}-01-01"]
    thr = _thresholds(hist)
    f = f.merge(thr, on=["unit_id", "woy"], how="left")
    f["level"] = alert_level(f.q50, f.q90, f.alert, f.epidemic)
    f["actual_level"] = alert_level(f.actual, f.actual, f.alert, f.epidemic)
    f["q50_per100k"] = f.q50 / f.population * 1e5
    return f


def _thresholds(history: pd.DataFrame) -> pd.DataFrame:
    return thresholds(history)


# ------------------------------------------------------------------ design helpers

def html(s: str) -> None:
    st.markdown(s, unsafe_allow_html=True)


def hero(title: str, muted: str, sub: str = "") -> None:
    html(f'<div class="hero-title">{title} <span>{muted}</span></div>' + (f'<div class="hero-sub">{sub}</div>' if sub else ""))


def card_title(name: str, title: str, sub: str = "") -> None:
    html(f'<div class="card-title"><span class="ic-wrap">{icon(name)}</span>{title}</div>'
         + (f'<div class="card-sub">{sub}</div>' if sub else '<div style="height:12px"></div>'))


def pill(level: str) -> str:
    pulse = " pulse" if level == "outbreak warning" else ""
    return (f'<span class="pill{pulse}" style="background:{LEVEL_COLOR[level]};color:{LEVEL_INK[level]}">'
            f'{LEVEL_NAME[lang][level]}</span>')


def count(n: int) -> str:
    return f'<span class="count" style="--to:{int(n)}"></span>'


def style(fig: go.Figure, height: int, **layout) -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=dict(family=FONT, color="#14211B", size=13),
                      hoverlabel=dict(font_family=FONT, bgcolor="#14211B", font_color="#fff", bordercolor="#14211B"),
                      legend=dict(orientation="h", y=-0.18, x=0, font=dict(size=12)), **layout)
    fig.update_xaxes(gridcolor="#EDF1EE", linecolor="#E2E8E4")
    fig.update_yaxes(gridcolor="#EDF1EE", linecolor="#E2E8E4")
    return fig


def brief_table(fc_all: pd.DataFrame, fc_now: pd.DataFrame) -> pd.DataFrame:
    """Per area: level at the chosen horizon, peak week, and the 8-week totals used to size supplies."""
    peak = fc_all.loc[fc_all.groupby("unit_id").q50.idxmax(), ["unit_id", "target_week"]].rename(columns={"target_week": "peak_week"})
    tot = expected_cases_8wk(fc_all)[["unit_id", "cases_mid", "cases_high"]]
    return fc_now.merge(peak, on="unit_id").merge(tot, on="unit_id").sort_values(["level", "q50_per100k"], ascending=False)


def brief_markdown(rows: pd.DataFrame) -> str:
    lines = [f"# EpiLag-PH action brief", "",
             f"{t['as_of']} {fc_h.week.max():%d %b %Y} · {PANELS[panel]['label'][lang]} · {horizon} {t['weeks_ahead']}", ""]
    for r in rows.itertuples():
        lines += [f"## {r.unit_name}: {LEVEL_NAME[lang][r.level]}",
                  f"- {t['cases']}: {fmt(r.q50)} ({t['range']} {fmt(r.q10)}–{fmt(r.q90)}), {t['for_week']} {r.target_week:%d %b %Y}",
                  f"- {t['prepare'].format(n=fmt(r.cases_high))}"]
        lines += [f"- **{when}**: {do}" for when, do, _ in PLAYBOOK[lang][r.level]]
        lines.append("")
    lines.append("Source: EpiLag-PH (github.com/Romeo-04/epilag). Forecasts carry uncertainty; see the likely range.")
    return "\n".join(lines)


# ------------------------------------------------------------------ pages

def page_home():
    origin_d, target_d = fc_h.week.max(), fc_h.target_week.max()
    hero(t["hello"], f"{horizon} {t['weeks_ahead']}",
         f"{t['as_of']} {origin_d:%d %b %Y} · {t['for_week']} {target_d:%d %b %Y} · {PANELS[panel]['label'][lang]}")
    counts = fc_h.level.value_counts()
    n_warn, n_watch, n_above = (int(counts.get(lv, 0)) for lv in LEVELS[:0:-1])

    left, right = st.columns([1, 1.6], gap="medium")
    with left, st.container(key="hero_status"):
        html(f'<div class="kicker" style="color:rgba(255,255,255,.75)">{t["act_now"]}</div>'
             f'<div class="big" style="margin:10px 0 6px">{count(n_warn + n_watch)}</div>'
             f'<span class="chip"><i class="dot" style="background:{LEVEL_COLOR["outbreak warning"]}"></i>{n_warn} {t["warning_n"]}</span>'
             f'<span class="chip"><i class="dot" style="background:{LEVEL_COLOR["watch"]}"></i>{n_watch} {t["watch_n"]}</span>'
             f'<span class="chip"><i class="dot" style="background:{LEVEL_COLOR["above usual"]}"></i>{n_above} {t["above_n"]}</span>')
        if mode == "replay":
            crossed = fc_h[fc_h.actual_level == LEVELS[3]]
            flagged = int(crossed.level.isin(LEVELS[2:]).sum())
            html(f'<div style="margin-top:18px;font-size:14px;opacity:.85">{t["then"]}</div>'
                 f'<div style="font-size:22px;font-weight:700;margin:2px 0 14px">{flagged} {t["of"]} {len(crossed)} '
                 f'<span style="font-size:15px;font-weight:500">{t["then_line"].format(h=horizon)}</span></div>')
        elif n_warn + n_watch == 0:
            html(f'<div style="margin:16px 0 12px;font-size:15px;opacity:.9">{t["quiet"]}</div>')
            st.button(t["replay_story"], icon=":material/history:", on_click=go_replay_story, key="story_btn")
        else:
            html('<div style="height:14px"></div>')
        st.page_link(PAGES["map"], label=t["open_map"], icon=":material/arrow_outward:")

    with right, st.container(key="card_story"):
        card_title("clock", t["story_head"])
        steps = "".join(f'<div class="step"><div class="bub">{icon(ic, 22)}</div><b>{a}</b><span>{b}</span></div>'
                        for (a, b), ic in zip(t["story"], ["rain", "bug", "sick", "hospital"]))
        html(f'<div class="story">{steps}</div><div class="warn-here">{icon("bell", 16)}{t["story_note"]}</div>')

    html(f'<div class="hero-title" style="font-size:28px;margin-top:28px">{t["features_head"]} <span>{t["features_sub"]}</span></div>')
    keys = ["map", "unit", "budget", "qc", "proof", "about"]
    for row in (keys[:3], keys[3:]):
        for col, key in zip(st.columns(3, gap="medium"), row):
            does, why, you = FEATURES[lang][key]
            with col, st.container(key=f"feat_{key}"):
                html(f'<div class="feat"><div class="feat-ic">{icon(key, 24)}</div><div class="feat-name">{t["nav_" + key]}</div>'
                     f'<dl><dt>{t["does"]}</dt><dd>{does}</dd><dt>{t["why_h"]}</dt><dd>{why}</dd>'
                     f'<dt>{t["you"]}</dt><dd class="you">{you}</dd></dl></div>')
                st.page_link(PAGES[key], label=t["open"], icon=":material/arrow_outward:")

    rows = brief_table(fc, fc_h)
    act = rows[rows.level.isin(LEVELS[2:])].head(6)
    with st.container(key="card_brief"):
        card_title("bell", t["brief_head"], t["brief_sub"])
        shown = act if not act.empty else rows[rows.level == LEVELS[1]].head(3)
        if act.empty:
            html(f'<div class="alertbar" style="background:var(--accent-soft)">{icon("check")}{t["brief_empty"]}</div>')
        items = []
        for r in shown.itertuples():
            when, do, _ = PLAYBOOK[lang][r.level][0]
            items.append(f'<div class="brief"><div><div class="nm">{r.unit_name} &nbsp;{pill(r.level)}</div>'
                         f'<div class="meta">{t["cases"]}: <b>{fmt(r.q50)}</b> ({fmt(r.q10)}–{fmt(r.q90)}) · '
                         f'{t["peak"]} {r.peak_week:%d %b}</div></div>'
                         f'<div class="next"><b>{when}:</b> {do}<div class="meta">{t["prepare"].format(n=fmt(r.cases_high))}</div></div></div>')
        html("".join(items))
        if not shown.empty:
            st.download_button(t["download_brief"], brief_markdown(shown), file_name="epilag_action_brief.md",
                               mime="text/markdown", icon=":material/download:", key="dl_brief")


def page_map():
    hero(t["nav_map"], f"{horizon} {t['weeks_ahead']}",
         f"{t['as_of']} {fc_h.week.max():%d %b %Y} · {t['for_week']} {fc_h.target_week.max():%d %b %Y}")
    if mode == "replay":
        crossed = fc_h[fc_h.actual_level == LEVELS[3]]
        flagged = int(crossed.level.isin(LEVELS[2:]).sum())
        with st.container(key="hero_replay"):
            html(f'<div class="kicker" style="color:rgba(255,255,255,.75)">{t["replay_banner"]} · {t["result"]}</div>'
                 f'<div class="replay-result" data-crossed="{len(crossed)}" data-flagged="{flagged}" '
                 f'style="font-size:30px;font-weight:700;margin:6px 0 4px">{count(flagged)}&nbsp;{t["of"]} {len(crossed)}</div>'
                 f'<div style="font-size:15px">{t["hits"]}: {len(crossed)} · {flagged} {t["caught"]}.</div>'
                 f'<div style="font-size:13px;opacity:.8;margin-top:6px">{t["replay_note"]}</div>')

    counts = fc_h.level.value_counts()
    for col, lvl, key in zip(st.columns(4, gap="medium"), reversed(LEVELS), ["warning", "watch", "above", "normal"]):
        with col, st.container(key=f"card_kpi_{key}"):
            pulse = " pulse" if lvl == "outbreak warning" and counts.get(lvl, 0) else ""
            html(f'<div class="kpi"><div class="lab"><i class="dot{pulse}" style="background:{LEVEL_COLOR[lvl]};width:12px;height:12px"></i>'
                 f'{t[key + "_n"]}</div><div class="val">{count(counts.get(lvl, 0))}</div><div class="desc">{t[key + "_d"]}</div></div>')

    geo_ids = {f["id"] for f in D["geo"]["features"]}
    on_map = fc_h[fc_h.unit_id.isin(geo_ids)]
    hover = on_map[["unit_name"]].astype(str).assign(
        level=on_map.level.astype(str).map(LEVEL_NAME[lang]),
        q50=on_map.q50.round(0).astype(int).astype(str), q10=on_map.q10.round(0).astype(int).astype(str),
        q90=on_map.q90.round(0).astype(int).astype(str))
    # Tile-based choropleth: unlike go.Choropleth it does not depend on polygon winding order.
    fig = go.Figure(go.Choroplethmap(
        geojson=D["geo"], locations=on_map.unit_id, z=on_map.level.cat.codes,
        zmin=0, zmax=3, colorscale=[[i / 3, LEVEL_COLOR[l]] for i, l in enumerate(LEVELS)],
        showscale=False, marker_line_color="white", marker_line_width=0.8, marker_opacity=0.92,
        customdata=hover.values,
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>%{customdata[2]} (%{customdata[3]}–%{customdata[4]})<extra></extra>",
    ))
    style(fig, 600)
    fig.update_layout(map=dict(style="carto-positron", center=dict(lat=12.0, lon=122.3), zoom=4.75))
    left, right = st.columns([1.5, 1], gap="medium")
    with left, st.container(key="card_map"):
        card_title("map", t["nav_map"], f"{t['for_week']} {fc_h.target_week.max():%d %b %Y}")
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        html('<div class="legend">' + "".join(f'<span><i class="dot" style="background:{LEVEL_COLOR[l]}"></i>{LEVEL_NAME[lang][l]}</span>'
                                              for l in LEVELS) + "</div>")
    with right, st.container(key="card_rank"):
        card_title("bell", t["rank"], t["rank_sub"])
        table = fc_h.sort_values(["q50_per100k"], ascending=False)
        top, peak = table.head(12), max(table.q50_per100k.max(), 1e-9)
        rows = []
        for i, r in enumerate(top.itertuples(), 1):
            sub = f"{fmt(r.q50)} ({fmt(r.q10)}–{fmt(r.q90)})"
            if mode == "replay" and pd.notna(r.actual):
                sub += f" → {fmt(r.actual)}"
            rows.append(f'<div class="row" style="animation-delay:{i * 0.04:.2f}s"><span class="rk">{i}</span>'
                        f'<div class="nm">{r.unit_name}<small>{sub}</small></div>{pill(r.level)}'
                        f'<div class="bar"><i style="width:{r.q50_per100k / peak * 100:.0f}%;--c:{LEVEL_COLOR[r.level] if r.level != "normal" else ACCENT}"></i></div>'
                        f'<span class="num">{r.q50_per100k:.1f}</span></div>')
        html('<div class="rows">' + "".join(rows) + "</div>")
    with st.expander(t["all_areas"], icon=":material/table:"):
        view = pd.DataFrame({
            t["area"]: table.unit_name, t["level"]: table.level.astype(str).map(LEVEL_NAME[lang]),
            t["cases"]: table.q50.round(0).astype(int),
            t["range"]: table.q10.round(0).astype(int).astype(str) + "–" + table.q90.round(0).astype(int).astype(str),
            t["per100k"]: table.q50_per100k.round(1),
        })
        if mode == "replay":
            view[t["actual_col"]] = table.actual.round(0).astype("Int64").astype(str) + " · " + table.actual_level
        st.dataframe(view, hide_index=True, width="stretch")


def threshold_series(unit_id: str, weeks: pd.Series) -> pd.Series:
    # In replay, thresholds come only from years before the replayed year (as in the backtest).
    table = _thresholds(D["history"][D["history"].week < f"{origin.year}-01-01"]) if mode == "replay" else D["thresholds"]
    thr = table[table.unit_id == unit_id].set_index("woy").epidemic
    woy = weeks.dt.isocalendar().week.astype(int).clip(upper=52)
    return woy.map(thr).values


def page_unit():
    names = fc_h.sort_values("q50_per100k", ascending=False)
    hero(t["nav_unit"], f"{horizon} {t['weeks_ahead']}", t["tagline"])
    unit_name = st.selectbox(t["pick"], names.unit_name)
    unit_id = names[names.unit_name == unit_name].unit_id.iloc[0]
    row = fc_h[fc_h.unit_id == unit_id].iloc[0]
    rows = brief_table(fc[fc.unit_id == unit_id], fc_h[fc_h.unit_id == unit_id]).iloc[0]

    a, b, c = st.columns([1.2, 1, 1], gap="medium")
    with a, st.container(key="hero_unit"):
        html(f'<div class="kicker" style="color:rgba(255,255,255,.75)">{unit_name} · {t["level"]}</div>'
             f'<div style="font-size:30px;font-weight:700;margin:8px 0 6px">{LEVEL_NAME[lang][row.level]}</div>'
             f'<div style="font-size:14px;opacity:.9">{ALERT_TEXT[lang][row.level]}</div>')
    with b, st.container(key="card_u_cases"):
        html(f'<div class="kpi"><div class="lab">{t["cases"]} · {horizon} wk</div><div class="val">{fmt(row.q50)}</div>'
             f'<div class="desc">{t["range"]}: {fmt(row.q10)}–{fmt(row.q90)} · {t["for_week"]} {row.target_week:%d %b %Y}</div></div>')
    with c, st.container(key="card_u_rate"):
        html(f'<div class="kpi"><div class="lab">{t["per100k"]}</div><div class="val">{row.q50_per100k:.1f}</div>'
             f'<div class="desc">{t["prepare"].format(n=fmt(rows.cases_high))}</div></div>')

    with st.container(key="card_todo"):
        card_title("check", t["todo"], ALERT_TEXT[lang][row.level].split(":")[0])
        steps = "".join(f'<div class="todo"><span class="when">{icon("clock", 15)}{w}</span><span class="do">{d}</span>'
                        f'<span class="gives">{g.format(n=fmt(rows.cases_high))}</span></div>'
                        for w, d, g in PLAYBOOK[lang][row.level])
        html(f'<div><div class="todo head"><span>{t["when"]}</span><span>{t["do"]}</span><span>{t["gives"]}</span></div>{steps}</div>')
        one = brief_table(fc[fc.unit_id == unit_id], fc_h[fc_h.unit_id == unit_id])
        st.download_button(t["download_brief"], brief_markdown(one), file_name=f"epilag_brief_{unit_id}.md",
                           mime="text/markdown", icon=":material/download:", key="dl_unit")

    hist = D["history"][D["history"].unit_id == unit_id]
    if mode == "replay":
        hist = hist[(hist.week >= origin - pd.Timedelta(weeks=104)) & (hist.week <= origin + pd.Timedelta(weeks=26))]
    else:
        hist = hist[hist.week >= hist.week.max() - pd.Timedelta(weeks=156)]
    bt = D["backtest"][(D["backtest"].unit_id == unit_id) & (D["backtest"].horizon == 4)].sort_values("target_week")
    bt = bt[bt.target_week.between(hist.week.min(), hist.week.max())]
    now = fc[fc.unit_id == unit_id].sort_values("target_week")

    fig = go.Figure()
    if not bt.empty:
        for year, g in bt.groupby("test_year"):
            fig.add_trace(go.Scatter(x=pd.concat([g.target_week, g.target_week[::-1]]),
                                     y=pd.concat([g.q90, g.q10[::-1]]), fill="toself", fillcolor=BAND,
                                     line=dict(width=0), hoverinfo="skip", showlegend=False))
            fig.add_trace(go.Scatter(x=g.target_week, y=g.q50, line=dict(color=ACCENT, width=1.5, dash="dot"),
                                     name=t["fc4"], showlegend=bool(year == bt.test_year.min())))
    fig.add_trace(go.Scatter(x=hist.week, y=hist.cases, line=dict(color="#14211B", width=2, shape="spline", smoothing=0.4),
                             name=t["actual"]))
    fig.add_trace(go.Scatter(x=hist.week, y=threshold_series(unit_id, hist.week),
                             line=dict(color=LEVEL_COLOR["outbreak warning"], width=1.4, dash="dash"), name=t["epi_line"]))
    fig.add_trace(go.Scatter(x=now.target_week, y=now.q50, mode="lines+markers",
                             error_y=dict(type="data", symmetric=False, array=now.q90 - now.q50,
                                          arrayminus=now.q50 - now.q10, color=ACCENT, thickness=2, width=6),
                             line=dict(color=ACCENT, width=3), marker=dict(size=10, line=dict(color="#fff", width=2)),
                             name=t["fcnow"] if mode == "latest" else f"{t['fcnow']} ({origin:%d %b %Y})"))
    with st.container(key="card_hist"):
        card_title("unit", t["history"])
        st.plotly_chart(style(fig, 420, yaxis_title=t["cases"]), width="stretch", config={"displayModeBar": False})

    if mode == "replay":
        return
    dr = D["drivers"][(D["drivers"].unit_id == unit_id) & (D["drivers"].horizon == horizon)]
    dr = dr.reindex(dr.shap.abs().sort_values(ascending=False).index).head(10)
    with st.container(key="card_why"):
        card_title("about", t["why"], t["why_note"])
        html('<div class="why-list">' + "".join(
            f'<div><span class="pill" style="background:{ACCENT_DARK if v > 0 else "#E2E8E4"};color:{"#fff" if v > 0 else "#2B3A33"}">'
            f'{"+" if v > 0 else "−"}{abs(v):.2f}</span><b>{d}</b> {t["up"] if v > 0 else t["down"]}</div>'
            for d, v in zip(dr.driver.head(3), dr.shap.head(3))) + "</div>")
        dr = dr[::-1]
        bar = go.Figure(go.Bar(x=dr.shap, y=dr.driver, orientation="h", marker_cornerradius=6,
                               marker_color=[ACCENT if v > 0 else "#C5CFC9" for v in dr.shap]))
        st.plotly_chart(style(bar, 320, xaxis_zeroline=True, xaxis_zerolinecolor="#9AA5B1"), width="stretch",
                        config={"displayModeBar": False})


def page_proof():
    hero(t["proof_head"], t["proof_muted"], t["proof_sub"])
    rep = load_reports(panel)
    if "backtest" not in rep:
        st.warning("No backtest results for this dataset yet.")
        return
    bt = rep["backtest"]
    h = horizon if horizon in set(bt.horizon) else 4
    bh = bt[bt.horizon == h]
    beat = int(((bh.mae_epilag < bh.mae_seasonal_naive) & (bh.mae_epilag < bh.mae_persistence)).sum())
    al = rep.get("alerts")
    alw = al[(al.horizon == h) & (al.rule == "warn_upper")] if al is not None else None

    c1, c2, c3 = st.columns(3, gap="medium")
    with c1, st.container(key="hero_proof"):
        html(f'<div class="big">{count(beat)}<span style="font-size:30px;opacity:.75"> / {len(bh)}</span></div>'
             f'<div style="margin-top:8px;font-size:15px">{t["beat"].format(h=h)}</div>')
    with c2, st.container(key="card_p_caught"):
        rng = f"{alw.share_warned.min():.0%}–{alw.share_warned.max():.0%}" if alw is not None and len(alw) else "–"
        html(f'<div class="kpi"><div class="lab">{icon("bell", 16)}{t["ew_chart"].format(h=h)}</div><div class="val">{rng}</div>'
             f'<div class="desc">{t["caught_share"].format(h=h)}</div></div>')
    with c3, st.container(key="card_p_cov"):
        html(f'<div class="kpi"><div class="lab">{icon("proof", 16)}{t["range"]}</div>'
             f'<div class="val">{bh.coverage_10_90.min():.0%}–{bh.coverage_10_90.max():.0%}</div>'
             f'<div class="desc">{t["coverage"]}</div></div>')

    left, right = st.columns(2, gap="medium")
    years = bh.test_year.astype(str)
    err = go.Figure([go.Bar(name="EpiLag-PH", x=years, y=bh.mae_epilag, marker_color=ACCENT),
                     go.Bar(name="Same week last year", x=years, y=bh.mae_seasonal_naive, marker_color="#C5CFC9"),
                     go.Bar(name="Same as this week", x=years, y=bh.mae_persistence, marker_color="#8A9891")])
    with left, st.container(key="card_err"):
        card_title("proof", t["err_chart"].format(h=h))
        st.plotly_chart(style(err, 340, barmode="group", barcornerradius=8, bargap=0.3, xaxis_type="category"), width="stretch",
                        config={"displayModeBar": False})
    if alw is not None and len(alw):
        ew = go.Figure([go.Bar(name="Caught" if lang == "en" else "Nahuli", x=alw.test_year.astype(str), y=alw.share_warned,
                               marker_color=ACCENT, text=[f"{v:.0%}" for v in alw.share_warned], textposition="outside"),
                        go.Bar(name="False alarms" if lang == "en" else "Maling babala", x=alw.test_year.astype(str),
                               y=alw.false_alarm_share, marker_color="#EE8A2A",
                               text=[f"{v:.0%}" for v in alw.false_alarm_share], textposition="outside")])
        with right, st.container(key="card_ew"):
            card_title("bell", t["ew_chart"].format(h=h))
            st.plotly_chart(style(ew, 340, barmode="group", barcornerradius=8, bargap=0.3, xaxis_type="category",
                                  yaxis=dict(tickformat=".0%", range=[0, 1.15])), width="stretch",
                            config={"displayModeBar": False})

    if "backtest_noweather" in rep:
        nw = rep["backtest_noweather"].set_index(["test_year", "horizon"]).mae_epilag
        w = bt.set_index(["test_year", "horizon"]).mae_epilag
        gain = (1 - w / nw).rename("gain").reset_index()
        with st.container(key="card_weather"):
            card_title("rain", t["weather_head"], t["weather_note"])
            g = gain[gain.horizon == h]
            fig = go.Figure(go.Bar(x=g.test_year.astype(str), y=g.gain, marker_cornerradius=8,
                                   marker_color=[ACCENT if v > 0 else "#C5CFC9" for v in g.gain],
                                   text=[f"{v:+.0%}" for v in g.gain], textposition="outside"))
            st.plotly_chart(style(fig, 260, yaxis=dict(tickformat="+.0%"), bargap=0.55, xaxis_type="category"), width="stretch",
                            config={"displayModeBar": False})

    with st.expander(t["tables"], icon=":material/table:"):
        view = bt[["test_year", "horizon", "mae_epilag", "mae_seasonal_naive", "mae_persistence", "coverage_10_90"]].copy()
        view.columns = ["Test year", "Weeks ahead", "EpiLag error", "Same week last year", "Same as this week",
                        "Range coverage (target 80%)"]
        st.dataframe(view.style.format({"EpiLag error": "{:.0f}", "Same week last year": "{:.0f}",
                                        "Same as this week": "{:.0f}", "Range coverage (target 80%)": "{:.0%}"}),
                     hide_index=True, width="stretch")
        if al is not None:
            piv = al[al.horizon == h].pivot_table(index="test_year", columns="rule", values=["share_warned", "false_alarm_share"])
            piv.columns = [f"{'Caught' if a == 'share_warned' else 'False alarms'} ({'watch' if r == 'warn_upper' else 'warning'})"
                           for a, r in piv.columns]
            st.dataframe(piv.style.format("{:.0%}"), width="stretch")
        if "backtest_noweather" in rep:
            st.dataframe(gain.rename(columns={"gain": "Error reduction from weather"})
                         .style.format({"Error reduction from weather": "{:+.0%}"}), hide_index=True, width="stretch")


def page_budget():
    hero(t["plan_head"], t["plan_muted"], t["plan_sub"])
    left, right = st.columns([1, 1.5], gap="medium")
    with left, st.container(key="card_inputs"):
        card_title("budget", t["budget"])
        budget = st.number_input(t["budget"], min_value=0, value=5_000_000, step=500_000, label_visibility="collapsed")
        html('<div class="kicker" style="margin-top:14px">Clean-up drive + container covers</div>')
        cost_a = st.number_input(t["cost"], value=15.0, step=1.0, key="ca")
        eff_a = st.slider(t["effect"], 0.0, 0.8, (0.10, 0.50), key="ea")
        html('<div class="kicker" style="margin-top:14px">Targeted fogging</div>')
        cost_b = st.number_input(t["cost"], value=25.0, step=1.0, key="cb")
        eff_b = st.slider(t["effect"], 0.0, 0.8, (0.0, 0.10), key="eb")
    actions = (
        Action("Clean-up drive + container covers", cost_a, eff_a[0], sum(eff_a) / 2, eff_a[1], 0.30),
        Action("Targeted fogging", cost_b, eff_b[0], sum(eff_b) / 2, eff_b[1], 0.10),
    )
    plan = allocate(fc[fc.horizon.isin([2, 4, 6, 8])], budget, actions)
    with right:
        if plan.empty:
            st.info("No funded actions. Increase the budget.")
            return
        lo, mid, hi = plan.averted_low.sum(), plan.averted_mid.sum(), plan.averted_high.sum()
        with st.container(key="hero_plan"):
            html(f'<div class="kicker" style="color:rgba(255,255,255,.75)">{t["averted"]}</div>'
                 f'<div class="big" style="margin:8px 0">{count(mid)}</div>'
                 f'<span class="chip">{t["averted_range"]}: {fmt(lo)}–{fmt(hi)}</span>'
                 f'<span class="chip">{t["per_case"]}: ₱{fmt(plan.spend.sum() / mid) if mid else "–"}</span>'
                 f'<span class="chip">{t["people"]}: {fmt(plan.people_covered.sum())}</span>')
        by_area = plan.pivot_table(index="unit_name", columns="action", values="spend", aggfunc="sum", fill_value=0)
        by_area = by_area.loc[by_area.sum(axis=1).sort_values().index].tail(12)
        fig = go.Figure([go.Bar(y=by_area.index, x=by_area[a], name=a, orientation="h",
                                marker_color=ACCENT if i == 0 else "#F2C14E")
                         for i, a in enumerate(by_area.columns)])
        with st.container(key="card_spend"):
            card_title("map", t["spend_chart"], t["plan_gives"])
            st.plotly_chart(style(fig, 380, barmode="stack", barcornerradius=6, xaxis_tickprefix="₱"),
                            width="stretch", config={"displayModeBar": False})
    out = pd.DataFrame({
        t["area"]: plan.unit_name, "Action": plan.action, "Spend (PHP)": plan.spend.round(0).astype(int),
        "People covered": plan.people_covered.round(0).astype(int),
        "Cases averted (low)": plan.averted_low.round(0).astype(int),
        "Cases averted (central)": plan.averted_mid.round(0).astype(int),
        "Cases averted (high)": plan.averted_high.round(0).astype(int),
    })
    with st.container(key="card_plan"):
        card_title("check", t["plan"])
        st.dataframe(out.style.format({c: "{:,}" for c in out.columns[2:]}), hide_index=True, width="stretch")
        st.download_button(t["download_plan"], out.to_csv(index=False), file_name="epilag_funded_plan.csv",
                           mime="text/csv", icon=":material/download:", key="dl_plan")


def page_qc():
    hero(t["qc_head"], t["qc_muted"], t["qc_note"])
    if panel != "region_qc":
        with st.container(key="card_switch"):
            html(f'<div class="alertbar" style="background:var(--accent-soft)">{icon("about")}{t["switch_qc"]}</div>')
            st.button(t["switch_btn"], on_click=lambda: st.session_state.update(panel="region_qc"), key="switch_btn")
        return
    brgy = pd.read_csv(DATA / "qc_barangays.csv")
    qc = fc[(fc.unit_id == "QC")].sort_values("horizon")
    qc8 = qc.q50.mean() * 8
    brgy["expected_8wk"] = brgy.share * qc8
    lvl = qc[qc.horizon == horizon].level.iloc[0]
    a, b = st.columns([1, 1.6], gap="medium")
    with a:
        with st.container(key="hero_qc"):
            html(f'<div class="kicker" style="color:rgba(255,255,255,.75)">{t["city_fc"]}</div>'
                 f'<div class="big" style="margin:8px 0">{count(qc8)}</div>'
                 f'<span class="chip"><i class="dot" style="background:{LEVEL_COLOR[lvl]}"></i>{LEVEL_NAME[lang][lvl]}</span>'
                 f'<div style="font-size:14px;opacity:.9;margin-top:12px">{ALERT_TEXT[lang][lvl]}</div>')
        with st.container(key="card_qc_top"):
            card_title("qc", "Top 5")
            top5 = brgy.head(5)
            html('<div class="rows">' + "".join(
                f'<div class="row" style="grid-template-columns:28px minmax(0,1fr) 64px;animation-delay:{i * .05:.2f}s">'
                f'<span class="rk">{i}</span><div class="nm">{r.Barangay}<small>{r.share:.1%} · {int(r.cases_2025):,} (2025)</small></div>'
                f'<span class="num">{r.expected_8wk:.0f}</span></div>' for i, r in enumerate(top5.itertuples(), 1)) + "</div>")
    with b, st.container(key="card_qc_chart"):
        card_title("map", t["brgy_chart"])
        top = brgy.head(20)[::-1]
        shade = [f"rgba(18,128,74,{0.35 + 0.65 * i / 19:.2f})" for i in range(len(top))]
        fig = go.Figure(go.Bar(x=top.expected_8wk, y=top.Barangay, orientation="h", marker_color=shade,
                               marker_cornerradius=6))
        st.plotly_chart(style(fig, 560), width="stretch", config={"displayModeBar": False})
    with st.expander(t["all_areas"], icon=":material/table:"):
        st.dataframe(brgy.rename(columns={"cases_2022_2025": "Cases 2022-2025", "cases_2025": "Cases 2025",
                                          "share": "Share of city", "expected_8wk": "Expected, next 8 weeks"}),
                     hide_index=True, width="stretch")


def page_about():
    hero(t["about_head"], t["about_muted"])
    blocks = [
        ("unit", "What EpiLag-PH does",
         "It forecasts weekly dengue cases 2-8 weeks ahead for each area, from recent cases, season, and rain, heat and "
         "humidity in the past 12 weeks. It flags areas likely to pass the epidemic threshold, explains each forecast, "
         "and ranks where a limited budget prevents the most cases."),
        ("proof", "Method",
         "LightGBM quantile models (10th, 50th, 90th percentile), one per horizon. Ranges are calibrated with conformalized "
         "quantile regression. Thresholds per area and week of year from earlier years only: usual = mean, "
         "epidemic = mean + 2 SD. Explanations with SHAP."),
        ("map", "Data",
         "<ul><li>DOH Epidemiology Bureau dengue cases and deaths, 2016-2021, via HDX (PJDSC official catalogue).</li>"
         "<li>UPRI-NOAH weekly dengue and rainfall: 17 regions (2016-2019, 2022-2025) and Quezon City (2010-2025), "
         "Zenodo 19448695, ODC-ODbL.</li><li>Weather: ERA5 reanalysis via the Open-Meteo archive API, at each area's centroid.</li>"
         "<li>Population: OCHA COD-PS (PSA-based), 2022. Codes and boundaries: OCHA COD-AB; maps: faeldon/philippines-json-maps (MIT).</li></ul>"),
        ("bell", "Limits (read before use)",
         "<ul><li>Province data ends in January 2021; the province view is a historical replay.</li>"
         "<li>Reported cases undercount true infections (about 4.7 times in one Cebu City study).</li>"
         "<li>One weather point per area: large provinces are simplified.</li>"
         "<li>Weather adds only a modest gain over recent cases and season.</li>"
         "<li>The 'watch' level catches most outbreak starts but has many false alarms; the 'warning' level is stricter.</li>"
         "<li>Budget effects and costs are assumptions, shown as ranges and editable.</li>"
         "<li>Barangay ranking in Quezon City uses yearly shares, not weekly barangay forecasts.</li></ul>"),
    ]
    for row in (blocks[:2], blocks[2:]):
        for col, (ic, head, body) in zip(st.columns(2, gap="medium"), row):
            with col, st.container(key=f"card_about_{ic}"):
                card_title(ic, head)
                html(f'<div style="font-size:14.5px;line-height:1.6">{body}</div>')


# ------------------------------------------------------------------ shell: navigation, controls, run

def go_replay_story():
    st.session_state.update(panel="province", mode="replay")


lang = st.session_state.get("lang", "en")
t = T[lang]
PAGE_FNS = {"home": page_home, "map": page_map, "unit": page_unit, "budget": page_budget, "qc": page_qc,
            "proof": page_proof, "about": page_about}
start = st.query_params.get("page")  # optional deep link, e.g. ?page=budget
PAGES = {key: st.Page(fn, title=t[f"nav_{key}"], icon=PAGE_ICON[key], url_path=key,
                      default=(key == start) if start in PAGE_FNS else (key == "home"))
         for key, fn in PAGE_FNS.items()}
nav = st.navigation(list(PAGES.values()), position="hidden")
current = next((k for k, p in PAGES.items() if p.title == nav.title), "home")

html(CSS)
with st.container(key="topbar"):
    brand, menu, langs = st.columns([1.7, 9, 1.3], gap="small")
    with brand:
        html(f'<div class="brand">{LOGO}<div>EpiLag-PH<small>Dengue early warning</small></div></div>')
    with menu, st.container(key="topnav"):
        for col, (key, pg) in zip(st.columns(len(PAGES), gap="small"), PAGES.items()):
            with col, st.container(key=f"navon_{key}" if key == current else f"navoff_{key}"):
                st.page_link(pg, label=t[f"nav_{key}"])
    with langs:
        st.radio(t["lang"], ["en", "fil"], format_func=lambda x: "EN" if x == "en" else "FIL", horizontal=True,
                 key="lang", label_visibility="collapsed")

with st.container(key="ctx"):
    c1, c2, c3, c4 = st.columns([2.1, 2.1, 2.4, 1.6], gap="medium")
    panel = c1.radio(t["dataset"], list(PANELS), format_func=lambda p: PANELS[p]["label"][lang], horizontal=True,
                     key="panel", help=PANELS["region_qc"]["note"][lang] + " · " + PANELS["province"]["note"][lang])
    D = load(panel)
    mode = c2.radio(t["mode"], ["latest", "replay"], format_func=lambda m: t[f"mode_{m}"], horizontal=True, key="mode")
    if mode == "replay":
        origins = replay_origins(panel)
        default = origins[origins.dt.month.eq(6)].iloc[0] if origins.dt.month.eq(6).any() else origins.iloc[0]
        origin = c3.select_slider(t["origin"], options=list(origins), value=default,
                                  format_func=lambda d: d.strftime("%d %b %Y"), key=f"origin_{panel}")
        horizon = c4.radio(t["horizon"], [4, 8], horizontal=True, key="h_replay")
    else:
        c3.markdown(f'<div class="hero-sub" style="margin-top:28px">{PANELS[panel]["note"][lang]}</div>',
                    unsafe_allow_html=True)
        horizon = c4.radio(t["horizon"], [2, 4, 6, 8], index=1, horizontal=True, key="h_latest")

fc = D["forecast"] if mode == "latest" else replay_forecast(panel, origin)
fc_h = fc[fc.horizon == horizon].copy()
fc_h["level"] = pd.Categorical(fc_h.level, LEVELS, ordered=True)

nav.run()
