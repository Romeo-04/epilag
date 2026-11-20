# EpiLag-PH trailer: voice-over script

14 lines, about 2:10 of speech in a 2:40 trailer. Record one file per line, named `01` to `14`.
The "guide" time is how long the AI guide voice takes; stay close to it and the trailer keeps its length.

## Act 1 · Cold open

**01 · 0:01 · guide 15.0 s** (low and slow; a breath between the three objects)

> Quezon City. September 2024.
> The rains arrive.
> Water collects in old tires, gutters, flower pots.
> And in the dark, the mosquitoes start to breed.

**02 · 0:16 · guide 4.8 s** (two flat statements; each one lands a title card)

> The rain is free.
> The dengue bill comes later.

**03 · 0:22 · guide 10.4 s** (the numbers do the work)

> By February, 622 cases in a single week.
> Five times the epidemic line.
> 27 weeks above it.

**04 · 0:33 · guide 6.2 s**

> The health office saw it late, because cases are counted weeks after the rain that caused them.

**05 · 0:40 · guide 5.1 s** (a question, a beat, then lift on the name)

> What if they had seen it coming?
> This is EpiLag-PH.

**06 · 0:47 · guide 12.2 s** (start right on "Rewind": the tape runs back under it)

> Rewind to September, and replay the season with only the data of the time.
> On September 15, five weeks before the line was crossed, Quezon City turns to Watch.

*(1:00 to 1:04: five quick cuts, music only: SEE IT. PLAN IT. FUND IT. TEST IT. PLAY IT.)*

## Act 2 · The product

**07 · 1:04 · guide 9.2 s** (brisk and even from here to line 10)

> It forecasts dengue 2 to 8 weeks ahead, for 104 areas: every province, every region, and Quezon City.

**08 · 1:14 · guide 7.2 s**

> Open an area, and you get a plan, not just a number: what to do this week, and why it is flagged.

**09 · 1:22 · guide 7.2 s**

> Give it a budget, and it ranks where clean-up and fogging prevent the most cases per peso, down to the barangay.

**10 · 1:29 · guide 6.0 s**

> A guided tour on your first visit.
> In English, or in Filipino.

## Act 3 · The research

**11 · 1:36 · guide 16.0 s** (pause after the first sentence: a title card lands there)

> Then we tried to break it.
> 19 studies reviewed.
> Three rival methods, on the same test.
> Ours had the lowest error in 12 of 24 checks, and beat the simple rules in 5 of 6 test years.

**12 · 1:53 · guide 7.0 s** (plain, no apology in the voice; pause after the first sentence)

> It lost three times.
> We traced every loss to its cause, and published all of it.

## Act 4 · Dengue Drill

**13 · 2:01 · guide 15.6 s** (with a smile; pause after the first sentence, then short, punchy counts)

> Don't take our word for it.
> Play Dengue Drill.
> 18 real seasons. Ten teams. Eight turns.
> Choose whose forecast you trust, and the real cases keep score.

*(2:17 to 2:28: gameplay montage, music only: SEND THE TEAMS. END THE TURN. WATCH IT SPREAD. COUNT THE CASES. DID THE FORECAST HELP? TRY ANOTHER MODEL.)*

## Act 5 · Close

**14 · 2:28 · guide 7.7 s** (slow again, as in line 01)

> The rains will come again.
> This time, see dengue coming.
> EpiLag-PH.

## Pronunciation

- EpiLag-PH: "EP-ih-lag P-H"
- 622: "six hundred twenty-two"
- 2 to 8: "two to eight"
- 104: "one hundred four"
- 12 of 24, 5 of 6: say "of", not "out of"
- barangay: "ba-rang-GUY"

## Bringing the recording in

1. Put the 14 files (`01.m4a` to `14.m4a`, or any audio format) in one folder.
2. `python scripts/reel_import_vo.py --trailer <folder>`
3. `python scripts/record_trailer.py`

Keep the wording as written: the captions show this text, and the cuts wait for these words.
To change a line, edit `LINES` in `scripts/trailer_voice.py` first.
