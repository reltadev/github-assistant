import { ChevronLeft, Loader } from "lucide-react";
import Link from "next/link";

export const LoadingPage = async ({
  owner,
  repo,
}: {
  owner: string;
  repo: string;
}) => {
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
      <div className="flex-grow items-center flex justify-center gap-2">
        <Loader className="size-4 animate-spin" /> Importing repository...
      </div>
    </main>
  );
};
