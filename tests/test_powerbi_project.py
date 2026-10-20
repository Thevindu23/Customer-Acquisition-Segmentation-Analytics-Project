"""Lightweight structural tests for the checked-in Power BI source project.

These tests DO NOT replace opening and refreshing in Power BI Desktop.
"""
import json
import re
import unittest
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PBI = ROOT / 'powerbi'
REPORT = PBI / 'Customer_Acquisition.Report'
MODEL = PBI / 'Customer_Acquisition.SemanticModel'
DEFINITION = REPORT / 'definition'


class PowerBIStructure(unittest.TestCase):
    def test_report_and_model_metadata(self):
        pbip = json.loads((PBI / 'Customer_Acquisition.pbip').read_text())
        self.assertEqual(pbip['artifacts'][0]['report']['path'], REPORT.name)
        pbir = json.loads((REPORT / 'definition.pbir').read_text())
        self.assertEqual(pbir['datasetReference']['byPath']['path'], '../'+MODEL.name)
        self.assertTrue((MODEL/'definition.pbism').is_file())
        for f in REPORT.rglob('*.json'):
            self.assertIsInstance(json.loads(f.read_text()), dict)

    def test_three_pages_and_real_visuals(self):
        pages = json.loads((DEFINITION/'pages/pages.json').read_text())
        self.assertEqual(len(pages['pageOrder']), 3)
        self.assertEqual(len(list((DEFINITION/'pages').rglob('visual.json'))), 26)
        found = set()
        for pageid in pages['pageOrder']:
            p=DEFINITION/'pages'/pageid
            self.assertTrue(p.is_dir())
            page=json.loads((p/'page.json').read_text())
            self.assertEqual(page['name'],pageid)
            self.assertEqual((page['width'],page['height']),(1280,720))
            for vf in p.rglob('visual.json'):
                visual=json.loads(vf.read_text())
                self.assertEqual(visual['name'],vf.parent.name)
                self.assertNotIn(visual['name'],found)
                found.add(visual['name'])
                box=visual['position']
                self.assertLessEqual(box['x']+box['width'],1280)
                self.assertLessEqual(box['y']+box['height'],720)
                self.assertTrue(visual['visual']['query']['queryState'])

    def test_dax_measures_and_source_path(self):
        tmdl = (MODEL/'definition/tables/Customers.tmdl').read_text()
        self.assertIn('source =',tmdl)
        self.assertIn('Csv.Document(File.Contents(Customer_CSV_Path)',tmdl)
        self.assertIn("measure 'Postal Mismatch Rate'",tmdl)
        self.assertIn('"format_mismatch"',tmdl)
        parameter = (MODEL/'definition/expressions.tmdl').read_text()
        self.assertIn('expression Customer_CSV_Path',parameter)
        self.assertIn('IsParameterQuery=true',parameter)
        self.assertIn('sourceColumn: customer_acquisition_cost',tmdl)
        self.assertNotIn('customer_name',tmdl.lower())
        self.assertNotIn('postal_code',tmdl.lower())

    def test_visual_measures_all_exist(self):
        tmdl=(MODEL/'definition/tables/Customers.tmdl').read_text()
        measures=set(re.findall(r"(?m)^\tmeasure '([^']+)'",tmdl))
        cols=set(re.findall(r"(?m)^\tcolumn '([^']+)'",tmdl))
        for vf in (DEFINITION/'pages').rglob('visual.json'):
            vis=json.loads(vf.read_text())
            for role in vis['visual']['query']['queryState'].values():
                for proj in role['projections']:
                    fields=proj['field']
                    kind, f = next(iter(fields.items()))
                    if kind=='Measure': self.assertIn(f['Property'],measures)
                    if kind=='Column': self.assertIn(f['Property'],cols)

    def test_kpi_values_match_python_project(self):
        df=pd.read_csv(ROOT/'data/public/customer_analytics.csv')
        self.assertEqual(len(df),25000)
        self.assertEqual(df.customer_country.nunique(),7)
        self.assertEqual(df.customer_segment.nunique(),4)
        self.assertAlmostEqual(df.customer_acquisition_cost.mean(),42.1597504)
        self.assertEqual((df.postal_format_check=='format_mismatch').sum(),7254)
        self.assertEqual((df.postal_format_check!='not_checked').sum(),24225)


if __name__=='__main__':
    unittest.main()
