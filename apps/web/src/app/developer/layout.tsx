// Purpose: Preserve the developer route boundary without duplicating the global shell. Inputs: route content; outputs: unchanged children.
export default function DeveloperLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
