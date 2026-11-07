import Link from "next/link";
const destinations = [
  ["Home", "/"], ["Homebuyer", "/homebuyer"], ["Donor", "/donor"],
  ["Employer", "/employer"], ["Funding Manager", "/manager"],
  ["Developer", "/developer"], ["Admin", "/admin"],
] as const;

/**
 * Purpose: Offer simple top-level role navigation for the prototype.
 * Inputs: None (static destinations).
 * Outputs: Accessible React navigation markup.
 * TODO(prod): Filter destinations by authenticated organization permissions.
 */
export function Nav() {
  return (
    <header className="site-header">
      <div className="header-inner">
        <Link href="/" className="logo">HOMELY<span className="logo-dot">.</span></Link>
        <nav className="nav" aria-label="Main navigation">
          {destinations.map(([title, path]) => <Link href={path} key={path}>{title}</Link>)}
        </nav>
      </div>
    </header>
  );
}
