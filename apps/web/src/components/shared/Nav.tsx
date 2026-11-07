"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
const destinations = [
  ["Home", "/"],
  ["Homebuyer", "/homebuyer"],
  ["Donor", "/donor"],
  ["Employer", "/employer"],
  ["Funding Manager", "/manager"],
  ["Developer", "/developer"],
  ["Admin", "/admin"],
] as const;
// Purpose: Render one template-based brand/navigation and theme control. Inputs: active route and theme preference; outputs: accessible application header.
export function Nav() {
  const path = usePathname();
  const [theme, setTheme] = useState("system");
  // Purpose: Restore appearance preference only. Inputs: local theme setting; outputs: root theme, without retaining user/profile data.
  useEffect(() => {
    try {
      const saved = localStorage.getItem("homely-theme");
      if (saved && ["light", "dark", "system"].includes(saved)) {
        setTheme(saved);
        document.documentElement.dataset.theme = saved;
      }
    } catch {}
  }, []);
  // Purpose: Change the shared palette. Inputs: selected theme; outputs: persisted non-sensitive appearance preference.
  function changeTheme(value: string) {
    setTheme(value);
    document.documentElement.dataset.theme = value;
    try {
      localStorage.setItem("homely-theme", value);
    } catch {}
  }
  return (
    <header className="site-header">
      <div className="header-inner">
        <Link href="/" className="logo" aria-label="Homely home">
          <svg viewBox="0 0 40 40" aria-hidden="true">
            <path
              d="M29.5 5.5c-2.2-1.3-2.2-2.7 0-3.9"
              fill="none"
              stroke="#FFF6F0"
              strokeWidth="1.6"
              strokeLinecap="round"
              opacity=".7"
            />
            <rect
              x="26.5"
              y="8"
              width="5.5"
              height="10"
              rx="1.6"
              fill="#B59577"
            />
            <rect x="7" y="18" width="26" height="18" rx="5" fill="#B59577" />
            <path
              d="M4 21.5L20 8l16 13.5"
              fill="none"
              stroke="#FFF6F0"
              strokeWidth="4.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <rect x="17" y="26" width="6" height="10" rx="3" fill="#765640" />
            <rect
              x="10.5"
              y="22.5"
              width="4.8"
              height="4.8"
              rx="1.6"
              fill="#FFE3A8"
            />
            <rect
              x="24.7"
              y="22.5"
              width="4.8"
              height="4.8"
              rx="1.6"
              fill="#FFE3A8"
            />
          </svg>
          <span>homely</span>
        </Link>
        <nav className="nav" aria-label="Main navigation">
          {destinations.map(([title, url]) => (
            <Link
              href={url}
              key={url}
              aria-current={
                (url === "/" ? path === url : path.startsWith(url))
                  ? "page"
                  : undefined
              }
            >
              {title}
            </Link>
          ))}
        </nav>
        <div className="theme-select">
          <label htmlFor="theme">Theme</label>
          <select
            id="theme"
            value={theme}
            onChange={(e) => changeTheme(e.target.value)}
          >
            <option value="system">System</option>
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </div>
      </div>
    </header>
  );
}
