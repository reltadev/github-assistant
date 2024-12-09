import { MyAssistant } from "@/components/MyAssistant";
import { ReltaApiClient } from "@/lib/reltaApi";
import { ChevronLeft } from "lucide-react";
import Link from "next/link";
import { redirect } from "next/navigation";
import { LoadingPage } from "./fallback";
import { FC, Suspense } from "react";
import { AddRepositoryToList } from "./AddRepositoryToList";

export const maxDuration = 60;

const EnsureRepoIsLoaded: FC<{
  owner: string;
  repo: string;
}> = async ({ owner, repo }) => {
  const client = new ReltaApiClient({
    owner,
    repo_name: repo,
  });
  try {
    const startTime = Date.now();
    while (true) {
      const info = await client.getRepoInfo();
      if (
        info.last_pipeline_run !== null ||
        info.pipeline_status === "SUCCESS"
      ) {
        return null;
      }

      const age = (Date.now() - startTime) / 1000;
      if (age < maxDuration - 5) {
        await new Promise((resolve) => setTimeout(resolve, 1000));
      } else {
        break;
      }
    }
  } catch (e) {
    console.log(e);
    // notFound();
  }

  redirect(`/repo/${owner}/${repo}`);
};

export default async function Home({
  params,
}: {
  params: Promise<{ owner: string; repo: string }>;
}) {
  const { owner, repo } = await params;

  return (
    <>
      <AddRepositoryToList owner={owner} repo={repo} />
      <Suspense fallback={<LoadingPage owner={owner} repo={repo} />}>
        <EnsureRepoIsLoaded owner={owner} repo={repo} />
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
      </Suspense>
    </>
  );
}
