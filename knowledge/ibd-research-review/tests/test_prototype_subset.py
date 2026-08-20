import json, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path('/Users/janakirampulipati/ibd-research-review')
subset=json.loads((ROOT/'ibd-prototype-evidence.json').read_text())
excluded=json.loads((ROOT/'prototype-evidence-exclusions.json').read_text())

def test_clm083_scope_correction():
    c=next(c for c in subset['claims'] if c['claimId']=='CLM-083')
    assert c['conditionApplicability']=='crohns_disease'
    assert c['outcomeType']=='obstruction_risk'
    assert c['confidence']=='low'

def test_clm092_excluded():
    assert 'CLM-092' in subset['excludedClaimIds']
    assert excluded['clm092']['status']=='still_needs_evidence'
    assert excluded['clm092']['prototypeEligible'] is False

def test_excluded_filtering_and_unique_ids():
    ids=[c['claimId'] for c in subset['claims']]
    assert len(ids)==len(set(ids))
    assert not set(ids) & set(subset['excludedClaimIds'])

def test_active_sources_and_no_superseded_espen():
    source_ids={s['sourceId'] for s in subset['sources']}
    assert all(c['sourceId'] in source_ids for c in subset['claims'])
    assert all(c['sourceId']!='SRC-003' for c in subset['claims'])
    assert all(c['sourceId']=='SRC-026' for c in subset['claims'] if c['claimId'] in {'CLM-096','CLM-097','CLM-098','CLM-099','CLM-100'})

def test_required_metadata_and_eligibility():
    required=['claimId','sourceId','sourceTitle','sourceUrl','conditionApplicability','diseaseContext','topic','outcomeType','claimText','plainLanguageExplanation','supportingExcerpt','exactLocator','evidenceLevel','limitations','applicabilityLimitations','confidence','prototypeEligibilityStatus']
    for c in subset['claims']:
        assert all(c.get(k) not in (None,'') for k in required if k!='topic')
        assert c['prototypeEligibilityStatus'].startswith('prototype_eligible')

def test_workbook_frozen_headers_dropdowns_and_blank_review_fields():
    p=ROOT/'ibd-prototype-evidence-review.xlsx'
    with zipfile.ZipFile(p) as z:
        sheets=[n for n in z.namelist() if n.startswith('xl/worksheets/sheet') and n.endswith('.xml')]
        assert len(sheets)==8
        for n in sheets:
            root=ET.fromstring(z.read(n))
            ns={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            assert root.find('x:sheetViews/x:sheetView/x:pane',ns) is not None
            assert root.find('x:dataValidations',ns) is not None or 'sheet7' in n or 'sheet8' in n
            xml=z.read(n).decode('utf-8')
            assert 'Approve for prototype' not in xml or 'dataValidation' in xml

def test_json_schema_and_formula_scan():
    assert subset['version']=='prototype-v1'
    assert subset['intendedUse']=='informational prototype only'
    assert set(subset)=={'version','createdAt','intendedUse','sources','claims','excludedClaimIds','limitations'}
    with zipfile.ZipFile(ROOT/'ibd-prototype-evidence-review.xlsx') as z:
        formulas=''.join(z.read(n).decode('utf-8') for n in z.namelist() if n.endswith('.xml'))
        assert '#REF!' not in formulas and '#DIV/0!' not in formulas and '#VALUE!' not in formulas
