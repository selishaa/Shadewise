# Attribution — The Pudding foundation-names

## Upstream project

- Dataset folder: https://github.com/the-pudding/data/tree/master/foundation-names  
- Essay: [The Naked Truth](https://pudding.cool/2021/03/foundation-names) (March 2021)  
- Primary file used by ShadeWise: `allShades.csv`  
- Parent data repo: https://github.com/the-pudding/data  

## License (verified from upstream repo)

The `the-pudding/data` repository root includes an **MIT License**  
(`Copyright (c) 2019 The Pudding`). A copy is stored next to this file as `LICENSE`.

MIT allows use, copy, modification, and distribution of **that Software** (their
data files and scripts in the repo) when the copyright notice and permission
notice are retained.

## What MIT does *not* automatically grant

| Asset | Notes |
|-------|--------|
| Brand / product names | Trademarks of the brands |
| Shade descriptions copied from retailer pages | Brand / retailer copy |
| Swatch images (`imgSrc` URLs on Ulta/Sephora CDNs) | Third-party images — **do not rehost** |
| Calibrated color truth | Hex/HSL are **approximate** extractions from swatch images |

## ShadeWise usage policy

1. Import offline into **staging only** (`app/data/staging/`), never into `foundation_catalog.json` automatically.  
2. Keep every imported row `estimated` / `unreviewed` / `not_evaluated`.  
3. `recommendation_eligible` stays **false** until a human verifies against a **current official brand page** and promotes a curated row into the live catalog.  
4. Preserve MIT notice when redistributing substantial portions of the imported Software.  
5. Do not claim swatch hex accuracy or matching proof.

## Collection dates (from upstream README)

- Sephora data: 2021-01-11  
- Ulta data: 2021-01-18  
- `allShades.csv` last modified note: 2021-03-17  
