# eVinci / reference-reactor design documents (Stream A / WP A1)

## IAEA_ARIS_SMR_catalogue_2024.pdf (10 MB, 394 pp) — PRIMARY design source
- **Source:** IAEA Advanced Reactors Information System (ARIS),
  https://aris.iaea.org/Publications/SMR_catalogue_2024.pdf
- **Retrieved:** 2026-07-04
- **License:** IAEA publication, freely distributed
- **Contains:** official 2-page datasheets for eVinci, USNC MMR, MARVEL, Oklo Aurora and ~70 other
  SMR/microreactor designs — thermal/electric output, coolant, core outlet temp, refuelling interval,
  footprint, design status. This is the **cleanest citable source for the reference-reactor spec table**.
- **Extract for A1:** pull the eVinci datasheet (≈13 MWth / ≈5 MWe, heat-pipe, ~8-yr core) and the
  MMR/MARVEL/Aurora sheets for the comparator sensitivity.

## NRC eVinci pre-application docs — MANUAL FETCH (auto-download blocked)
- **Landing (works in browser):** https://www.nrc.gov/reactors/new-reactors/advanced/who-were-working-with/pre-application-activities/evinci
- **Example doc:** ADAMS accession **ML23355A166** (eVinci Topical/pre-app material).
- **Barrier:** NRC ADAMS (`adamsxt.nrc.gov` / `www.nrc.gov/docs/...`) blocks scripted curl from here
  (connection refused / 301). Fetch manually via the ADAMS public search:
  https://adamswebsearch2.nrc.gov/webSearch2/main.jsp?AccessionNumber=ML23355A166
  or Google `ML23355A166 site:nrc.gov`. Not blocking — ARIS covers the design envelope for siting.

## Additional design literature to collect (open)
- Westinghouse eVinci technical papers (search: "eVinci heat pipe microreactor" in ANS/Elsevier).
- KRUSTY papers (Poston, Gibson et al.) double as validation refs (see `../nuclear_benchmarks/`).
