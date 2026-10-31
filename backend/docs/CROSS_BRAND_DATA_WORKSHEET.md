# Cross-brand foundation data worksheet (Milestone C.1a)

**Purpose:** Collect ~18–24 real shades by hand so Milestone C.1b can add them to the live catalog.

**This file is a planning worksheet only.** It does **not** add shades to `foundation_catalog.json`. Do not mark anything verified until you open the official page yourself.

---

## Two different “verified” ideas (do not mix them up)

| Idea | Field | Meaning |
|------|--------|---------|
| Catalog metadata checked | `metadata_verification_status` = `source_checked` | You copied brand/product/shade text from the official page |
| Match accuracy proven | `matching_accuracy_status` = `wear_validated` | Someone actually tested that the shade matches well |

For every new shade in C.1b:

- After you check the page → `source_checked` + `brand_verified`
- Keep `matching_accuracy_status` = **`not_evaluated`**
- Leave all `independent_*` fields **`null`** until a real wear test

Checking a webpage ≠ proving a match.

---

## Official product pages (open in a browser — do not scrape)

| Brand | Product | URL |
|-------|---------|-----|
| NARS | Light Reflecting Foundation | https://www.narscosmetics.com/USA/light-reflecting%E2%84%A2-advanced-skincare-foundation/999NAC0000141.html |
| Maybelline | Fit Me Matte + Poreless Foundation | https://www.maybelline.com/face-makeup/foundation-makeup/fit-me-matte-poreless-foundation |
| Fenty Beauty | Pro Filt'r Soft Matte Longwear Foundation | https://fentybeauty.com/products/pro-filtr-soft-matte-longwear-foundation |

Optional Fenty helper (not a substitute for copying shade fields from a product/shade page):  
https://fentybeauty.com/pages/fenty-face-shade-finder

Machine-readable stubs live in:  
`backend/app/data/catalog_entry_template.json` → `cross_brand_shades_worksheet`

---

## How many shades we plan to collect

**Already in the live catalog (keep — do not re-add):** 5 NARS  
(Fiji, Punjab, Patagonia, Santa Fe, Stromboli)

| Brand / product | Already collected | New slots to fill | Planned total |
|-----------------|-------------------|-------------------|---------------|
| NARS Light Reflecting | 5 | **3** (prefer fair/light, tan, deep gaps) | **8** |
| Maybelline Fit Me Matte + Poreless | 0 | **8** | **8** |
| Fenty Pro Filt'r Soft Matte | 0 | **8** | **8** |
| **Real shades (goal)** | **5** | **19** | **~24** |

Fictional **ShadeWise Demo** rows stay for tests. Never treat them as real recommendations.

---

## Balanced selection targets

When you pick shades on each site, aim for this **shape** (exact names come from the brand — never invent them):

| Depth family (`brand_reported_depth`) | Aim |
|---------------------------------------|-----|
| fair | ~3–4 shades across brands |
| light | ~4–5 |
| medium | ~5–6 (you already have several NARS mediums) |
| tan | ~3–4 |
| deep | ~3–4 |

Also mix undertones where the brand clearly says so: cool, warm, neutral (olive only if the brand literally says olive).

### Depth rules (important)

Our catalog enum allows only: `fair` | `light` | `medium` | `tan` | `deep` | `null`

| Brand wording | What to put in `brand_reported_depth` | What to do instead |
|---------------|----------------------------------------|--------------------|
| fair / light / medium / tan / deep (clear single family) | That enum value | — |
| “light-medium”, “medium-deep”, “light to medium” | **`null`** | Copy exact words into `brand_shade_description` and/or `brand_depth_band` on the worksheet |
| Unclear / missing | **`null`** | Note it in `uncertainty_notes` |

**Do not guess.** Fiji already uses `null` for “Light to medium” — follow that pattern.

### Undertone rules

Set `brand_reported_undertone` only when the brand clearly indicates cool / warm / neutral / olive (including Fit Me names like “Natural Beige” **Warm**).  
If unsure → `null` + note in `uncertainty_notes`.

---

## Fields to fill for each shade

Use one row per shade (see blank table below, or JSON stubs in the template).

| Field | What to write |
|-------|----------------|
| `id` | Unique slug, e.g. `maybelline-fitme-220-natural-beige` |
| `brand` | Exact brand name |
| `product` | Exact product name |
| `shade_name` | Exact marketing name from the page |
| `shade_code` | Code/SKU if shown (e.g. `M1`, `220`, `190`); else `null` |
| `source_url` | Page you used (product or shade URL) |
| `brand_shade_description` | Copy brand blurb **exactly**, or `null` |
| `brand_reported_depth` | Enum or `null` (see rules above) |
| `brand_depth_band` | **Worksheet only** — free text like `light-medium` when enum must stay null |
| `brand_reported_undertone` | `cool` / `warm` / `neutral` / `olive` / `null` |
| `uncertainty_notes` | Anything ambiguous or missing |
| `date_verified` | `YYYY-MM-DD` only after you personally check |
| `metadata_verification_status` | Stay `unreviewed` until checked → then `source_checked` |
| `verification_status` | Stay `estimated` until checked → then `brand_verified` |
| `matching_accuracy_status` | Keep **`not_evaluated`** |
| `independent_depth` / `independent_undertone` / `independent_measurement_notes` | Keep **`null`** until a real wear test |
| `provenance_notes` | Short note: who copied it and when |
| `notes` | Optional free notes (target depth family, why you picked it) |

`brand_depth_band` is for your notes while collecting. It is **not** a live catalog field yet — when you paste into `foundation_catalog.json` in C.1b, either omit it or move the text into `uncertainty_notes` / `brand_shade_description`.

---

## Beginner steps (how to fill this)

1. Open one official product page from the table above.
2. Pick a real shade that helps fill a **depth gap** (see targets).
3. Copy name, code, and description **exactly** into a stub in `catalog_entry_template.json` → `cross_brand_shades_worksheet` (or into the blank table below).
4. Set depth/undertone enums **only** when clearly supported; otherwise `null`.
5. Leave verification as `unreviewed` / `estimated` until the row matches the page.
6. When it matches: set `source_checked`, today’s `date_verified`, `brand_verified`; keep matching accuracy `not_evaluated`.
7. Do **not** paste into `foundation_catalog.json` until Milestone **C.1b** (after review).
8. Repeat until the 19 new slots are filled (or as many as you can honestly verify).

---

## Already in catalog (NARS — reference only)

| id | Shade | Code | Depth enum | Undertone |
|----|-------|------|------------|-----------|
| `nars-lrf-fiji-l5` | Fiji | L5 | `null` (“Light to medium”) | warm |
| `nars-lrf-punjab-m1` | Punjab | M1 | medium | warm |
| `nars-lrf-patagonia-m1-2` | Patagonia | M1.2 | medium | neutral |
| `nars-lrf-santa-fe-m2` | Santa Fe | M2 | medium | neutral |
| `nars-lrf-stromboli-m3` | Stromboli | M3 | medium | warm |

---

## Blank collection table (print / copy)

Fill during browsing. Status starts as draft.

| Slot | Brand | Target depth gap | Exact shade name | Shade code | brand_reported_depth | brand_depth_band (if needed) | brand_reported_undertone | Source URL checked? | date_verified | Notes / uncertainty |
|------|-------|------------------|------------------|------------|----------------------|------------------------------|--------------------------|---------------------|---------------|---------------------|
| N1 | NARS | fair or light | | | | | | [ ] | | |
| N2 | NARS | tan | | | | | | [ ] | | |
| N3 | NARS | deep | | | | | | [ ] | | |
| M1 | Maybelline | fair | | | | | | [ ] | | |
| M2 | Maybelline | fair/light cool | | | | | | [ ] | | |
| M3 | Maybelline | light warm | | | | | | [ ] | | |
| M4 | Maybelline | light/medium neutral | | | | | | [ ] | | |
| M5 | Maybelline | medium warm | | | | | | [ ] | | |
| M6 | Maybelline | medium cool | | | | | | [ ] | | |
| M7 | Maybelline | tan | | | | | | [ ] | | |
| M8 | Maybelline | deep | | | | | | [ ] | | |
| F1 | Fenty | fair / light | | | | | | [ ] | | |
| F2 | Fenty | light | | | | | | [ ] | | |
| F3 | Fenty | light-medium → depth null | | | | | | [ ] | | |
| F4 | Fenty | medium | | | | | | [ ] | | |
| F5 | Fenty | medium | | | | | | [ ] | | |
| F6 | Fenty | medium-deep → depth null | | | | | | [ ] | | |
| F7 | Fenty | tan / deep | | | | | | [ ] | | |
| F8 | Fenty | deep | | | | | | [ ] | | |

Slot F3/F6 intentionally practice **ambiguous bands** → keep `brand_reported_depth` null.

---

## What you must provide before Milestone C.1b

1. Filled worksheet rows (markdown table and/or JSON stubs) with **exact** shade names/codes from the sites.  
2. Honest `null`s where depth/undertone are unclear.  
3. For each row you want in the live catalog: confirmation you opened the source (`source_checked` + date).  
4. Still **`not_evaluated`** matching accuracy and **`null`** independent measurements.  
5. No invented shades and no Demo rows treated as real.

C.1b will copy reviewed rows into `foundation_catalog.json` and extend tests — not this milestone.
