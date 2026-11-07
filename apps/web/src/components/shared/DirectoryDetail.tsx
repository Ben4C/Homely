"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import { formatUsd } from "@/lib/money";
import type {
  DirectoryProgram,
  DirectoryOrganization,
} from "@homely/contracts/directory";
import { ProgramCard, StatusBadge } from "./Directory";
// Purpose: Present public program evidence and official application/referral navigation. Inputs: ID; outputs: detail with loading/error states.
export function ProgramDetail({ id }: { id: string }) {
  const [data, setData] = useState<DirectoryProgram | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    apiGet<DirectoryProgram>(`/funding-programs/${encodeURIComponent(id)}`)
      .then((r) => {
        if (active) setData(r);
      })
      .catch((e) => {
        if (active) setError(String(e));
      });
    return () => {
      active = false;
    };
  }, [id]);
  return (
    <>
      <Link href="/homebuyer">Back to discovery</Link>
      {error ? (
        <p role="alert" className="error">
          {error}
        </p>
      ) : !data ? (
        <p role="status">Loading program evidence…</p>
      ) : (
        <>
          <h1>{data.name}</h1>
          <ProgramCard program={data} />
          <section className="panel">
            <h2>Program terms</h2>
            <dl className="facts">
              <div>
                <dt>Funding source</dt>
                <dd>{data.originating_source ?? "Not established"}</dd>
              </div>
              <div>
                <dt>Government level</dt>
                <dd>
                  {data.government_level ?? "Not applicable / not stated"}
                </dd>
              </div>
              <div>
                <dt>Assistance classification</dt>
                <dd>
                  {data.loan_grant.replaceAll("_", " ")} /{" "}
                  {data.assistance_type.replaceAll("_", " ")}
                </dd>
              </div>
              <div>
                <dt>Application opens</dt>
                <dd>{data.application_opens_on ?? "Not confirmed"}</dd>
              </div>
              <div>
                <dt>Application closes</dt>
                <dd>{data.application_closes_on ?? "Not confirmed"}</dd>
              </div>
            </dl>
            <h2>Source and rule history</h2>
            <p>{data.source_title}</p>
            <p>
              Retrieved: {data.source_retrieved_at} · Last reviewed:{" "}
              {data.last_verified_at ?? "Not reviewed"} · Publication/effective
              date: {data.source_published_on ?? "Not stated"}
            </p>
            <p>{data.source_evidence}</p>
            <a href={data.source_url} target="_blank" rel="noopener noreferrer">
              Read original source ↗
            </a>
            <h3>
              Eligibility rule version{" "}
              {data.eligibility_rule_version || "not verified"}
            </h3>
            <ul>
              {data.rules.map((r, i) => (
                <li key={i}>
                  {r.explanation}
                  {r.criterion === "MAX_INCOME" &&
                    typeof r.value.by_household_size === "object" &&
                    r.value.by_household_size !== null && (
                      <div className="table-wrap">
                        <table>
                          <caption>
                            Published annual household income limits; confirm
                            the current source chart
                          </caption>
                          <thead>
                            <tr>
                              <th>Household size</th>
                              <th>Maximum qualifying income</th>
                            </tr>
                          </thead>
                          <tbody>
                            {Object.entries(
                              r.value.by_household_size as Record<
                                string,
                                string
                              >,
                            ).map(([size, limit]) => (
                              <tr key={size}>
                                <td>{size}</td>
                                <td>{formatUsd(limit)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                </li>
              ))}
            </ul>
            <details>
              <summary>Published rule version history</summary>
              {data.rule_history?.map((v) => (
                <p key={v.version}>
                  Version {v.version}: reviewed{" "}
                  {v.reviewed_at ?? "Not reviewed"}; effective{" "}
                  {v.effective_on ?? "not stated"};{" "}
                  <a
                    href={v.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Source
                  </a>
                </p>
              ))}
            </details>
            <h3>Restrictions and remaining checks</h3>
            <ul>
              {data.restrictions.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
            <p>
              Service areas:{" "}
              {data.areas
                .map((a) => `${a.name} (${a.purpose?.toLowerCase()})`)
                .join(", ")}
            </p>
            {data.application_url && (
              <a
                className="button-link"
                href={data.application_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                Official application / referral information ↗
              </a>
            )}
            <p className="small">
              Opening this external page does not submit an application. Follow
              its administrator's instructions.
            </p>
          </section>
        </>
      )}
    </>
  );
}
// Purpose: Display organization services without inventing funding or partnership. Inputs: ID; outputs: sourced organization and related programs.
export function OrganizationDetail({ id }: { id: string }) {
  const [data, setData] = useState<DirectoryOrganization | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    apiGet<DirectoryOrganization>(`/organizations/${encodeURIComponent(id)}`)
      .then((r) => {
        if (active) setData(r);
      })
      .catch((e) => {
        if (active) setError(String(e));
      });
    return () => {
      active = false;
    };
  }, [id]);
  return (
    <>
      <Link href="/donor">Back to organizations</Link>
      {error ? (
        <p role="alert">{error}</p>
      ) : !data ? (
        <p role="status">Loading organization…</p>
      ) : (
        <>
          <h1>{data.name}</h1>
          <section className="panel">
            <StatusBadge status={data.verification_status} />
            <dl className="facts">
              <div>
                <dt>Legal name</dt>
                <dd>{data.legal_name}</dd>
              </div>
              <div>
                <dt>Location</dt>
                <dd>{data.headquarters ?? "Not supplied"}</dd>
              </div>
              <div>
                <dt>Service geography</dt>
                <dd>{data.areas.map((a) => a.name).join(", ")}</dd>
              </div>
              <div>
                <dt>Services</dt>
                <dd>
                  {data.services.map((s) => s.replaceAll("_", " ")).join(", ")}
                </dd>
              </div>
            </dl>
            <p>
              Source checked:{" "}
              {data.last_verified_at ?? "Not independently reviewed"}
            </p>
            <p>{data.source_evidence}</p>
            <p>
              Source: {data.source_title}. Retrieved: {data.source_retrieved_at}
              .
            </p>
            <a href={data.source_url} target="_blank" rel="noopener noreferrer">
              Read organization source
            </a>
            <p>
              Charitable status:{" "}
              {data.charitable_status.status ?? "Not independently checked"}. A
              source-checked website does not establish current subsidies or a
              Homely partnership.
            </p>
            {Object.entries(data.charitable_status)
              .filter(([key]) => key !== "status")
              .map(([key, value]) => (
                <p key={key}>
                  {key.replaceAll("_", " ")}: {value}
                </p>
              ))}
            {Object.entries(data.contact).map(([k, v]) => (
              <p key={k}>
                {k}: {v}
              </p>
            ))}
            <a href={data.website} target="_blank" rel="noopener noreferrer">
              Official contact / referral website ↗
            </a>
          </section>
          <h2>Related directory programs</h2>
          {data.programs?.length ? (
            data.programs.map((p) => <ProgramCard program={p} key={p.id} />)
          ) : (
            <p>
              No published programs are linked. This does not imply that funding
              is available.
            </p>
          )}
        </>
      )}
    </>
  );
}
