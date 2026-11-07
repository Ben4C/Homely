"use client";
import { DirectorySearch } from "@/components/shared/Directory";
import { MatchingGiftDemo } from "@/components/donor/MatchingGiftDemo";
import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { Status } from "@/components/shared/Status";
import type {
  CampaignListResponse,
  PledgePreviewRequest,
  PledgePreviewResponse,
  AllocationPreviewRequest,
  AllocationPreviewResponse,
} from "@homely/contracts/donors";

/**
 * Purpose: Show simulated nonprofit campaigns and nonbinding donation/allocation previews.
 * Inputs: Campaign selection, amount and sample available allocation budget.
 * Outputs: Visible preview receipt and allocation recommendations; no payment execution.
 * TODO(prod): Connect authorized charity/provider flow, restricted gifts and auditable ledger.
 */
export function DonorDashboard() {
  const [campaigns, setCampaigns] = useState<CampaignListResponse | null>(null);
  const [selected, setSelected] = useState("demo-campaign-1");
  const [amount, setAmount] = useState("250.00");
  const [designation, setDesignation] = useState<
    "RESTRICTED_CAMPAIGN" | "UNRESTRICTED"
  >("RESTRICTED_CAMPAIGN");
  const [query, setQuery] = useState("");
  const [preview, setPreview] = useState<PledgePreviewResponse | null>(null);
  const [allocations, setAllocations] =
    useState<AllocationPreviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const visibleCampaigns = (campaigns?.campaigns ?? []).filter((c) =>
    `${c.title} ${c.organization_id} ${c.project_id}`
      .toLowerCase()
      .includes(query.toLowerCase()),
  );

  /**
   * Purpose: Load fictional project campaigns for the donor portal.
   * Inputs: Component mount.
   * Outputs: CampaignListResponse state, or an API error message.
   */
  useEffect(() => {
    apiGet<CampaignListResponse>("/donors/campaigns")
      .then(setCampaigns)
      .catch((e) =>
        setError(e instanceof Error ? e.message : "Campaign loading failed"),
      )
      .finally(() => setLoading(false));
  }, []);

  /**
   * Purpose: Generate a pledge-only receipt without charging any funds.
   * Inputs: Selected campaign and an entered dollar amount.
   * Outputs: PledgePreviewResponse for display or error.
   */
  async function previewPledge() {
    setError(null);
    setPreview(null);
    try {
      setPreview(
        await apiPost<PledgePreviewRequest, PledgePreviewResponse>(
          "/donors/pledge-preview",
          { campaign_id: selected, amount_usd: amount, designation },
        ),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Pledge preview failed");
    }
  }

  /**
   * Purpose: Preview deterministic queue-based distribution for fictional unrestricted money.
   * Inputs: $50,000 synthetic available budget.
   * Outputs: AllocationPreviewResponse listing nonbinding recommendations.
   */
  async function previewAllocation() {
    setError(null);
    setAllocations(null);
    try {
      setAllocations(
        await apiPost<AllocationPreviewRequest, AllocationPreviewResponse>(
          "/donors/allocate-preview",
          {
            total_available_usd: "50000.00",
            designated_campaign_ids: [selected],
          },
        ),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Allocation preview failed");
    }
  }

  return (
    <>
      <DirectorySearch organizations />
      <h2 className="section-title">Synthetic contribution planning</h2>
      <div className="split">
        <section className="panel">
          <h2>Nonprofit campaigns</h2>
          <Status loading={loading} error={error} />
          <p className="small">
            Demo campaigns are synthetic and not verified nonprofit
            solicitations. Choose a campaign directly; a designated gift stays
            with that campaign.
          </p>
          <div className="field">
            <label htmlFor="campaign-search">
              Search by campaign or organization
            </label>
            <input
              id="campaign-search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search campaigns"
            />
          </div>
          {visibleCampaigns.map((c) => (
            <div className="item" key={c.id}>
              <h3>{c.title}</h3>
              <div className="metric">
                $
                {Number(c.remaining_project_gap_usd).toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </div>
              <p className="small">
                Remaining assumed project gap · {c.status} · organization not
                verified
              </p>
            </div>
          ))}
          {visibleCampaigns.length === 0 && !loading && (
            <p className="small">No campaigns match that search.</p>
          )}
          <h2>Preview a gift</h2>
          <div className="field">
            <label htmlFor="donor-campaign">Campaign</label>
            <select
              id="donor-campaign"
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
            >
              {(campaigns?.campaigns ?? []).map((c) => (
                <option key={c.id} value={c.id}>
                  {c.title}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="donor-amount">Amount (USD)</label>
            <input
              id="donor-amount"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              inputMode="decimal"
            />
          </div>
          <div className="field">
            <label htmlFor="donor-designation">Gift designation</label>
            <select
              id="donor-designation"
              value={designation}
              onChange={(e) =>
                setDesignation(e.target.value as typeof designation)
              }
            >
              <option value="RESTRICTED_CAMPAIGN">
                Restricted to selected campaign
              </option>
              <option value="UNRESTRICTED">Unrestricted to nonprofit</option>
            </select>
          </div>
          <button onClick={previewPledge}>Preview pledge — do not pay</button>
          {preview && (
            <p role="status" className="success">
              {preview.message}
            </p>
          )}
        </section>
        <section className="panel">
          <h2>Funding allocation queue</h2>
          <p>
            Illustrative manager controlled suggestion using a fictional $50,000
            pool. The queue is limited to your selected campaign; it cannot
            reassign designated gifts. No financial decisions are made.
          </p>
          <button className="secondary" onClick={previewAllocation}>
            Simulate allocation
          </button>
          {allocations?.lines.map((l) => (
            <div className="item" key={l.campaign_id}>
              <strong>{l.campaign_id}</strong>
              <div className="metric">
                ${Number(l.suggested_usd).toLocaleString()}
              </div>
              <p className="small">{l.reason}</p>
            </div>
          ))}
          {allocations && (
            <p className="small">
              Unallocated: $
              {Number(allocations.unallocated_usd).toLocaleString()}
            </p>
          )}
        </section>
      </div>
      <MatchingGiftDemo />
    </>
  );
}
