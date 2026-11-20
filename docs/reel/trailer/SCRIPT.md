# EpiLag-PH trailer: storyline

Length 2:40, 30 fps. Two cuts from one timeline:

- landscape 1920 x 1080: `docs/reel/trailer/out/epilag-trailer-land.mp4`. The picture fills the frame; titles sit over it.
- portrait 1080 x 1920 (Instagram Reels): `docs/reel/trailer/out/epilag-trailer-port.mp4`. The same picture as a band
  over its own blur, the chapter title stacked above, captions below.

The voice-over script, line by line, is in [`VOICEOVER.md`](VOICEOVER.md). The voice is a guide track
(`en-US-ChristopherNeural`); every cut, title and caption is placed on the spoken words, so a new recording
re-times the trailer by itself.

| Time | Beat | Picture | Type |
|---|---|---|---|
| 0:00 | The rains | Rain gathers into QUEZON CITY and washes away | September 2024 |
| 0:08 | What the water breeds | Old tire, gutter, flower pot fill; larvae; the swarm doubles to 256 | |
| 0:16 | The bill | The swarm rushes the camera | THE RAIN IS FREE. / THE DENGUE BILL COMES LATER. |
| 0:22 | The surge | The camera rides the 2024-25 season up to its peak, then pulls back | 622 · 5× · 27 |
| 0:33 | The problem | | THEY SAW IT LATE. Rain, mosquitoes, people sick, counted |
| 0:40 | The question | Brand hit | WHAT IF THEY HAD SEEN IT COMING? · EpiLag-PH |
| 0:47 | Rewind | The season runs backwards on tape, then replays with the forecasts; the Watch alert arrives | ▶ REPLAY 2024 · Flagged five weeks early |
| 1:00 | Sizzle (music only) | Five cuts on the beat | SEE IT. PLAN IT. FUND IT. TEST IT. PLAY IT. |
| 1:04 | 01 / SEE | Forecast map, priority list, Quezon City's row | Dengue, 2 to 8 weeks ahead · 104 areas |
| 1:14 | 02 / ACT | The Watch call, the checklist, why it is flagged | A plan, not just a number |
| 1:22 | 03 / SPEND | Budget typed, plan re-ranked, the barangays | The most cases prevented per peso |
| 1:29 | 04 / FOR EVERYONE | First-visit tour, switch to Filipino | A guided tour. English or Filipino. |
| 1:36 | Card | | THEN WE TRIED TO BREAK IT. |
| 1:39 | 05 / TEST | Research page: headline numbers, four-method test, the table | 19 · 3 · 12/24 · 5/6 |
| 1:53 | Card | | IT LOST THREE TIMES. |
| 1:56 | 06 / OWN IT | Where it lost, and why | 3 losses · 3 causes |
| 2:01 | Card | | DON'T TAKE OUR WORD FOR IT. |
| 2:04 | 07 / PLAY | Drill title and missions, the choice of forecaster, a round with forecasts | 18 seasons · 10 teams · 8 turns |
| 2:17 | Montage (music only) | Six gameplay cuts | SEND THE TEAMS. … TRY ANOTHER MODEL. |
| 2:28 | The rains again | Rain over the city | THE RAINS WILL COME AGAIN. / THIS TIME, SEE DENGUE COMING. |
| 2:34 | End card | | EpiLag-PH · romeo-04.github.io/epilag |

Where the numbers come from: the Quezon City season is `docs/film/data.js` (DOH counts); 104 areas, 19 studies,
12 of 24 and 5 of 6 are from `research/README.md` and the Research page; 18 missions, 10 teams and 8 turns are
the Drill's title screen.

## Rebuilding

```bash
TRAILER_SITE=<checkout>/docs python scripts/trailer_capture.py   # films the built site (default: this checkout's docs/)
python scripts/trailer_voice.py                                    # guide voice and word timings
python scripts/record_trailer.py                                   # both cuts; or: land | port, --remix, --stills
```

Preview in a browser: open `docs/reel/trailer/index.html` (landscape); `#t=80` starts at 80 s.
The portrait page (`index.html?port`) shows rendered picture frames, so it previews only after
`python scripts/record_trailer.py port --keep-pic`.
