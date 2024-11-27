import { MyAssistant } from "@/components/MyAssistant";
import { ChevronLeft } from "lucide-react";
import Link from "next/link";

export default async function Home({
  params,
}: {
  params: Promise<{ org: string; repo: string }>;
}) {
  const { org, repo } = await params;
  return (
    <main className="h-dvh flex flex-col">
      <div className="border-b px-4">
        <div className="max-w-2xl mx-auto py-6 flex gap-2 items-center">
          <Link href="/">
            <ChevronLeft />
          </Link>
          <h1 className="text-2xl font-bold">
            {org}/{repo}
          </h1>
        </div>
      </div>
      <div className="flex-grow">
        <MyAssistant org={org} repo={repo} />
      </div>
    </main>
  );
}
