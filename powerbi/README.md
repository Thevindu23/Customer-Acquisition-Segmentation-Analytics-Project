# Power BI Dashboard — Customer Acquisition & Segmentation

This folder contains a **Power BI Project (`.pbip`)** with a report definition (PBIR)
with **three editable pages and 26 visuals**, an Import-mode Power Query model, and
DAX measures. This is versionable source suitable for GitHub. It is **not** a prebuilt
`.pbix` binary and has **not been opened in Power BI Desktop** in this environment.

## 1. Load the customer CSV on Windows

1. Install/update **Power BI Desktop** for Windows.
2. Extract the **entire repository** into a normal local folder, such as
   `C:\Users\you\Documents\customer-acquisition-segmentation`.
3. Locate `data/public/customer_analytics.csv` and choose **Copy as path** in
   Windows File Explorer. The CSV is a reduced analytical extract; read the
   root README's data-publication warning before committing publicly.
4. Open `powerbi/Customer_Acquisition.pbip` in Power BI Desktop.
5. Choose **Transform data > Edit parameters**; set **Customer_CSV_Path** to
   the full path of `customer_analytics.csv` (e.g.,
   `C:\Users\you\Documents\customer-acquisition-segmentation\data\public\customer_analytics.csv`).
   Remove any surrounding quote characters that Windows Copy as path adds.
6. Select **Apply changes / Refresh** and, if prompted, authorize the local
   File data source at the appropriate privacy level.
7. The report should populate the pages with measures and filtering.
   Select **File > Save As** and choose PBIX if you want a `.pbix` file.

**If the file path cannot be edited because the first load fails:**
Open `Customer_Acquisition.SemanticModel/definition/expressions.tmdl` in a text
editor, replace the default value of `Customer_CSV_Path` with your absolute path,
then reopen the PBIP. Path strings in Power Query use ordinary backslashes.

## Layout preview

![Dashboard design preview](assets/powerbi_dashboard_preview.png)

*The PNG above illustrates the desired visual layout from actual aggregates; it is
not a screenshot from an executed Power BI Desktop report.*

## Pages and visuals

| Page | Purpose | Main visuals |
|---|---|---|
| Executive Overview | Customer size, country / segment mix and cost | 4 KPI cards, 3 charts, 3 slicers |
| Customer Segmentation | Age distribution, cost bands, mix by country | 4 KPI cards, 4 charts |
| Data Quality | Postal-format mismatch review | 4 KPI cards, 3 charts, 1 slicer |

The slicers should cross-filter visuals on their pages. Charts built from a
single fact table respond to selections. In Desktop, customize cross-page sync
using **View > Sync slicers** if wanted.

## DAX metrics included

- `Total Customers`: count of customer records
- `Countries Covered`, `Segments Covered`: distinct counts
- `Average Acquisition Cost`, `Median Acquisition Cost`: descriptive cost statistics
- `Total Recorded Cost`: sum of individual cost entries, **not** campaign spend
- `Average Customer Age`
- `Postal Mismatch Records`: formatting heuristic flag count
- `Postal Checked Records`: excludes `not_checked`
- `Postal Mismatch Rate`: mismatches / checked records, excluding UAE not-checked records
- `Customers in Consumer Segment`

## Business guardrails

- Original CSV has **no acquisition date, campaign, channel, sales, retention, or revenue**.
  Do not call average per-customer cost *channel CAC* or calculate ROI/CLV.
- **Cost currency not defined**. Visuals explicitly say *units*, not USD/LKR.
- Postal format flags check the **pattern**, not actual address validity.
- Country and segment patterns in this dataset are descriptive, not causal.
- A `.pbip` is the appropriate text-based, diffable GitHub artifact. A `.pbix`
  can only be saved after opening the project in Power BI Desktop.

## Key definitions

Data source: `../data/public/customer_analytics.csv`
(with a local file path set through `Customer_CSV_Path`).

Power Query creates age groups (18-24 through 65+) and fixed acquisition cost
bands (<20, 20–39.99, 40–59.99, 60+) while importing the original 8 columns.
Both resulting group/band fields are sorted using corresponding order columns.

## Repository structure

```text
powerbi/
  README.md
  Customer_Acquisition.pbip
  Customer_Acquisition.Report/
    definition.pbir
    definition/report.json
    definition/pages/.../visuals/.../visual.json
    StaticResources/...
  Customer_Acquisition.SemanticModel/
    definition.pbism
    definition/model.tmdl
    definition/expressions.tmdl
    definition/tables/Customers.tmdl
```

**Validation status:** Source CSV/metrics and JSON structure can be checked
programmatically; final rendering, refresh and `.pbix` conversion require Power
BI Desktop and must be tested after opening. The checked-in project is a
Power BI source project, not a screenshot passed off as a finished `.pbix`.
