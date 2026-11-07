/* Developer 5 review regressions. Requires Playwright and isolated web/API servers.
   PLAYWRIGHT_MODULE: absolute Playwright module path, DEV5_WEB_URL: localhost:3105,
   DEV5_API_URL: 127.0.0.1:18081/api/v1. AI transport is always intercepted. */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const assert = require("node:assert/strict");
const web = process.env.DEV5_WEB_URL || "http://localhost:3105";
const api = process.env.DEV5_API_URL || "http://127.0.0.1:18081/api/v1";
// Purpose: Coordinate delayed requests deterministically. Inputs: none; outputs: promise and resolver.
function deferred() {
  let resolve;
  const promise = new Promise((r) => {
    resolve = r;
  });
  return { promise, resolve };
}
// Purpose: Open the owned workspace against real local finance endpoints, with AI calls blocked.
// Inputs: browser; outputs: ready page plus captured actual pro forma requests. CORS is adapted only in this test harness.
async function openDeveloper(browser) {
  const page = await browser.newPage({
    viewport: { width: 1280, height: 900 },
  });
  const requests = [];
  await page.route("**/api/v1/**", async (route) => {
    const endpoint = route.request().url().split("/api/v1")[1];
    if (endpoint === "/projects/ai-funding-advice")
      return route.fulfill({
        status: 503,
        json: { detail: "AI intercepted by regression test" },
      });
    if (endpoint === "/projects/gap")
      requests.push(route.request().postDataJSON());
    const response = await page.request.fetch(api + endpoint, {
      method: route.request().method(),
      data: route.request().postData() ?? undefined,
      headers: { "Content-Type": "application/json" },
    });
    await route.fulfill({
      response,
      headers: { ...response.headers(), "access-control-allow-origin": "*" },
    });
  });
  await page.goto(web + "/developer");
  await page
    .getByRole("heading", { name: "DEMO Santa Ana Single Home", exact: true })
    .waitFor();
  await page
    .getByLabel("Supported contribution classification")
    .first()
    .selectOption("CASH");
  return { page, requests };
}
// Purpose: Build explicitly mocked advice around real deterministic finance output.
// Inputs: intercepted advice request, page and explanation; outputs: structured response without a paid call.
async function advice(route, page, explanation) {
  const body = route.request().postDataJSON();
  assert.equal(body.sources[0].contribution_kind, "CASH");
  const calculation = await page.request.post(api + "/projects/gap", {
    data: body.financials,
  });
  assert.equal(calculation.status(), 200);
  return route.fulfill({
    json: {
      demo: true,
      ai_generated: true,
      human_review_required: true,
      deterministic_gap: await calculation.json(),
      overall_explanation: explanation,
      source_assessments: [],
      potential_stack_conflicts: [],
      next_actions: [],
      scenarios: [],
      disclaimer: "Synthetic regression mock",
    },
  });
}
// Purpose: Verify independent models, preserved itemization, hidden-input compatibility, stale errors and exact rendering.
// Inputs: local servers; outputs: assertions for all frontend defects from the review.
async function main() {
  const browser = await chromium.launch({ headless: true });
  try {
    const { page } = await openDeveloper(browser);
    await page
      .getByLabel("Total development cost", { exact: true })
      .fill("999999");
    await page.getByRole("button", { name: "Add source", exact: true }).click();
    await page.getByLabel("Amount (USD)", { exact: true }).fill("123.45");
    await page
      .getByRole("button", { name: "Model this project", exact: true })
      .nth(1)
      .click();
    assert.equal(
      await page
        .getByLabel("Total development cost", { exact: true })
        .inputValue(),
      "535000.00",
    );
    assert.equal(
      await page.getByLabel("Amount (USD)", { exact: true }).count(),
      0,
    );
    await page
      .getByRole("button", { name: "Model this project", exact: true })
      .nth(0)
      .click();
    assert.equal(
      await page
        .getByLabel("Total development cost", { exact: true })
        .inputValue(),
      "999999",
    );
    assert.equal(
      await page.getByLabel("Amount (USD)", { exact: true }).inputValue(),
      "123.45",
    );
    await page
      .getByLabel("Use itemized costs instead of the total cost")
      .check();
    await page.getByLabel("Land acquisition", { exact: true }).fill("12345.67");
    await page
      .getByLabel("Use itemized costs instead of the total cost")
      .uncheck();
    await page
      .getByLabel("Use itemized costs instead of the total cost")
      .check();
    assert.equal(
      await page.getByLabel("Land acquisition", { exact: true }).inputValue(),
      "12345.67",
    );
    await page
      .getByRole("button", { name: "Model this project", exact: true })
      .nth(1)
      .click();
    assert.equal(
      await page
        .getByLabel("Use itemized costs instead of the total cost")
        .isChecked(),
      false,
    );
    await page
      .getByRole("button", { name: "Model this project", exact: true })
      .nth(0)
      .click();
    assert.equal(
      await page.getByLabel("Land acquisition", { exact: true }).inputValue(),
      "12345.67",
    );
    await page.close();
    console.log(
      "PASS project isolation, source isolation, and preserved itemized drafts across mode/project switches",
    );

    const hidden = await openDeveloper(browser);
    const hp = hidden.page;
    await hp.getByLabel("Total development cost", { exact: true }).fill("");
    await hp.getByLabel("Use itemized costs instead of the total cost").check();
    await hp.getByLabel("Construction", { exact: true }).fill("535000.00");
    await hp
      .getByRole("button", { name: "Calculate development gap", exact: true })
      .click();
    await hp.getByText("$95,000.00", { exact: true }).waitFor();
    assert.equal(hidden.requests.at(-1).cost_to_create_usd, "0.00");
    await hp.route("**/projects/ai-funding-advice", (r) =>
      advice(r, hp, "ITEMIZED_ADVICE"),
    );
    await hp
      .getByLabel(
        "I consent to sending these project assumptions and public program terms to Claude.",
      )
      .check();
    await hp
      .getByRole("button", { name: "Analyze funding stack", exact: true })
      .click();
    await hp.getByText("ITEMIZED_ADVICE", { exact: true }).waitFor();
    assert.equal(await hp.locator(".ai-panel [role=alert]").count(), 0);
    await hp.close();
    console.log(
      "PASS hidden aggregate compatibility for both calculation and advice",
    );

    const exact = await openDeveloper(browser);
    const ep = exact.page;
    await ep
      .getByLabel("Total development cost", { exact: true })
      .fill("99999999999999.99");
    await ep.route("**/projects/ai-funding-advice", (r) =>
      advice(r, ep, "EXACT_ADVICE"),
    );
    await ep
      .getByLabel(
        "I consent to sending these project assumptions and public program terms to Claude.",
      )
      .check();
    await ep
      .getByRole("button", { name: "Analyze funding stack", exact: true })
      .click();
    await ep.getByText("EXACT_ADVICE", { exact: true }).waitFor();
    assert.equal(
      (await ep.locator(".ai-panel .metric").innerText()).trim(),
      "$99,999,999,559,999.99",
    );
    await ep.close();
    console.log("PASS exact large-amount currency rendering");

    const stale = await openDeveloper(browser);
    const sp = stale.page;
    const started = deferred(),
      release = deferred(),
      currentStarted = deferred(),
      currentRelease = deferred();
    let calls = 0;
    await sp.route("**/projects/ai-funding-advice", async (r) => {
      calls++;
      if (calls === 1) {
        started.resolve();
        await release.promise;
        return r.fulfill({ status: 502, json: { detail: "OBSOLETE_ERROR" } });
      }
      currentStarted.resolve();
      await currentRelease.promise;
      return advice(r, sp, "CURRENT_ADVICE");
    });
    await sp
      .getByLabel(
        "I consent to sending these project assumptions and public program terms to Claude.",
      )
      .check();
    await sp
      .getByRole("button", { name: "Analyze funding stack", exact: true })
      .click();
    await started.promise;
    await sp
      .getByLabel("Total development cost", { exact: true })
      .fill("600000.00");
    await sp
      .getByRole("button", { name: "Analyze funding stack", exact: true })
      .click();
    await currentStarted.promise;
    const finished = sp.waitForResponse(
      (r) =>
        r.url().endsWith("/projects/ai-funding-advice") && r.status() === 502,
    );
    release.resolve();
    await finished;
    await sp.getByLabel("Total development cost", { exact: true }).focus();
    await sp.keyboard.press("Tab");
    assert.equal(
      await sp.locator(".ai-panel button[type=submit]").isDisabled(),
      true,
    );
    currentRelease.resolve();
    await sp.getByText("CURRENT_ADVICE", { exact: true }).waitFor();
    assert.equal(await sp.locator(".ai-panel [role=alert]").count(), 0);
    assert.equal(
      await sp.getByText("CURRENT_ADVICE", { exact: true }).count(),
      1,
    );
    assert.equal(
      await sp
        .getByRole("button", { name: "Analyze funding stack", exact: true })
        .isEnabled(),
      true,
    );
    await sp.close();
    console.log(
      "PASS obsolete failed response cannot replace current advice or error/busy state",
    );
  } finally {
    await browser.close();
  }
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
