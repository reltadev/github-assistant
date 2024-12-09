"use client";

import { NewRepositoryDialog } from "@/components/NewRepositoryDialog";
import { Button } from "@/components/ui/button";
import { Card, CardHeader } from "@/components/ui/card";
import { defaultRepos, useRepoStore } from "@/lib/storage";
import { SignedIn } from "@clerk/nextjs";
import { SignOutButton } from "@clerk/nextjs";
import { PlusIcon, TrashIcon } from "lucide-react";
import Link from "next/link";
import { Suspense } from "react";

interface RepoCardProps {
  name: string;
  id: string;
  href?: string;
  onDelete?: () => void;
}

function RepoCard({ name, id, href, onDelete }: RepoCardProps) {
  const content = (
    <Card className="aspect-[5/3] hover:bg-muted/20 transition-all hover:shadow-md shadow-none relative">
      <CardHeader className="h-full pb-4">
        <h2 className="text-xl font-semibold mb-1 truncate">{name}</h2>
        <p className="text-sm text-gray-500 truncate">{id}</p>
        <div className="flex-grow" />
        {onDelete && (
          <Button
            variant="ghost"
            size="icon"
            className="self-end -mr-2"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onDelete();
            }}
          >
            <TrashIcon />
          </Button>
        )}
      </CardHeader>
    </Card>
  );

  return href ? <Link href={href}>{content}</Link> : content;
}

export default function RepoSelection() {
  const { repositories: userRepos, deleteRepository } = useRepoStore();

  const renderRepoCards = (
    repos: { owner: string; repo: string }[],
    onDelete?: (owner: string, repo: string) => void
  ) => {
    return repos.map((repo) => {
      const id = `${repo.owner}/${repo.repo}`;
      return (
        <RepoCard
          key={id}
          name={repo.repo}
          id={id}
          href={`/repo/${id}`}
          onDelete={
            onDelete ? () => onDelete(repo.owner, repo.repo) : undefined
          }
        />
      );
    });
  };

  return (
    <div className="min-h-dvh flex flex-col">
      <div className="border-b px-4 container mx-auto py-6 flex gap-2 items-center">
        <h1 className="text-2xl font-bold">github assistant</h1>
        <div className="flex-1" />
        <SignedIn>
          <SignOutButton />
        </SignedIn>
      </div>
      <div className="container mx-auto px-4 py-8 flex flex-col justify-center">
        <div>
          <h1 className="text-3xl font-bold text-center mb-8">
            Which repository do you want to explore?
          </h1>

          {/* Original 10 repos */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 mb-8">
            {renderRepoCards(defaultRepos)}
          </div>

          <hr className="my-8 border-gray-200" />

          {/* User added repos */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 mb-8">
            {renderRepoCards(userRepos, deleteRepository)}

            {/* Dotted add repo button */}
            <Suspense>
              <NewRepositoryDialog
                trigger={
                  <Card className="aspect-[5/3] hover:bg-muted/20 transition-all shadow-none border-dashed border-2">
                    <CardHeader className="flex flex-row items-center gap-2">
                      <PlusIcon className="size-4" />
                      <h2 className="leading-0 !mt-0 truncate">
                        Import Repository
                      </h2>
                    </CardHeader>
                  </Card>
                }
              />
            </Suspense>
          </div>
        </div>
      </div>
    </div>
  );
}
