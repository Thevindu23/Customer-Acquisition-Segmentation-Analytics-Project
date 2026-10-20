"""Customer acquisition and segmentation analytics portfolio project.

Run from any directory:
    python src/analyze_customers.py

All metrics derive from the uploaded source data. This dataset does not specify
currency, dates, revenue, or channel information; avoid inventing these.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'data' / 'public' / 'customer_analytics.csv'
OUTPUTS = ROOT / 'reports'
CLEANED = ROOT / 'data' / 'processed' / 'customers_cleaned.csv'
REQUIRED = [
    'record_id', 'customer_age', 'gender', 'customer_segment',
    'customer_country', 'region', 'customer_acquisition_cost', 'postal_format_check',
]
POSTAL_CHECK_COUNTRIES = ['Australia', 'Canada', 'Germany', 'India', 'UK', 'USA']

AGE_BINS = [17, 24, 34, 44, 54, 64, np.inf]
AGE_LABELS = ['18–24', '25–34', '35–44', '45–54', '55–64', '65+']
INK = '#1c3152'
BLUE = '#3763c9'
TEAL = '#1f9984'
ORANGE = '#e7a54d'


def read_data(filepath: Path) -> pd.DataFrame:
    """Load the reviewable analytics extract, not the private customer master."""
    df = pd.read_csv(filepath, dtype={'record_id': 'string'}, low_memory=False)
    missing_cols = set(REQUIRED).difference(df.columns)
    if missing_cols:
        raise ValueError('Missing required columns: ' + ', '.join(sorted(missing_cols)))
    for col in ['record_id', 'gender', 'customer_segment', 'customer_country',
                'region', 'postal_format_check']:
        df[col] = df[col].astype('string').str.strip().replace('', pd.NA)
    df['customer_age'] = pd.to_numeric(df['customer_age'], errors='coerce')
    df['customer_acquisition_cost'] = pd.to_numeric(df['customer_acquisition_cost'], errors='coerce')
    return df


def data_quality(df: pd.DataFrame) -> dict:
    """Audit public fields and summarize postal patterns from source-derived flags."""
    allowed_flags = {'matches_pattern', 'format_mismatch', 'not_checked'}
    invalid_flags = ~df['postal_format_check'].isin(allowed_flags)
    result = {
        'total_records': int(len(df)),
        'total_columns_in_analysis_extract': len(REQUIRED),
        'duplicate_rows': int(df.duplicated().sum()),
        'duplicate_record_ids': int(df['record_id'].duplicated().sum()),
        'missing_cells': int(df[REQUIRED].isna().sum().sum()),
        'missing_by_column': {col:int(n) for col,n in df[REQUIRED].isna().sum().items()},
        'invalid_age_outside_18_to_110': int((~df['customer_age'].between(18,110)).sum()),
        'negative_acquisition_costs': int((df['customer_acquisition_cost'] < 0).sum()),
        'invalid_record_ids_format': int((~df['record_id'].str.fullmatch(r'ANON-\d{6}', na=False)).sum()),
        'unrecognized_postal_check_flags': int(invalid_flags.sum()),
        'postal_code_format_review_by_country': {},
    }
    for country in POSTAL_CHECK_COUNTRIES:
        grp = df.loc[df['customer_country'].eq(country), 'postal_format_check']
        result['postal_code_format_review_by_country'][country] = {
            'rows_checked': int(len(grp)),
            'format_mismatches': int(grp.eq('format_mismatch').sum()),
        }
    result['postal_code_format_mismatches_reviewed_countries'] = int(sum(
        v['format_mismatches'] for v in result['postal_code_format_review_by_country'].values()
    ))
    result['postal_code_note'] = (
        'Flags were derived from the private source before removing postal codes. '
        'They are formatting heuristics, not evidence that an address exists. '
        'UAE postal codes were not checked; country/state/city match is not verified.'
    )
    return result


def clean_and_enrich(df: pd.DataFrame) -> pd.DataFrame:
    # Do not silently discard records or infer personal information.
    if df['record_id'].isna().any() or df['record_id'].duplicated().any():
        raise ValueError('record_id must be present and unique. Investigate source before continuing.')
    if df['customer_age'].isna().any() or df['customer_acquisition_cost'].isna().any():
        raise ValueError('Age or cost is missing/non-numeric. Investigate source before continuing.')
    if (~df['customer_age'].between(18,110)).any() or (df['customer_acquisition_cost'] < 0).any():
        raise ValueError('Invalid customer age or negative cost. Investigate source before continuing.')
    if (~df['postal_format_check'].isin({'matches_pattern', 'format_mismatch', 'not_checked'})).any():
        raise ValueError('Unexpected postal format flag. Review input.')
    result = df.copy()
    result['age_group'] = pd.cut(result['customer_age'], bins=AGE_BINS, labels=AGE_LABELS).astype('string')
    quartiles = result['customer_acquisition_cost'].quantile([.25,.5,.75]).to_numpy()
    boundaries = [-np.inf, *quartiles, np.inf]
    result['acquisition_cost_quartile'] = pd.cut(
        result['customer_acquisition_cost'], bins=boundaries,
        labels=['Q1 · Lowest', 'Q2', 'Q3', 'Q4 · Highest'], include_lowest=True
    ).astype('string')
    return result


def make_summary(df: pd.DataFrame, by: str) -> pd.DataFrame:
    result = (df.groupby(by, observed=True, dropna=False)
      .agg(customers=('record_id','size'), total_acquisition_cost=('customer_acquisition_cost','sum'),
           average_acquisition_cost=('customer_acquisition_cost','mean'),
           median_acquisition_cost=('customer_acquisition_cost','median'),
           average_age=('customer_age','mean'))
      .reset_index())
    result['customer_share_pct'] = 100*result['customers']/len(df)
    result['acquisition_cost_share_pct'] = 100*result['total_acquisition_cost']/df['customer_acquisition_cost'].sum()
    return result.sort_values(['customers',by], ascending=[False,True]).reset_index(drop=True)


def hypothesis_tests(df: pd.DataFrame) -> dict:
    y = df['customer_acquisition_cost']
    outcome = {}
    for col in ['customer_segment', 'customer_country', 'region', 'gender']:
        arr = [g['customer_acquisition_cost'].to_numpy() for _, g in df.groupby(col)]
        f,p = stats.f_oneway(*arr)
        between = sum(len(g)*(g.mean()-y.mean())**2 for g in arr)
        outcome[f'anova_{col}'] = {
            'f_statistic': float(f), 'p_value': float(p),
            'eta_squared': float(between/((y-y.mean())**2).sum()),
        }
    corr, p = stats.pearsonr(df['customer_age'], y)
    outcome['age_vs_acquisition_cost_pearson'] = {'r': float(corr), 'p_value':float(p)}
    ct = pd.crosstab(df['customer_country'],df['customer_segment'])
    chi2,p,dof,expected = stats.chi2_contingency(ct)
    cramer = np.sqrt(chi2/(len(df)*min(ct.shape[0]-1,ct.shape[1]-1)))
    outcome['country_vs_segment_chi_square'] = {
        'chi_squared':float(chi2),'p_value':float(p),'degrees_of_freedom':int(dof),
        'cramers_v':float(cramer), 'minimum_expected_cell_count':float(expected.min())
    }
    return outcome


def set_theme() -> None:
    plt.rcParams.update({'figure.facecolor':'white', 'axes.facecolor':'white',
      'axes.spines.top':False, 'axes.spines.right':False,
      'axes.titlesize':15, 'axes.titleweight':'bold', 'axes.titlecolor': INK,
      'axes.labelcolor':INK, 'xtick.color':'#52657d', 'ytick.color':'#52657d',
      'font.size':10, 'savefig.bbox':'tight', 'savefig.dpi':180})


def save_plot(path:Path) -> None:
    plt.tight_layout(pad=2)
    plt.savefig(path, dpi=180)
    plt.close()


def create_charts(df:pd.DataFrame, tables:dict, output:Path) -> None:
    set_theme()
    output.mkdir(parents=True, exist_ok=True)
    country = tables['country'].sort_values('customers')
    fig,ax=plt.subplots(figsize=(9,5))
    bars=ax.barh(country['customer_country'],country['customers'],color=BLUE)
    ax.bar_label(bars,fmt='{:,.0f}',padding=5)
    ax.set_xlim(0,country['customers'].max()*1.19)
    ax.set_title('Customer base by country')
    ax.set_xlabel('Number of customers')
    save_plot(output/'01_customers_by_country.png')

    seg = tables['segment'].sort_values('customers')
    fig,ax=plt.subplots(figsize=(8,4.4))
    bars=ax.barh(seg['customer_segment'],seg['customers'],color=TEAL)
    ax.bar_label(bars,fmt='{:,.0f}',padding=5)
    ax.set_xlim(0,seg['customers'].max()*1.2)
    ax.set_title('Customer mix by segment')
    ax.set_xlabel('Number of customers')
    save_plot(output/'02_customers_by_segment.png')

    fig,ax=plt.subplots(figsize=(9,4.7))
    ax.hist(df['customer_acquisition_cost'], bins=30, color=BLUE, alpha=.88, edgecolor='white')
    ax.axvline(df['customer_acquisition_cost'].mean(),color=ORANGE,linewidth=2,linestyle='--',
      label=f"Overall mean: {df['customer_acquisition_cost'].mean():.2f}")
    ax.set(title='Distribution of customer acquisition costs', xlabel='Acquisition cost (currency unspecified)',ylabel='Customers')
    ax.legend(frameon=False)
    save_plot(output/'03_acquisition_cost_distribution.png')

    fig,ax=plt.subplots(figsize=(9,4.7))
    vals=[df.loc[df.customer_segment.eq(x),'customer_acquisition_cost'] for x in sorted(df.customer_segment.unique())]
    ax.boxplot(vals, tick_labels=sorted(df.customer_segment.unique()), showfliers=False,
               patch_artist=True,boxprops={'facecolor':'#cbdaf4','color': BLUE},
               medianprops={'color':INK,'linewidth':2},
               whiskerprops={'color':BLUE},capprops={'color':BLUE})
    ax.set(title='Acquisition cost spread by segment', xlabel='Segment', ylabel='Acquisition cost (currency unspecified)')
    save_plot(output/'04_acquisition_cost_by_segment.png')

    fig,ax=plt.subplots(figsize=(9,4.7))
    agecounts=df['age_group'].value_counts().reindex(AGE_LABELS)
    bars=ax.bar(agecounts.index,agecounts.values,color=TEAL)
    ax.bar_label(bars,fmt='{:,.0f}',padding=3)
    ax.set_ylim(0,agecounts.max()*1.13)
    ax.set(title='Customer age distribution',xlabel='Age group',ylabel='Customers')
    save_plot(output/'05_customer_age_groups.png')

    fig,ax=plt.subplots(figsize=(9,5))
    country_cost=tables['country'].sort_values('average_acquisition_cost')
    bars=ax.barh(country_cost.customer_country,country_cost.average_acquisition_cost,color=ORANGE)
    ax.bar_label(bars,fmt='%.2f',padding=5)
    ax.set_xlim(0,country_cost.average_acquisition_cost.max()*1.19)
    ax.axvline(df.customer_acquisition_cost.mean(),color=INK,linestyle='--',linewidth=1.5,label='Overall mean')
    ax.set(title='Average acquisition cost by country',xlabel='Mean acquisition cost (currency unspecified)')
    ax.legend(frameon=False)
    save_plot(output/'06_average_cost_by_country.png')

    cross=pd.crosstab(df.customer_country,df.customer_segment,normalize='index').mul(100)
    fig,ax=plt.subplots(figsize=(10,5.3))
    bottom=np.zeros(len(cross))
    palette=[INK,BLUE,TEAL,ORANGE]
    for color,col in zip(palette,cross.columns):
        vals=cross[col].to_numpy()
        ax.barh(cross.index,vals,left=bottom,label=col,color=color)
        bottom+=vals
    ax.set(title='Customer segment composition by country',xlabel='Within-country share (%)',xlim=(0,100))
    ax.legend(ncol=4,loc='lower center',bbox_to_anchor=(.5,-.27),frameon=False)
    save_plot(output/'07_segment_mix_by_country.png')

    by_age = df.groupby('customer_age')['customer_acquisition_cost'].agg(['mean','size']).reset_index()
    fig,ax=plt.subplots(figsize=(9,4.7))
    ax.plot(by_age['customer_age'],by_age['mean'],color=BLUE,linewidth=2,marker='.',markersize=5)
    ax.axhline(df.customer_acquisition_cost.mean(),color=ORANGE,linestyle='--',label='Overall mean')
    ax.set(title='Mean acquisition cost across ages (descriptive)',xlabel='Customer age (years)',ylabel='Mean acquisition cost')
    ax.legend(frameon=False)
    save_plot(output/'08_cost_by_age.png')


def write_report(df:pd.DataFrame,tables:dict,dq:dict,tests:dict,path:Path) -> None:
    n=len(df)
    avg=df.customer_acquisition_cost.mean()
    total=df.customer_acquisition_cost.sum()
    usa=tables['country'].set_index('customer_country').loc['USA']
    consumer=tables['segment'].set_index('customer_segment').loc['Consumer']
    agem=df.customer_age.mean()
    segment_stats=tests['anova_customer_segment']
    country_stats=tests['anova_customer_country']
    mismatch=dq['postal_code_format_mismatches_reviewed_countries']
    segments=tables['segment'].sort_values('customers',ascending=False)
    countries=tables['country'].sort_values('customers',ascending=False)
    quartiles=df.customer_acquisition_cost.quantile([.25,.5,.75]).tolist()
    fmt=lambda x:f'{x:,.2f}'
    table_seg='\n'.join(f'| {r.customer_segment} | {int(r.customers):,} | {r.customer_share_pct:.1f}% | {r.average_acquisition_cost:.2f} |'
      for r in segments.itertuples())
    table_country='\n'.join(f'| {r.customer_country} | {int(r.customers):,} | {r.customer_share_pct:.1f}% | {r.average_acquisition_cost:.2f} |'
      for r in countries.itertuples())
    s=f'''# Customer Acquisition and Segmentation — Analysis Report

## Executive summary

The analytical extract contains **{n:,} customer records** in **{df.customer_country.nunique()} countries** across **{df.customer_segment.nunique()} customer segments**.
Average recorded customer acquisition cost is **{fmt(avg)} units**; total recorded acquisition cost is **{fmt(total)} units**. The monetary currency is **not specified**.
Average customer age is **{agem:.1f} years**.

The **USA** contributes **{int(usa.customers):,} customers ({usa.customer_share_pct:.1f}%)** and **Consumer** is the largest segment with **{int(consumer.customers):,} customers ({consumer.customer_share_pct:.1f}%)**. These groups also account for large *total* recorded acquisition cost because they contain more customers; their *average* costs are similar to other groups.

## Business questions

1. Which countries and segments account for the largest shares of acquired customers?
2. How do recorded acquisition costs vary across countries, segments, genders, and regions?
3. Is customer age associated with acquisition cost?
4. What data-quality limits affect business decisions?

## KPIs

| Metric | Value |
| --- | ---: |
| Customer records | {n:,} |
| Overall mean recorded acquisition cost | {fmt(avg)} cost units |
| Median recorded acquisition cost | {fmt(df.customer_acquisition_cost.median())} cost units |
| Total of recorded acquisition costs | {fmt(total)} cost units |
| Mean customer age | {agem:.1f} years |
| Countries | {df.customer_country.nunique()} |
| Customer segments | {df.customer_segment.nunique()} |
| Customer acquisition cost interquartile range | {quartiles[0]:.2f}–{quartiles[2]:.2f} units |

## Customer segments

| Segment | Customers | Customer share | Mean recorded acquisition cost |
| --- | ---: | ---: | ---: |
{table_seg}

## Country profile

| Country | Customers | Customer share | Mean recorded acquisition cost |
| --- | ---: | ---: | ---: |
{table_country}

## Statistical exploration

- **Cost vs. segment:** one-way ANOVA F={segment_stats['f_statistic']:.3f}, p={segment_stats['p_value']:.3f}, eta-squared={segment_stats['eta_squared']:.5f}. This sample shows no compelling evidence of substantial mean-cost differences across segments.
- **Cost vs. country:** one-way ANOVA F={country_stats['f_statistic']:.3f}, p={country_stats['p_value']:.3f}, eta-squared={country_stats['eta_squared']:.5f}. Country explains a negligible fraction of the observed cost variation in this sample.
- **Cost vs. age:** Pearson r={tests['age_vs_acquisition_cost_pearson']['r']:.5f}, p={tests['age_vs_acquisition_cost_pearson']['p_value']:.3f}. There is no meaningful linear relationship in these records.
- **Country vs. segment:** chi-square p={tests['country_vs_segment_chi_square']['p_value']:.3f}; Cramér's V={tests['country_vs_segment_chi_square']['cramers_v']:.4f}. The sample shows no meaningful country/segment association.

These tests are exploratory and assume sufficiently representative and reliable data. Non-significant p-values do **not** prove groups are identical; statistical tests do not establish causality.

## Data quality and limitations

- **No missing data and no duplicate analysis IDs:** {dq['missing_cells']:,} missing extract cells and {dq['duplicate_record_ids']:,} duplicate analysis IDs.
- **Postal-code format concern:** {mismatch:,} ({100*mismatch/n:.1f}%) rows were flagged during basic postal-code *format* checks of the private source. Canada and the UK typically use alphanumeric formats; India typically uses six digits; Australia typically uses four. This is a format-screening result only, not postcode-level verification.
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
'''
    path.write_text(s,encoding='utf-8')


def create_sqlite(df:pd.DataFrame,path:Path) -> None:
    with sqlite3.connect(path) as con:
        df.to_sql('customers',con,if_exists='replace',index=False)
        con.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_record_id ON customers(record_id)')
        con.execute('CREATE INDEX IF NOT EXISTS idx_country ON customers(customer_country)')
        con.execute('CREATE INDEX IF NOT EXISTS idx_segment ON customers(customer_segment)')


def main() -> None:
    parser=argparse.ArgumentParser(description='Run customer acquisition analytics')
    parser.add_argument('--input',type=Path,default=INPUT,help='Input customer CSV')
    args=parser.parse_args()
    (ROOT/'data'/'processed').mkdir(parents=True,exist_ok=True)
    (OUTPUTS/'tables').mkdir(parents=True,exist_ok=True)
    (OUTPUTS/'charts').mkdir(parents=True,exist_ok=True)
    (ROOT/'sql').mkdir(parents=True,exist_ok=True)

    raw=read_data(args.input)
    dq=data_quality(raw)
    df=clean_and_enrich(raw)
    df.to_csv(CLEANED,index=False)
    tables={
      'country':make_summary(df,'customer_country'),
      'segment':make_summary(df,'customer_segment'),
      'region':make_summary(df,'region'),
      'gender':make_summary(df,'gender'),
      'age_group':make_summary(df,'age_group'),
    }
    for name,table in tables.items():
        table.to_csv(OUTPUTS/'tables'/f'{name}_summary.csv',index=False,float_format='%.5f')
    pd.crosstab(df['customer_country'],df['customer_segment']).to_csv(OUTPUTS/'tables'/'country_segment_counts.csv')
    pd.crosstab(df['customer_country'],df['customer_segment'],normalize='index').mul(100).to_csv(
        OUTPUTS/'tables'/'country_segment_pct.csv',float_format='%.4f')
    overall=pd.DataFrame([{'customers':len(df),'countries':df.customer_country.nunique(),
      'segments':df.customer_segment.nunique(),'average_acquisition_cost':df.customer_acquisition_cost.mean(),
      'median_acquisition_cost':df.customer_acquisition_cost.median(),
      'total_recorded_acquisition_cost':df.customer_acquisition_cost.sum(),
      'average_age':df.customer_age.mean()}])
    overall.to_csv(OUTPUTS/'tables'/'overall_kpis.csv',index=False,float_format='%.6f')
    tests=hypothesis_tests(df)
    (OUTPUTS/'data_quality_report.json').write_text(json.dumps(dq,indent=2),encoding='utf-8')
    (OUTPUTS/'statistical_tests.json').write_text(json.dumps(tests,indent=2),encoding='utf-8')
    create_charts(df,tables,OUTPUTS/'charts')
    write_report(df,tables,dq,tests,OUTPUTS/'analysis_report.md')
    create_sqlite(df,ROOT/'sql'/'customers.sqlite')
    print('Complete:',len(df),'records;',len(tables),'summary dimensions; 8 charts.')
    print('Overall average acquisition cost:',round(df.customer_acquisition_cost.mean(),4),'units')
    print('Generated project artifacts in',ROOT)


if __name__ == '__main__':
    main()
