import { dehydrate, HydrationBoundary } from "@tanstack/react-query";
import { makeQueryClient } from "@/lib/makeQueryClient";
import { RepositoryInfoClient } from "./RepositoryInfo.client";
import { getRepoInfo } from "@/lib/actions";

export async function RepositoryInfo({
  owner,
  repo,
}: {
  owner: string;
  repo: string;
}) {
  const queryClient = makeQueryClient();

  await queryClient.prefetchQuery({
    queryKey: ["repo-info", owner, repo],
    queryFn: () => {
      return getRepoInfo(owner, repo);
    },
  });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <RepositoryInfoClient owner={owner} repo={repo} />
    </HydrationBoundary>
  );
}
