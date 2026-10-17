# EpiLag-PH: the film

`docs/demo.mp4` (1:48, 1920×1080, H.264 + AAC) is a motion-graphics film with an original synthesised music
bed. The on-screen text tells the story, so it works without a voice-over. The source is
`docs/film/index.html` (HTML/CSS animation), recorded with `python scripts/record_film.py`.

Optional voice-over (about 130 words per minute), timed to the scenes:

| Time | Scene | On screen | Voice-over |
| --- | --- | --- | --- |
| 0:00–0:07 | The rains | Rain, "The rains arrive." | "June 2019. The rains arrive. Standing water, warm nights, and mosquitoes breed." |
| 0:07–0:16 | The surge | Provinces turn red | "Four weeks later, dengue surges. In a single week, thirty-two provinces cross the epidemic threshold." |
| 0:16–0:25 | Why late | Rain → mosquitoes → sick → hospital reports | "Why do we always act late? Because the cases we count are reported weeks after the rain that caused them." |
| 0:25–0:31 | Brand | EpiLag-PH logo | "EpiLag-PH. See dengue coming. Act weeks earlier." |
| 0:31–0:43 | Replay | EpiLag's 2 June forecast map, "30 of 32" | "Here is what EpiLag-PH said on the second of June, using models trained only on earlier years. Of the thirty-two provinces that crossed the threshold, thirty were already flagged, four weeks ahead." |
| 0:43–0:52 | Overview | App overview | "The app starts with one screen that explains every tool and lists this week's priority areas." |
| 0:52–1:01 | Forecast | Forecast map | "It forecasts every province, region and Quezon City, two to eight weeks ahead, with a likely range." |
| 1:01–1:10 | Explain & act | Area checklist | "For each area, a checklist: what to do today, in two weeks, in four, and what EpiLag-PH gives you to do it." |
| 1:10–1:19 | Plan | Budget plan | "Enter a budget, and it puts each peso where it averts the most cases." |
| 1:19–1:27 | Target | QC barangays | "In Quezon City, it names the barangays to visit first." |
| 1:27–1:38 | Proof | Three stat cards | "We tested it honestly. It beat simple rules in five of six tests and caught most outbreak starts four weeks ahead, with false alarms we report openly." |
| 1:38–1:48 | Close | "EpiLag-PH sees it now." | "Hospitals see dengue a month late. EpiLag-PH sees it now." |

To re-record after changing the app: run the app on port 8599, then `python scripts/screenshots.py` and
`python scripts/record_film.py` (needs Chrome and `pip install imageio-ffmpeg`).
