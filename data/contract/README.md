# Weekly case data contract

This is the one file a health office, a regional epidemiology unit or the DOH Epidemiology Bureau needs to send for
EpiLag-PH to forecast its areas. It is the same shape as the DOH data the pipeline already reads: counts per area per
week, nothing about any patient.

| Column | Required | What it holds |
| --- | --- | --- |
| `area_code` | yes | The area's code: the PSGC-based code EpiLag-PH uses (`PH01028` for Ilocos Norte), `R_NCR` style for regions, `QC` for Quezon City. A new code is accepted with a warning and becomes a new area. |
| `area_name` | no | A readable name, for the people checking the file. |
| `week_ending` | yes | The Sunday that ends the reporting week, as `YYYY-MM-DD`. |
| `cases` | yes | Reported dengue cases that week, a whole number of 0 or more. **Leave it empty if the area did not report**; never write 0 for a missing report. |

Rules the check enforces (`python scripts/validate_cases.py <file.csv>`):

- **Errors** (the file is rejected): a missing column; a date that is not a Sunday, cannot be read or is in the future;
  a negative or fractional count; the same area and week twice.
- **Warnings** (the file is accepted, a person should look): an unknown area code; a week more than 10 times the
  area's previous 12-week median, which is often a typing slip or a backlog of late reports; gaps of missing weeks.

**No personal data.** The file must hold counts only: no names, addresses, ages, case IDs or dates of birth. The check
rejects any column it does not know, so patient line lists cannot slip in. One number per area per week does not
identify anyone, which keeps the system clear of the personal and sensitive personal information covered by the Data
Privacy Act of 2012 (RA 10173). The one risk is a very small count in a very small area, so barangay-level numbers
should be shared for health-office use, not published, until they are aggregated.

[`weekly_cases_template.csv`](weekly_cases_template.csv) is a filled-in example. The second Ilocos Sur week shows a
missing report.
