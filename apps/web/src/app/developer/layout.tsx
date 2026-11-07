import type { ReactNode } from "react";
import styles from "@/components/developer/Dashboard.module.css";
// Purpose: Apply the template's scoped palette and typography. Inputs: route content; outputs: owned dashboard shell.
export default function DeveloperLayout({ children }: { children: ReactNode }) {
  return (
    <div className={styles.dashboard}>
      <link
        rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@500;700&family=Source+Sans+3:wght@400;600&display=swap"
      />
      {children}
    </div>
  );
}
