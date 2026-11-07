import type { Metadata } from "next";
import { Nav } from "@/components/shared/Nav";
import { Notice } from "@/components/shared/Notice";
import "./globals.css";
export const metadata: Metadata = {
  title: "Homely | Affordable Homeownership",
  description:
    "Source-backed Southern California housing directory and clearly labelled financial previews",
};
// Purpose: Apply one shared template shell. Inputs: route content; outputs: single header/main/footer and common typography.
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <head>
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@500;700&family=Source+Sans+3:wght@400;600&display=swap"
        />
      </head>
      <body>
        <a className="skip-link" href="#main-content">
          Skip to content
        </a>
        <Nav />
        <main id="main-content" className="main">
          <Notice />
          {children}
        </main>
        <footer>
          Homely · Southern California · Directory information requires
          administrator confirmation; financial activity is simulated.
        </footer>
      </body>
    </html>
  );
}
