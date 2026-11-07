import Link from "next/link";
const roles = [
  {
    icon: "⌂",
    name: "Homebuyer",
    path: "/homebuyer",
    detail:
      "Find potential assistance and understand eligibility requirements.",
  },
  {
    icon: "♡",
    name: "Donor",
    path: "/donor",
    detail: "Explore nonprofits and preview donation allocation.",
  },
  {
    icon: "▣",
    name: "Employer",
    path: "/employer",
    detail: "Design workforce assistance and verify applicant workflow.",
  },
  {
    icon: "◎",
    name: "Funding Manager",
    path: "/manager",
    detail: "Manage program source checks and review applications.",
  },
  {
    icon: "▥",
    name: "Housing Developer",
    path: "/developer",
    detail: "Model affordable project development funding gaps.",
  },
  {
    icon: "⚙",
    name: "Platform Admin",
    path: "/admin",
    detail: "Review nonprofit and program verification tasks.",
  },
];

/**
 * Purpose: Explain the platform and route demo users to one of the six archetypes.
 * Inputs: None (static product navigation).
 * Outputs: Server-rendered landing page with six role cards.
 */
export default function HomePage() {
  return (
    <>
      <section className="hero">
        <div className="eyebrow">SOCAL AFFORDABLE HOMEOWNERSHIP</div>
        <h1>
          Bring the funding together.
          <br />
          <span>Make the home possible.</span>
        </h1>
        <p>
          One platform for prospective homeowners, nonprofits, donors,
          employers, and housing developers. Discover source-backed housing
          resources and explore clearly labelled financing previews.
        </p>
      </section>
      <section>
        <div className="section-title">
          <h2>Choose a workspace</h2>
          <span>6 archetypes · 5 development owners</span>
        </div>
        <div className="card-grid">
          {roles.map((role) => (
            <Link href={role.path} className="role-card" key={role.path}>
              <div className="role-icon">{role.icon}</div>
              <h3>{role.name}</h3>
              <p>{role.detail}</p>
              <span className="role-link">Open workspace →</span>
            </Link>
          ))}
        </div>
      </section>
      <section className="footer-info">
        <h2>Two financial tracks. One shared system.</h2>
        <p>
          <strong>Project financing</strong> closes the gap between creating an
          affordable home and affordable sale proceeds.{" "}
          <strong>Homebuyer assistance</strong> helps eligible households
          finance their purchase. Homely keeps the two separate.
        </p>
      </section>
    </>
  );
}
