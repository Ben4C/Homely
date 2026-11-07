import { ProgramDetail } from "@/components/shared/DirectoryDetail";
// Purpose: Mount public source-backed detail. Inputs: stable route ID; outputs: sourced detail interface.
export default async function DetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <ProgramDetail id={id} />;
}
