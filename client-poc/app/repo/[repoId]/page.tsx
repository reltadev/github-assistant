import { MyAssistant } from "@/components/MyAssistant";

export default function Home({ params }: { params: { repoId: string } }) {
  return (
    <main className="h-dvh">
      <MyAssistant repoId={params.repoId} />
    </main>
  );
}
