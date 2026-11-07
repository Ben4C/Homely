"""Developer 5 regression tests: exact finance, source integrity and safe SDK failures."""
import asyncio
import sys
import types
from datetime import date
from decimal import Decimal
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError
from app.main import app
from app.core.claude_client import SourceDocument, claude_json, document_blocks
from app.domains.admin.schemas import ReviewItem
from app.domains.admin.service import integrity_flags

client = TestClient(app)

# Purpose: Build a minimal exact-decimal request. Inputs: overrides; outputs: compatible legacy pro forma.
def financials(**overrides):
    return {**dict.fromkeys(['cost_to_create_usd','affordable_buyer_proceeds_usd','public_development_subsidies_usd','earned_project_revenue_usd','nonprofit_donations_usd','employer_project_sponsorship_usd'],'0.00'),**overrides}

# Purpose: Verify exact cents, zero and surplus. Inputs: decimal inputs; outputs: exact nonnegative totals.
@pytest.mark.parametrize('cost,buyer,revenue,gap,surplus',[
    ('0.30','0.10','0.20','0.00','0.00'),('100.00','0.00','0.00','100.00','0.00'),
    ('0.00','0.00','0.00','0.00','0.00'),('10.00','12.00','0.00','0.00','2.00')])
def test_exact_finance(cost,buyer,revenue,gap,surplus):
    response=client.post('/api/v1/projects/gap',json=financials(cost_to_create_usd=cost,affordable_buyer_proceeds_usd=buyer,earned_project_revenue_usd=revenue))
    assert response.status_code==200
    assert response.json()['remaining_gap_usd']==gap
    assert response.json()['surplus_usd']==surplus

# Purpose: Exclude impossible or excessive legacy amounts. Inputs: invalid decimals; outputs: HTTP 422.
@pytest.mark.parametrize('amount',['NaN','Infinity','-Infinity','-1','0.001','100000000000000.00','abc'])
def test_invalid_amounts(amount):
    assert client.post('/api/v1/projects/gap',json=financials(cost_to_create_usd=amount)).status_code==422

# Purpose: Verify source classifications and itemized cost precedence. Inputs: mixed funding; outputs: no speculative cash.
def test_classified_sources_and_costs():
    sources=[{'id':f's{i}','category':'EMPLOYER','amount_usd':'10.00','status':status,'funding_track':track,'contribution_kind':kind}
             for i,(status,track,kind) in enumerate([('CONFIRMED','DEVELOPMENT','CASH'),('RECEIVED','DEVELOPMENT','CASH'),('PLEDGED','DEVELOPMENT','CASH'),('UNVERIFIED','DEVELOPMENT','CASH'),('CONFIRMED','BUYER','CASH'),('RECEIVED','DEVELOPMENT','IN_KIND')])]
    body=financials(cost_to_create_usd='999.00',itemized_costs={'land':'50.01','construction':'49.99'},funding_sources=sources)
    response=client.post('/api/v1/projects/gap',json=body)
    assert response.status_code==200,response.text
    result=response.json()
    assert result['cost_to_create_usd']=='100.00'
    assert result['total_funding_usd']=='20.00'
    assert result['remaining_gap_usd']=='80.00'
    assert result['potential_funding_usd']=='20.00'
    assert result['excluded_funding_usd']=='20.00'
    assert result['financing_identified_percent']=='20.00'
    body['funding_sources'].append(sources[0])
    assert client.post('/api/v1/projects/gap',json=body).status_code==422

# Purpose: Guard against source ID collisions with legacy fields. Inputs: matching name; outputs: additive distinct entries.
def test_source_id_cannot_overwrite_legacy_financing():
    body=financials(cost_to_create_usd='10.00',nonprofit_donations_usd='1.00',funding_sources=[{'id':'nonprofit_donations_usd','category':'OTHER','amount_usd':'2.00','status':'CONFIRMED'}])
    result=client.post('/api/v1/projects/gap',json=body).json()
    assert result['total_funding_usd']=='3.00'

# Purpose: Reject ambiguous and unsupported documents. Inputs: empty/dual/malformed content; outputs: validation errors.
@pytest.mark.parametrize('fields',[{'document_text':' '},{'pdf_base64':''},{'document_text':'x','pdf_base64':'abc'},{'document_text':'','pdf_base64':'abc'},{'pdf_base64':'invalid'},{'document_text':'x'*40001}])
def test_invalid_documents(fields):
    with pytest.raises(ValidationError):
        SourceDocument(source_label='sample',consent_to_send_to_claude=True,**fields)

# Purpose: Prevent validation bypass before submission. Inputs: constructed unconsented object; outputs: rejected source.
def test_document_blocks_revalidates():
    source=SourceDocument.model_construct(source_label='sample',document_text='sample',pdf_base64=None,consent_to_send_to_claude=False)
    with pytest.raises(ValidationError):
        document_blocks(source)

class Analysis(BaseModel):
    explanation: str

# Purpose: Verify provider timeout, refusal and schema failures are sanitized and resources closed.
# Inputs: fake SDK outcomes; outputs: safe 502 without secret/provider payload.
@pytest.mark.parametrize('outcome',['timeout','invalid','empty'])
def test_sdk_failure_sanitized_and_closed(monkeypatch,outcome):
    closed=[]
    class Messages:
        # Purpose: Simulate provider failure. Inputs: SDK arguments; outputs: mocked response or timeout.
        async def parse(self,**kwargs):
            if outcome=='timeout': raise TimeoutError('secret-provider-diagnostics')
            return types.SimpleNamespace(parsed_output={} if outcome=='invalid' else None)
    class FakeClient:
        # Purpose: Supply SDK mock. Inputs: configuration; outputs: fake messages client.
        def __init__(self,**kwargs): self.messages=Messages()
        # Purpose: Track transport cleanup. Inputs: none; outputs: closed marker.
        async def close(self): closed.append(True)
    monkeypatch.setenv('ANTHROPIC_API_KEY','secret-placeholder')
    monkeypatch.setitem(sys.modules,'anthropic',types.SimpleNamespace(AsyncAnthropic=FakeClient))
    with pytest.raises(HTTPException) as error:
        asyncio.run(claude_json('Explain',[{'type':'text','text':'sample'}],Analysis))
    assert error.value.status_code==502
    assert 'secret' not in error.value.detail
    assert closed==[True]

# Purpose: Detect stale, expired and unverified metadata. Inputs: fixed dates; outputs: manual flags without domain mutations.
def test_program_integrity_dates():
    item=ReviewItem(id='sample',category='PROGRAM_SOURCE',reason='review',status='PENDING',source_verified_on=date(2025,1,1),application_deadline=date(2025,2,1))
    flags=integrity_flags(item,date(2026,11,7))
    assert len(flags)==3
    item.source_verified_on=date(2026,11,7)
    item.application_deadline=date(2026,11,7)
    item.eligibility_verified=True
    assert integrity_flags(item,date(2026,11,7))==[]

# Purpose: Confirm public synthetic queue cannot enable privileged writes. Inputs: GET/POST; outputs: disabled decisions and no write endpoint.
def test_admin_decisions_remain_unavailable():
    body=client.get('/api/v1/admin/review-queue').json()
    assert body['decisions_enabled'] is False
    assert body['metrics']['pending_organization_verifications']==1
    assert body['warnings']
    assert client.post('/api/v1/admin/review-queue',json={}).status_code==405

# Purpose: Reject unsupported content before a provider call. Inputs: invalid blocks; outputs: safe 422.
@pytest.mark.parametrize('content',[[],[{'type':'image','source':{}}],[{'type':'text','text':' '}],[{'type':'text','text':'x'*100001}],[{'type':'document','source':{'type':'url','url':'https://example.com/private'}}]])
def test_content_block_validation(content):
    from app.core.claude_client import validate_content
    with pytest.raises(HTTPException) as error:
        validate_content(content)
    assert error.value.status_code==422

# Purpose: Check deterministic hypothetical scenarios never alter actual totals or include buyer aid.
# Inputs: mocked explanation and classified candidates; outputs: server math only for development scenarios.
def test_advisor_scenarios_and_source_filtering(monkeypatch):
    from app.domains.developers.ai_advisor import FundingAdviceAnalysis, AdviceItem
    # Purpose: Return one invented ID and duplicate real assessments. Inputs: prompt; outputs: bounded mocked analysis.
    async def mocked(system,content,result_type):
        return FundingAdviceAnalysis(overall_explanation='Review required',source_assessments=[
            AdviceItem(source_id='development',opportunity_or_constraint='Unknown',missing_verification='All'),
            AdviceItem(source_id='development',opportunity_or_constraint='Duplicate',missing_verification='All'),
            AdviceItem(source_id='invented',opportunity_or_constraint='Invented',missing_verification='All')],potential_stack_conflicts=[],next_actions=['Verify'])
    monkeypatch.setattr('app.domains.developers.ai_advisor.claude_json',mocked)
    sources=[{'id':identifier,'name':'Synthetic','funding_track':track,'type':'EMPLOYER','proposed_amount_usd':amount,'availability':status,'program_terms':'Unverified','contribution_kind':'CASH'} for identifier,track,amount,status in [
        ('development','DEVELOPMENT','20.01','UNVERIFIED'),('buyer','BUYER','500.00','UNVERIFIED'),('closed','DEVELOPMENT','900.00','CLOSED')]]
    body={'financials':financials(cost_to_create_usd='100.00',affordable_buyer_proceeds_usd='30.00'),'sources':sources,'consent_to_send_to_claude':True}
    response=client.post('/api/v1/projects/ai-funding-advice',json=body)
    assert response.status_code==200,response.text
    result=response.json()
    assert result['deterministic_gap']['remaining_gap_usd']=='70.00'
    assert [s['source_id'] for s in result['source_assessments']]==['development','buyer','closed']
    assert len(result['scenarios'])==1
    assert result['scenarios'][0]['hypothetical_remaining_gap_usd']=='49.99'
    assert result['scenarios'][0]['hypothetical_surplus_usd']=='0.00'
    body['sources'][0]['id']='invalid source / id'
    assert client.post('/api/v1/projects/ai-funding-advice',json=body).status_code==422

# Purpose: Accept redundant zero precision across every legacy financing input without server errors.
# Inputs: Cent-exact decimal strings; outputs: successful normalized money responses.
@pytest.mark.parametrize('field', ['cost_to_create_usd', 'affordable_buyer_proceeds_usd', 'public_development_subsidies_usd', 'earned_project_revenue_usd', 'nonprofit_donations_usd', 'employer_project_sponsorship_usd'])
@pytest.mark.parametrize('amount', ['1.2300', '0.000', '0e-100000'])
def test_redundant_zero_precision_in_legacy_inputs(field, amount):
    response = client.post('/api/v1/projects/gap', json=financials(**{field: amount}))
    assert response.status_code == 200, response.text
    expected = Decimal(amount)
    body = response.json()
    assert Decimal(body['cost_to_create_usd'] if field == 'cost_to_create_usd' else body['total_funding_usd']) == expected

# Purpose: Accept cent-exact trailing zeros in itemized and classified-source entry points.
# Inputs: Additional cost/source records; outputs: exact two-place totals without HTTP 500.
@pytest.mark.parametrize('amount', ['1.2300', '0.000', '0e-100000'])
@pytest.mark.parametrize('entry', ['itemized', 'source'])
def test_redundant_zero_precision_in_additional_inputs(amount, entry):
    extra = {'itemized_costs': {'land': amount}} if entry == 'itemized' else {'funding_sources': [
        {'id': 'cash', 'category': 'OTHER', 'amount_usd': amount, 'status': 'CONFIRMED'}]}
    response = client.post('/api/v1/projects/gap', json=financials(**extra))
    assert response.status_code == 200, response.text
    key = 'cost_to_create_usd' if entry == 'itemized' else 'total_funding_usd'
    assert Decimal(response.json()[key]) == Decimal(amount)

# Purpose: Ensure normalization never rounds nonzero fractional cents or accepts nonfinite/negative money.
# Inputs: Unsafe monetary strings; outputs: ValueError from the shared money helper.
@pytest.mark.parametrize('amount', ['1.231', '0.001', 'NaN', 'Infinity', '-0.01', '1e100'])
def test_money_helper_rejects_lossy_or_invalid_values(amount):
    from app.core.money import usd
    with pytest.raises(ValueError):
        usd(amount)

# Purpose: Reconcile scenarios against existing commitments while preserving eligible potential-cash scenarios.
# Inputs: Existing funding status and candidate identity; outputs: no duplicate counted cash.
@pytest.mark.parametrize('status,candidate_id,expected_scenarios,expected_gap', [
    ('CONFIRMED', 'existing', 0, None), ('RECEIVED', 'existing', 0, None),
    ('CONFIRMED', 'additional', 1, '20.00'), ('PLEDGED', 'existing', 1, '60.00'),
    ('UNVERIFIED', 'existing', 1, '60.00'),
])
def test_advisor_scenarios_do_not_recount_commitments(monkeypatch, status, candidate_id, expected_scenarios, expected_gap):
    from app.domains.developers.ai_advisor import FundingAdviceAnalysis
    # Purpose: Stub advisory prose. Inputs: provider arguments; outputs: no paid request and valid structured analysis.
    async def mocked(*args, **kwargs):
        return FundingAdviceAnalysis(overall_explanation='Review required', source_assessments=[], potential_stack_conflicts=[], next_actions=[])
    monkeypatch.setattr('app.domains.developers.ai_advisor.claude_json', mocked)
    body = {'financials': financials(cost_to_create_usd='100.00', funding_sources=[
        {'id': 'existing', 'category': 'EMPLOYER', 'amount_usd': '40.00', 'status': status}]),
        'sources': [{'id': candidate_id, 'name': 'Synthetic cash', 'funding_track': 'DEVELOPMENT',
                     'type': 'EMPLOYER', 'proposed_amount_usd': '40.00', 'availability': 'UNVERIFIED',
                     'program_terms': 'Cash proposal subject to verification', 'contribution_kind': 'CASH'}],
        'consent_to_send_to_claude': True}
    response = client.post('/api/v1/projects/ai-funding-advice', json=body)
    assert response.status_code == 200, response.text
    result = response.json()
    assert len(result['scenarios']) == expected_scenarios
    assert result['deterministic_gap']['remaining_gap_usd'] == ('60.00' if status in {'CONFIRMED', 'RECEIVED'} else '100.00')
    if expected_scenarios:
        assert result['scenarios'][0]['hypothetical_remaining_gap_usd'] == expected_gap

# Purpose: Keep noncash, unclassified, buyer and closed candidates out of cash-gap scenarios.
# Inputs: Candidate classification; outputs: unchanged authoritative gap and scenario eligibility.
@pytest.mark.parametrize('kind,track,availability,expected', [
    ('IN_KIND', 'DEVELOPMENT', 'UNVERIFIED', 0), ('UNKNOWN', 'DEVELOPMENT', 'UNVERIFIED', 0),
    (None, 'DEVELOPMENT', 'UNVERIFIED', 0), ('CASH', 'BUYER', 'UNVERIFIED', 0),
    ('CASH', 'DEVELOPMENT', 'CLOSED', 0), ('CASH', 'DEVELOPMENT', 'UNVERIFIED', 1),
])
def test_candidate_cash_classification(monkeypatch, kind, track, availability, expected):
    from app.domains.developers.ai_advisor import FundingAdviceAnalysis
    # Purpose: Mock Claude discussion. Inputs: content and schema; outputs: provider-independent analysis.
    async def mocked(*args, **kwargs):
        return FundingAdviceAnalysis(overall_explanation='Verify source terms', source_assessments=[], potential_stack_conflicts=[], next_actions=[])
    monkeypatch.setattr('app.domains.developers.ai_advisor.claude_json', mocked)
    candidate = {'id': 'candidate', 'name': 'Synthetic support', 'funding_track': track, 'type': 'EMPLOYER',
                 'proposed_amount_usd': '40.000', 'availability': availability, 'program_terms': 'Respect cash/in-kind classification'}
    if kind is not None:
        candidate['contribution_kind'] = kind
    response = client.post('/api/v1/projects/ai-funding-advice', json={
        'financials': financials(cost_to_create_usd='100.00'), 'sources': [candidate], 'consent_to_send_to_claude': True})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result['deterministic_gap']['remaining_gap_usd'] == '100.00'
    assert len(result['scenarios']) == expected
    if expected:
        assert result['scenarios'][0]['hypothetical_cash_usd'] == '40.00'
        assert result['scenarios'][0]['hypothetical_remaining_gap_usd'] == '60.00'
