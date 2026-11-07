"use client";

import { useMemo, useState } from "react";
import { apiPost } from "@/lib/api";
import { AIDocumentReview } from "@/components/homebuyer/AIDocumentReview";
import type { HomebuyerProfile, MatchRequest, MatchResponse } from "@homely/contracts/homebuyers";
import styles from "./Homebuyer.module.css";

type View = "home" | "profile" | "documents";

/** Purpose: Render the template-inspired homebuyer home, onboarding, match results, and next steps.
 * Inputs: User-entered sample household fields; no profile is persisted.
 * Outputs: Conservative match response and locally maintained progress state.
 */
export function HomebuyerDashboard() {
  const [view, setView] = useState<View>("home");
  const [county, setCounty] = useState("Orange");
  const [householdSize, setHouseholdSize] = useState("3");
  const [income, setIncome] = useState("52000");
  const [firstTime, setFirstTime] = useState("yes");
  const [employer, setEmployer] = useState("");
  const [result, setResult] = useState<MatchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const completedSteps = useMemo(() => [
    Boolean(county), Number.isInteger(Number(householdSize)) && Number(householdSize) >= 1 && Number(householdSize) <= 30,
    income !== "" && Number.isFinite(Number(income)) && Number(income) >= 0, Boolean(firstTime),
  ].filter(Boolean).length, [county, householdSize, income, firstTime]);

  /** Purpose: Submit a minimum-necessary sample profile for preliminary matching.
   * Inputs: Validated local onboarding fields.
   * Outputs: API matches clearly marked for manual review; nothing is saved or submitted to a program.
   */
  async function runMatch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const annualIncome = Number(income);
    const people = Number(householdSize);
    if (!Number.isFinite(annualIncome) || annualIncome < 0 || !Number.isInteger(people) || people < 1 || people > 30) {
      setError("Enter a valid annual income and a household size from 1 to 30.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    const profile: HomebuyerProfile = {
      profile_id: "demo-browser-profile", county, household_size: people,
      annual_income_usd: annualIncome.toFixed(2), first_time_buyer: firstTime === "unknown" ? null : firstTime === "yes",
      employer_name: employer.trim() || null, preferred_language: "en",
    };
    try {
      setResult(await apiPost<MatchRequest, MatchResponse>("/homebuyers/match", { profile }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load program matches.");
    } finally {
      setLoading(false);
    }
  }

  return <div className={styles.root}>
    <header className={styles.header}>
      <button className={styles.logo} aria-label="Homely home" onClick={() => setView("home")}>
        <svg viewBox="0 0 40 40" aria-hidden="true"><rect x="7" y="18" width="26" height="18" rx="5" fill="#B59577"/><path d="M4 21.5L20 8l16 13.5" fill="none" stroke="#FFF6F0" strokeWidth="4.2" strokeLinecap="round" strokeLinejoin="round"/><rect x="17" y="26" width="6" height="10" rx="3" fill="#765640"/><rect x="10.5" y="22.5" width="4.8" height="4.8" rx="1.6" fill="#FFE3A8"/><rect x="24.7" y="22.5" width="4.8" height="4.8" rx="1.6" fill="#FFE3A8"/></svg>
        <span>homely</span>
      </button>
      <nav className={styles.tabs} aria-label="Homebuyer navigation" role="tablist">
        {([["home", "Home"], ["profile", "Get started"], ["documents", "Documents"]] as const).map(([key, label]) =>
          <button key={key} type="button" role="tab" aria-selected={view === key} onClick={() => setView(key)}>{label}</button>)}
      </nav>
    </header>

    <main className={styles.main}>
      {view === "home" && <>
        <section className={styles.hero}>
          <div className={styles.heroGrid}>
            <div><span className={styles.eyebrow}>HOMEbuyer workspace · demo</span><h1>Housing help, matched to your next step.</h1>
              <p>Explore homebuyer assistance by county and household. See what is known, what still needs review, and which documents to prepare.</p>
              <div className={styles.actions}><button className={styles.button} onClick={() => setView("profile")}>Start your profile</button><button className={styles.ghost} onClick={() => setView("documents")}>Check document readiness</button></div>
            </div>
            <Neighborhood />
          </div>
        </section>
        <h2 className={styles.sectionTitle}>Your path to homeownership</h2>
        <div className={styles.cards}>
          <article className={styles.card}><span className={styles.icon}>⌂</span><h3>Share the basics</h3><p>County, household size, income, and first-time buyer status help us start a preliminary search.</p></article>
          <article className={styles.card}><span className={styles.icon}>↗</span><h3>Review possible matches</h3><p>Understand which areas line up and which requirements still need an official source or human review.</p></article>
          <article className={styles.card}><span className={styles.icon}>✓</span><h3>Prepare your documents</h3><p>Use the optional AI readiness review with sample or carefully redacted material and your explicit consent.</p></article>
        </div>
        <section className={`${styles.card} ${styles.next}`}><h2>Helpful next steps</h2><ol><li>Enter household details to see the demo program registry.</li><li>Check each program’s official source and current availability with its administrator.</li><li>Gather only the documents requested by a verified program.</li></ol><button className={styles.buttonSmall} onClick={() => setView("profile")}>Continue onboarding</button></section>
      </>}

      {view === "profile" && <>
        <h1 className={styles.pageTitle}>Find homebuyer assistance</h1><p className={styles.lede}>Tell us a few basics. Results are potential matches only; no program eligibility or funding is confirmed.</p>
        <div className={styles.grid}>
          <form className={`${styles.card} ${styles.form}`} onSubmit={runMatch}>
            <h2>Your household</h2><p>Use fictional information only. This demo does not save your profile.</p>
            <div className={styles.field}><label htmlFor="hb-county">County</label><select id="hb-county" value={county} onChange={e => setCounty(e.target.value)}>{["Orange", "Los Angeles", "San Diego", "Riverside", "San Bernardino"].map(c => <option key={c}>{c}</option>)}</select></div>
            <div className={styles.field}><label htmlFor="hb-size">Household size</label><input id="hb-size" type="number" min="1" max="30" step="1" required value={householdSize} onChange={e => setHouseholdSize(e.target.value)} /></div>
            <div className={styles.field}><label htmlFor="hb-income">Household income per year (USD)</label><input id="hb-income" type="number" min="0" step="100" required value={income} onChange={e => setIncome(e.target.value)} /></div>
            <div className={styles.field}><label htmlFor="hb-first">First-time homebuyer?</label><select id="hb-first" value={firstTime} onChange={e => setFirstTime(e.target.value)}><option value="yes">Yes</option><option value="no">No</option><option value="unknown">Not sure</option></select></div>
            <div className={styles.field}><label htmlFor="hb-employer">Employer (optional)</label><input id="hb-employer" maxLength={120} value={employer} onChange={e => setEmployer(e.target.value)} placeholder="Only if relevant to assistance" /></div>
            <div className={styles.progress}><strong>Profile progress · {completedSteps} of 4 details</strong><div className={styles.bar} role="progressbar" aria-label="Homebuyer profile progress" aria-valuemin={0} aria-valuemax={4} aria-valuenow={completedSteps}><span style={{ width: `${completedSteps * 25}%` }} /></div><small>Program application not started · no information is saved</small></div>
            <button className={styles.button} type="submit" disabled={loading}>{loading ? "Finding programs…" : "Preview potential matches"}</button>
            {error && <p className={styles.error} role="alert">{error}</p>}
          </form>
          <section className={`${styles.card} ${styles.matches}`} aria-live="polite">
            <h2>Potential program matches</h2>
            {loading && <p className={styles.empty}>Checking the demo registry…</p>}
            {!loading && !result && !error && <p className={styles.empty}>Complete your profile to see programs with explanations.</p>}
            {!loading && result && <>
              <p className={styles.disclaimer}>{result.disclaimer}</p>
              {result.matches.length === 0 && <p className={styles.empty}>No demo programs are listed for this profile yet.</p>}
              {result.matches.map(match => <article className={styles.program} key={match.program_id}>
                <div className={styles.programHead}><div><h3>{match.program_name}</h3><p>{match.availability.replaceAll("_", " ")}{match.last_verified_at ? ` · checked ${match.last_verified_at}` : " · no verification date"}</p></div>
                  <span className={`${styles.tag} ${match.outcome === "NEEDS_MANUAL_REVIEW" ? styles.warn : ""}`}>{match.outcome === "NEEDS_MANUAL_REVIEW" ? "Potential match · review required" : "Outside listed area"}</span></div>
                <ul>{match.explanations.map((why, i) => <li key={`${match.program_id}-${i}`}>{why}</li>)}</ul>
                {match.source_url ? <a className={styles.link} href={match.source_url} target="_blank" rel="noreferrer">Program source ↗</a> : <span className={styles.muted}>Official source not supplied</span>}
              </article>)}
              <div className={styles.notice}>No confirmed eligibility or open funding is shown. Contact the program administrator to verify current rules and availability.</div>
            </>}
          </section>
        </div>
      </>}

      {view === "documents" && <>
        <h1 className={styles.pageTitle}>Get your documents ready</h1><p className={styles.lede}>Organize evidence requested by a verified program. The review below is optional and advisory.</p>
        <div className={styles.checklist}><h2>Common preparation checklist</h2><p>Requirements vary by program. Confirm the list with its administrator before sharing anything.</p><div className={styles.checkItems}><span>□ Proof of household income</span><span>□ Proof of county or residence</span><span>□ First-time buyer statement, if requested</span></div></div>
        <AIDocumentReview />
      </>}
      <p className={styles.footerNote}>Synthetic demonstration only. Homely does not verify eligibility, accept applications, or move funds.</p>
    </main>
  </div>;
}

/** Purpose: Recreate the source template's small neighborhood illustration with inline SVG.
 * Inputs: None.
 * Outputs: Accessible decorative neighborhood artwork, colored by the template palette.
 */
function Neighborhood() {
  return <svg className={styles.art} viewBox="0 0 400 280" role="img" aria-label="Illustration of a small neighborhood of cozy houses"><rect width="400" height="280" fill="#E3DAD1"/><circle cx="326" cy="62" r="26" fill="#B59577"/><path d="M0 215Q110 168 230 204T400 188V280H0Z" fill="#868F6D"/><g fill="#B59577" stroke="#765640" strokeWidth="4" strokeLinejoin="round"><path d="M26 170l47-45 51 45v52H26z"/><path d="M285 175l41-42 50 42v48h-91z"/><path d="M138 132l63-57 70 57v94H138z"/></g><path d="M130 137l71-63 77 63" fill="none" stroke="#765640" strokeWidth="7" strokeLinecap="round"/><path d="M187 226h26v54h-40z" fill="#E3DAD1"/><g fill="#FFE3A8"><rect x="52" y="174" width="17" height="17" rx="3"/><rect x="87" y="174" width="17" height="17" rx="3"/><rect x="157" y="145" width="20" height="20" rx="3"/><rect x="236" y="145" width="20" height="20" rx="3"/></g></svg>;
}
