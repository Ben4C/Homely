/* Local PostgreSQL-backed reviewer workflow. Supply HOMELY_REVIEWER_FILE with an
   ignored JSON file containing an authorized token; no credential is committed. */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const web = process.env.HOMELY_WEB_URL || "http://localhost:3105";
const api = process.env.HOMELY_API_URL || "http://127.0.0.1:18081/api/v1";

// Purpose: Verify authorized source review and persistent audit through the actual UI.
// Inputs: local services and an explicitly supplied local reviewer token; outputs: assertions.
// Keeps real program availability UNKNOWN and preserves all existing eligibility rules.
async function main() {
  assert(
    process.env.HOMELY_REVIEWER_FILE,
    "Set HOMELY_REVIEWER_FILE to an ignored local credential file",
  );
  const { token } = JSON.parse(
    fs.readFileSync(process.env.HOMELY_REVIEWER_FILE, "utf8"),
  );
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    const before = await (
      await page.request.get(api + "/funding-programs/garden-grove-first-home")
    ).json();
    assert.equal(before.availability, "UNKNOWN");
    await page.goto(web + "/admin");
    await page.getByLabel("Reviewer access token").fill(token);
    await page
      .getByRole("button", { name: "Load authorized records", exact: true })
      .click();
    await page
      .getByRole("heading", { name: "Recent audit history", exact: true })
      .waitFor();
    await page
      .getByRole("button", {
        name: "Review Garden Grove First-Time Home Buyer Loan",
        exact: true,
      })
      .click();
    await page.getByLabel("New status").selectOption("UNKNOWN");
    await page
      .getByLabel("Evidence from the current source")
      .fill(
        "The official city page describes first-time homebuyer loans and household-size income limits. Current application intake availability remains unconfirmed.",
      );
    const reason =
      "Local browser verification of source review; retaining UNKNOWN availability and existing rules.";
    await page
      .getByLabel("Review reason", { exact: true })
      .first()
      .fill(reason);
    await page
      .getByLabel(
        "I opened the current original source and verified the facts and application status. This attestation records the current UTC review time.",
      )
      .check();
    await page
      .getByRole("button", {
        name: "Save source review and audit event",
        exact: true,
      })
      .click();
    await page
      .getByText(
        "Directory review and audit event saved. No funding or applicant decision was made.",
        { exact: true },
      )
      .waitFor();
    const after = await (
      await page.request.get(api + "/funding-programs/garden-grove-first-home")
    ).json();
    assert.equal(after.revision, before.revision + 1);
    assert.equal(
      after.eligibility_rule_version,
      before.eligibility_rule_version,
    );
    assert.equal(after.availability, "UNKNOWN");
    await page.reload();
    assert.equal(
      await page.getByLabel("Reviewer access token").inputValue(),
      "",
    );
    await page.getByLabel("Reviewer access token").fill(token);
    await page
      .getByRole("button", { name: "Load authorized records", exact: true })
      .click();
    await page.getByRole("cell").filter({ hasText: reason }).first().waitFor();
    console.log(
      "PASS authorized browser review, revision increment, preserved rules/status, persistent audit and memory-only credential",
    );
  } finally {
    await browser.close();
  }
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
