/* All-role integration checks against the real PostgreSQL-backed API. No paid Claude requests. */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const url = process.env.HOMELY_WEB_URL || "http://localhost:3105";
// Purpose: Verify unified shell, persisted discovery, safe previews, responsiveness and themes. Inputs: local services; outputs: assertions/screenshots.
async function main() {
  const browser = await chromium.launch({ headless: true });
  const output = path.join(__dirname, "../.venv/integration/screenshots");
  fs.mkdirSync(output, { recursive: true });
  try {
    const page = await browser.newPage({
      viewport: { width: 1440, height: 1000 },
    });
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    for (const route of [
      "/",
      "/homebuyer",
      "/donor",
      "/employer",
      "/manager",
      "/developer",
      "/admin",
    ]) {
      await page.goto(url + route);
      await page.getByRole("heading", { level: 1 }).first().waitFor();
      assert.equal(await page.locator("header.site-header").count(), 1);
      assert.equal(await page.locator("header").count(), 1);
      assert.equal(await page.locator("main").count(), 1);
      assert.equal(
        await page.locator('nav[aria-label="Main navigation"]').count(),
        1,
      );
      await page.screenshot({
        path: path.join(output, (route.slice(1) || "home") + "-desktop.png"),
        fullPage: true,
      });
      await page.setViewportSize({ width: 390, height: 844 });
      await page.getByLabel("Theme", { exact: true }).selectOption("dark");
      assert.equal(
        await page.evaluate(
          () => getComputedStyle(document.body).backgroundColor,
        ),
        "rgb(42, 31, 24)",
      );
      assert(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
        route + " overflows mobile",
      );
      await page.screenshot({
        path: path.join(
          output,
          (route.slice(1) || "home") + "-mobile-dark.png",
        ),
        fullPage: true,
      });
      await page.getByLabel("Theme", { exact: true }).selectOption("light");
      await page.setViewportSize({ width: 1440, height: 1000 });
      console.log("PASS shell/mobile/dark", route);
    }
    await page.goto(url + "/homebuyer");
    await page
      .getByRole("button", { name: "Program directory", exact: true })
      .click();
    await page.getByText("8 directory results", { exact: true }).waitFor();
    await page
      .getByLabel("Purchase city", { exact: true })
      .selectOption("Garden Grove");
    await page
      .getByLabel("Annual household income (USD)", { exact: true })
      .fill("65000.00");
    await page.getByLabel("Household size", { exact: true }).fill("3");
    await page
      .getByLabel("First-time buyer status", { exact: true })
      .selectOption("true");
    await page
      .getByRole("button", { name: "Search directory", exact: true })
      .click();
    await page
      .getByRole("link", {
        name: "Garden Grove First-Time Home Buyer Loan",
        exact: true,
      })
      .waitFor();
    assert.equal(
      await page
        .getByRole("link", { name: "My Anaheim Home", exact: true })
        .count(),
      0,
    );
    await page
      .getByLabel("Search name", { exact: true })
      .fill("not-a-real-program");
    await page
      .getByRole("button", { name: "Search directory", exact: true })
      .click();
    await page.getByText("0 directory results", { exact: true }).waitFor();
    await page.getByLabel("Search name", { exact: true }).fill("Garden Grove");
    await page
      .getByRole("button", { name: "Search directory", exact: true })
      .click();
    await page
      .getByRole("link", { name: "View program details", exact: true })
      .click();
    await page
      .getByRole("heading", { name: "Source and rule history", exact: true })
      .waitFor();
    assert(
      await page
        .getByText("Eligibility rule version 1", { exact: true })
        .isVisible(),
    );
    assert(
      (
        await page
          .getByRole("link", { name: "Read original source ↗", exact: true })
          .getAttribute("href")
      ).startsWith("https://ggcity.org/"),
    );
    await page.screenshot({
      path: path.join(output, "program-detail.png"),
      fullPage: true,
    });
    console.log(
      "PASS persisted location/income search, empty results and sourced detail",
    );
    await page.goto(url + "/homebuyer");
    await page
      .getByRole("button", { name: "Household & matching", exact: true })
      .click();
    await page
      .getByLabel("Current residence county", { exact: true })
      .selectOption("Los Angeles");
    await page
      .getByLabel("Intended purchase city (optional)", { exact: true })
      .fill("Garden Grove");
    await page
      .getByRole("button", { name: "Preview potential matches", exact: true })
      .click();
    await page
      .getByRole("heading", {
        name: "Garden Grove First-Time Home Buyer Loan",
        exact: true,
      })
      .waitFor();
    console.log("PASS residence/purchase-separated preliminary matching");
    await page.goto(url + "/donor");
    await page
      .getByRole("link", {
        name: "Habitat for Humanity of Orange County",
        exact: true,
      })
      .waitFor();
    await page
      .getByRole("link", { name: "Organization details", exact: true })
      .click();
    await page
      .getByRole("heading", {
        level: 1,
        name: "Habitat for Humanity of Orange County",
        exact: true,
      })
      .waitFor();
    assert(
      await page
        .getByText(/No Homely partnership|does not establish current subsidies/)
        .first()
        .isVisible(),
    );
    console.log(
      "PASS real nonprofit detail without funding/partnership claims",
    );
    await page.goto(url + "/developer");
    await page
      .getByRole("button", { name: "Calculate development gap", exact: true })
      .click();
    await page.getByText("$95,000.00", { exact: true }).waitFor();
    await page
      .getByText("CalHome — Agency and Nonprofit Funding", { exact: true })
      .waitFor();
    assert.equal(
      await page.getByText(/Fictional county development subsidy/).count(),
      0,
    );
    console.log(
      "PASS preserved finance and database-backed advisor candidates",
    );
    await page.goto(url + "/manager");
    await page
      .getByRole("button", {
        name: "Preview intake — not a submission",
        exact: true,
      })
      .first()
      .waitFor();
    await page
      .getByRole("button", {
        name: "Preview intake — not a submission",
        exact: true,
      })
      .first()
      .click();
    await page
      .getByText(
        "Demo only: application was NOT submitted to any organization.",
        { exact: true },
      )
      .waitFor();
    console.log("PASS real-program intake remains an explicit preview");
    assert.deepEqual(errors, []);
    console.log("PASS all-role browser verification; screenshots:", output);
  } finally {
    await browser.close();
  }
}
main().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
