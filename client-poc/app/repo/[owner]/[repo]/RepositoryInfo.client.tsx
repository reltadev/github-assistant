"use client";

import { getRepoInfo } from "@/lib/actions";
import { useSuspenseQuery } from "@tanstack/react-query";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { ChevronDown, RefreshCw } from "lucide-react";
import { RepoInfo } from "@/lib/reltaApi";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { useRouter } from "next/navigation";

function getRelativeTimeString(isoString: string | null): string {
  if (!isoString) return "never";

  const date = new Date(isoString);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) return "just now";
  if (diffInSeconds < 3600)
    return `${Math.floor(diffInSeconds / 60)} minutes ago`;
  if (diffInSeconds < 86400)
    return `${Math.floor(diffInSeconds / 3600)} hours ago`;
  return `${Math.floor(diffInSeconds / 86400)} days ago`;
}

function StatusDot({
  status,
}: {
  status: "success" | "running" | "warning" | "error";
}) {
  const colors = {
    success: "bg-green-500",
    running: "bg-blue-500",
    warning: "bg-yellow-500",
    error: "bg-red-500",
  };

  return (
    <span
      className={`inline-block w-2 h-2 rounded-full ${colors[status]} mr-2`}
    />
  );
}

function getPipelineStatus(repoInfo: RepoInfo) {
  if (repoInfo.pipeline_status === "RUNNING") return "running";
  if (repoInfo.pipeline_status !== "SUCCESS") return "error";

  const allLoaded =
    repoInfo.loaded_issues &&
    repoInfo.loaded_stars &&
    repoInfo.loaded_pull_requests &&
    repoInfo.loaded_commits;

  return allLoaded ? "success" : "warning";
}

export const RepositoryInfoClient = ({
  owner,
  repo,
}: {
  owner: string;
  repo: string;
}) => {
  const { data: repoInfo } = useSuspenseQuery({
    queryKey: ["repo-info", owner, repo],
    staleTime: 5 * 1000,
    queryFn: async () => getRepoInfo(owner, repo),
  });

  const [isReimporting, setIsReimporting] = useState(false);
  const router = useRouter();

  const handleReimport = async () => {
    setIsReimporting(true);
    await fetch("/api/import", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ owner, repo }),
    });
    router.replace(`/repo/${owner}/${repo}`);
    setIsReimporting(false);
  };

  const pipelineStatus = getPipelineStatus(repoInfo);

  const lastImportText =
    repoInfo.pipeline_status === "SUCCESS"
      ? "Last import: " + getRelativeTimeString(repoInfo?.last_pipeline_run)
      : repoInfo.pipeline_status === "RUNNING"
      ? "Import currently in progress"
      : "Import failed";

  return (
    <div className="flex items-center gap-2">
      <StatusDot status={pipelineStatus} />
      <span>{lastImportText}</span>

      <Popover>
        <PopoverTrigger className="ml-1">
          <ChevronDown className="h-4 w-4" />
        </PopoverTrigger>
        <PopoverContent className="w-[300px]">
          <div className="flex flex-col gap-2">
            <div className="flex justify-between items-center mb-2">
              <div className="font-semibold">Import Status</div>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleReimport}
                disabled={isReimporting}
                className="h-8"
              >
                <RefreshCw className="size-4" />
              </Button>
            </div>

            <div className="flex justify-between items-center">
              <div className="flex items-center">
                <StatusDot
                  status={repoInfo.loaded_pull_requests ? "success" : "error"}
                />
                <span>Pull Requests</span>
              </div>
              <span className="text-sm">
                {repoInfo.loaded_pull_requests ? "Available" : "Not Available"}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <div className="flex items-center">
                <StatusDot
                  status={repoInfo.loaded_commits ? "success" : "error"}
                />
                <span>Commits</span>
              </div>
              <span className="text-sm">
                {repoInfo.loaded_commits ? "Available" : "Not Available"}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <div className="flex items-center">
                <StatusDot
                  status={repoInfo.loaded_issues ? "success" : "error"}
                />
                <span>Issues</span>
              </div>
              <span className="text-sm">
                {repoInfo.loaded_issues ? "Available" : "Not Available"}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <div className="flex items-center">
                <StatusDot
                  status={repoInfo.loaded_stars ? "success" : "error"}
                />
                <span>Stars</span>
              </div>
              <span className="text-sm">
                {repoInfo.loaded_stars ? "Available" : "Not Available"}
              </span>
            </div>

            <div className="text-sm text-muted-foreground mt-2">
              {lastImportText}
            </div>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
};
