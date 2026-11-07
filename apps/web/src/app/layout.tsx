import type { Metadata } from "next";
import { Nav } from "@/components/shared/Nav";
import { Notice } from "@/components/shared/Notice";
import "./globals.css";

export const metadata: Metadata = {
  title: "Homely | Affordable Homeownership Funding",
  description: "Southern California affordable homeownership funding — synthetic demo only",
};

/**
 * Purpose: Apply consistent navigation, layout and safety notices across all role dashboards.
 * Inputs: React children representing the active Next.js route.
 * Outputs: Document HTML shell.
 */
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body><Nav /><main className="main"><Notice />{children}</main><footer>Homely prototype · Southern California · Fictional data only</footer></body></html>;
}
