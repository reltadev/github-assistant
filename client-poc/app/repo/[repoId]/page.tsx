import { MyAssistant } from "@/components/MyAssistant";

export default async function Home({
  params,
}: {
  params: Promise<{ repoId: string }>;
}) {
  const { repoId } = await params;
  return (
    <main className="h-dvh">
      <MyAssistant repoId={repoId} />
    </main>
  );
}
