import { MyAssistant } from "@/components/MyAssistant";
import { ChevronLeft } from "lucide-react";
import Link from "next/link";

export default async function Home({
  params,
}: {
  params: Promise<{ owner: string; repo: string }>;
}) {
  const { owner, repo } = await params;
  return (
    <main className="h-dvh flex flex-col">
      <div className="border-b px-4">
        <div className="max-w-2xl mx-auto py-6 flex gap-2 items-center">
          <Link href="/">
            <ChevronLeft />
          </Link>
          <h1 className="text-2xl font-bold">
            {owner}/{repo}
          </h1>
        </div>
      </div>
      <div className="flex-grow">
        <MyAssistant owner={owner} repo={repo} />
      </div>
    </main>
  );
}
