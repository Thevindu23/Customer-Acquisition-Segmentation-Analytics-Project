# Dataset notes

This public-facing repository contains only `public/customer_analytics.csv`, a **reduced analytical extract** derived from an uploaded customer master file. Source attribution and permission to redistribute the original dataset have **not** been verified.

Original fields **removed** from the extract: `customer_name`, `customer_id`, `customer_city`, `customer_state`, `customer_postal_code`. The rows have been deterministically shuffled and assigned fresh analysis-only `record_id` values. The `postal_format_check` field stores a derived result of country-specific pattern checks, **not** any original postal code.

| Field | Meaning |
|---|---|
| `record_id` | Analysis-only surrogate record ID, not a customer identifier |
| `customer_age` | Age in years |
| `gender` | As recorded in source; self-reporting method unknown |
| `customer_segment` | Source-provided segment; category definitions unknown |
| `customer_country` | Source-provided country label; unverified |
| `region` | Source-provided region label; geographical interpretation unknown |
| `customer_acquisition_cost` | Recorded acquisition cost per row; **currency unknown** |
| `postal_format_check` | `matches_pattern`, `format_mismatch`, or `not_checked` based on country-specific source-format rules |

**Privacy and licensing:** Removal of direct identifiers does not guarantee anonymity; combinations of attributes and row-level costs can still be sensitive. Do not publish this extract or derived artifacts without the legal/rightful authorization to share source-derived information. If unsure, omit the CSV and embedded-row dashboard from a public GitHub repository until cleared. The repository's original customer master should always remain private.

Generated `data/processed/customers_cleaned.csv` is ignored. The project works from this analytical extract, not the private original.
