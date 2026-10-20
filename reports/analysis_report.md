# Customer Acquisition and Segmentation — Analysis Report

## Executive summary

The analytical extract contains **25,000 customer records** in **7 countries** across **4 customer segments**.
Average recorded customer acquisition cost is **42.16 units**; total recorded acquisition cost is **1,053,993.76 units**. The monetary currency is **not specified**.
Average customer age is **45.9 years**.

The **USA** contributes **14,925 customers (59.7%)** and **Consumer** is the largest segment with **13,638 customers (54.6%)**. These groups also account for large *total* recorded acquisition cost because they contain more customers; their *average* costs are similar to other groups.

## Business questions

1. Which countries and segments account for the largest shares of acquired customers?
2. How do recorded acquisition costs vary across countries, segments, genders, and regions?
3. Is customer age associated with acquisition cost?
4. What data-quality limits affect business decisions?

## KPIs

| Metric | Value |
| --- | ---: |
| Customer records | 25,000 |
| Overall mean recorded acquisition cost | 42.16 cost units |
| Median recorded acquisition cost | 41.98 cost units |
| Total of recorded acquisition costs | 1,053,993.76 cost units |
| Mean customer age | 45.9 years |
| Countries | 7 |
| Customer segments | 4 |
| Customer acquisition cost interquartile range | 23.30–61.13 units |

## Customer segments

| Segment | Customers | Customer share | Mean recorded acquisition cost |
| --- | ---: | ---: | ---: |
| Consumer | 13,638 | 54.6% | 42.26 |
| Premium | 6,301 | 25.2% | 41.94 |
| VIP | 2,542 | 10.2% | 41.93 |
| Business | 2,519 | 10.1% | 42.38 |

## Country profile

| Country | Customers | Customer share | Mean recorded acquisition cost |
| --- | ---: | ---: | ---: |
| USA | 14,925 | 59.7% | 42.09 |
| UK | 3,701 | 14.8% | 42.27 |
| Germany | 2,046 | 8.2% | 42.22 |
| Canada | 1,279 | 5.1% | 42.61 |
| Australia | 1,233 | 4.9% | 42.97 |
| India | 1,041 | 4.2% | 41.83 |
| UAE | 775 | 3.1% | 41.28 |

## Statistical exploration

- **Cost vs. segment:** one-way ANOVA F=0.498, p=0.683, eta-squared=0.00006. This sample shows no compelling evidence of substantial mean-cost differences across segments.
- **Cost vs. country:** one-way ANOVA F=0.682, p=0.664, eta-squared=0.00016. Country explains a negligible fraction of the observed cost variation in this sample.
- **Cost vs. age:** Pearson r=0.00021, p=0.974. There is no meaningful linear relationship in these records.
- **Country vs. segment:** chi-square p=0.937; Cramér's V=0.0114. The sample shows no meaningful country/segment association.

These tests are exploratory and assume sufficiently representative and reliable data. Non-significant p-values do **not** prove groups are identical; statistical tests do not establish causality.

## Data quality and limitations

- **No missing data and no duplicate analysis IDs:** 0 missing extract cells and 0 duplicate analysis IDs.
- **Postal-code format concern:** 7,254 (29.0%) rows were flagged during basic postal-code *format* checks of the private source. Canada and the UK typically use alphanumeric formats; India typically uses six digits; Australia typically uses four. This is a format-screening result only, not postcode-level verification.
- **Unusual geography:** The privately examined input used five-digit numeric postal codes for every country, which is implausible for several markets. Actual postcodes, names and granular locations have been excluded from the published extract.
- **Unknown currency:** all cost metrics are expressed in **unspecified cost units**, not USD or LKR.
- **No acquisition dates, marketing channels, revenues, campaign budgets, transactions, conversion events, or retention outcomes:** cannot calculate ROI, customer lifetime value, real-world channel efficiency, conversion rates, seasonality, or retention.
- **Country/region and segment labels are treated as given:** definitions of `region`, `Consumer`, `Business`, `Premium`, and `VIP` are not provided. Avoid assuming geographic standards, purchase activity, profitability, or VIP business value.
- **Potentially simulated data:** The original dataset appears potentially simulated, but its provenance and usage rights have not been verified. The public extract removes direct identifiers but is not a guarantee of anonymity.

## Actionable recommendations

1. **Audit customer-data provenance and country-specific postal codes** before joining to geographic market data or targeting individuals.
2. **Prioritize market-volume analysis for the USA and Consumer segment** because they make up the greatest shares of the file—not because they have proven higher ROI or profitability.
3. **Do not claim a cheaper segment or geography based on this file:** observed mean-cost differences are small, and the tests do not show meaningful differentiation.
4. **Add acquisition date, marketing channel, campaign ID, spend, and revenue/conversion outcomes** to support real CAC, ROAS/ROI, cohorts, trends, and customer-lifetime-value analysis.
5. **Validate source accuracy and sampling** before making commercial allocation decisions. This project is a descriptive portfolio demonstration.

## Visualization index

1. [Customers by country](charts/01_customers_by_country.png)
2. [Customers by segment](charts/02_customers_by_segment.png)
3. [Acquisition cost distribution](charts/03_acquisition_cost_distribution.png)
4. [Acquisition cost spread by segment](charts/04_acquisition_cost_by_segment.png)
5. [Age group distribution](charts/05_customer_age_groups.png)
6. [Average cost by country](charts/06_average_cost_by_country.png)
7. [Segment mix by country](charts/07_segment_mix_by_country.png)
8. [Mean cost by age](charts/08_cost_by_age.png)

## Reproducibility

Generated by `src/analyze_customers.py` from `data/public/customer_analytics.csv` (privacy-reduced extract). All summary tables are in `reports/tables/` and statistical tests in `reports/statistical_tests.json`.
