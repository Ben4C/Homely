// Purpose: Preserve the admin route boundary without duplicating the global shell. Inputs: route content; outputs: unchanged children.
export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
