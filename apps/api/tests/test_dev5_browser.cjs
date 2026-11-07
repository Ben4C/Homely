/* Run with PLAYWRIGHT_MODULE pointing to a locally installed Playwright package.
   Requires the API and Next.js development server; never calls a paid AI provider.
   Screenshots are written to the ignored .venv/dev5-previews directory. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
// Purpose: Exercise owned dashboards against the real API. Inputs: local servers; outputs: assertions and preview images.
async function main(){
  const browser=await chromium.launch({headless:true});
  const output=path.join(__dirname,'../.venv/dev5-previews');fs.mkdirSync(output,{recursive:true});
  try{
    const page=await browser.newPage({viewport:{width:1440,height:1000}});
    const errors=[];page.on('pageerror',error=>errors.push(error.message));
    await page.goto('http://localhost:3000/developer');
    await page.getByRole('heading',{name:'DEMO Santa Ana Single Home',exact:true}).waitFor();
    await page.getByRole('button',{name:'Calculate development gap',exact:true}).click();
    await page.getByText('$95,000.00',{exact:true}).waitFor();
    assert.equal(await page.getByRole('progressbar',{name:'Project financing identified',exact:true}).getAttribute('value'),'82.24');
    await page.getByLabel('Use itemized costs instead of the total cost').check();
    await page.getByLabel('Land acquisition',{exact:true}).fill('100.01');
    await page.getByRole('button',{name:'Calculate development gap',exact:true}).click();
    await page.getByText('$95,100.01',{exact:true}).waitFor();
    await page.getByRole('button',{name:'Add source',exact:true}).click();
    await page.getByLabel('Amount (USD)',{exact:true}).fill('10.01');
    await page.getByRole('button',{name:'Calculate development gap',exact:true}).click();
    await page.getByText('Potential, excluded from confirmed total: $10.01',{exact:true}).waitFor();
    await page.getByLabel('Status',{exact:true}).selectOption('CONFIRMED');
    await page.getByRole('button',{name:'Calculate development gap',exact:true}).click();
    await page.getByText('$95,090.00',{exact:true}).waitFor();
    assert(await page.getByRole('button',{name:'Analyze funding stack',exact:true}).isDisabled());
    await page.getByLabel('I consent to sending these synthetic assumptions to Claude.').check();
    // Purpose: Emulate the sanitized missing-key HTTP boundary, avoiding any provider call if local credentials exist.
    await page.route('**/projects/ai-funding-advice',route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Claude AI is not configured.'})}));
    await page.getByRole('button',{name:'Analyze funding stack',exact:true}).click();
    await page.getByRole('alert').filter({hasText:'Claude AI is not configured'}).waitFor();
    // Purpose: Verify structured advisory rendering with an explicit UI mock; real SDK behavior is tested in pytest.
    await page.route('**/projects/ai-funding-advice',async route=>{
      const body=route.request().postDataJSON();
      const calculation=await page.request.post('http://127.0.0.1:18080/api/v1/projects/gap',{data:body.financials});
      await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({
        demo:true,ai_generated:true,human_review_required:true,deterministic_gap:await calculation.json(),
        overall_explanation:'<img src=x onerror=alert(1)> Example advisory text.',
        source_assessments:[{source_id:body.sources[0].id,opportunity_or_constraint:'Restrictions remain unknown.',missing_verification:'Confirm official program terms.'}],
        potential_stack_conflicts:['Compatibility unknown.'],next_actions:['Ask the program administrator.'],
        scenarios:[{source_id:body.sources[0].id,hypothetical_cash_usd:'40000.00',hypothetical_remaining_gap_usd:'55090.00',hypothetical_surplus_usd:'0.00',assumption:'Hypothetical only; requires verified additional cash.'}],
        disclaimer:'UI test mock only; no funding approval.'})});
    });
    await page.getByRole('button',{name:'Analyze funding stack',exact:true}).click();
    await page.getByText('<img src=x onerror=alert(1)> Example advisory text.',{exact:true}).waitFor();
    assert.equal(await page.locator('img[src=x]').count(),0);
    await page.getByRole('heading',{name:'Hypothetical financing scenarios',exact:true}).waitFor();
    await page.screenshot({path:path.join(output,'developer-desktop.png'),fullPage:true});
    await page.setViewportSize({width:390,height:844});
    await page.emulateMedia({colorScheme:'dark'});
    const palette=await page.getByRole('heading',{name:'Development pro forma',exact:true}).evaluate(el=>getComputedStyle(el).color);
    assert.equal(palette,'rgb(255, 246, 240)');
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await page.screenshot({path:path.join(output,'developer-mobile-dark.png'),fullPage:true});
    await page.getByLabel('Land acquisition',{exact:true}).fill('200.01');
    assert.equal(await page.getByText('<img src=x onerror=alert(1)> Example advisory text.',{exact:true}).count(),0);
    await page.goto('http://localhost:3000/admin');
    await page.getByText('Official funding source not verified',{exact:true}).waitFor();
    await page.getByLabel('Review category').selectOption('ORGANIZATION');
    await page.getByText('Organization authorization evidence missing',{exact:true}).waitFor();
    assert.equal(await page.getByText('Official funding source not verified',{exact:true}).count(),0);
    assert(await page.getByRole('button',{name:'Record verification decision (requires authorized persistence)',exact:true}).isDisabled());
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await page.screenshot({path:path.join(output,'admin-mobile-dark.png'),fullPage:true});
    await page.setViewportSize({width:1440,height:1000});await page.emulateMedia({colorScheme:'light'});
    await page.getByLabel('Review category').selectOption('ALL');
    await page.screenshot({path:path.join(output,'admin-desktop.png'),fullPage:true});
    await page.getByLabel('Review category').focus();await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(()=>document.activeElement.tagName),'SUMMARY');
    assert.deepEqual(errors,[]);
    console.log('PASS: real API finance, source classification, consent/error, admin filters, disabled privileges, mobile overflow, dark palette, keyboard focus; four screenshots saved.');
  }finally{await browser.close();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
