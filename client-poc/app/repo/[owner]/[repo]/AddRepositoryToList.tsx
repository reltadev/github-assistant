"use client";

import { useRepoStore } from "@/lib/storage";
import { FC, useEffect } from "react";

export const AddRepositoryToList: FC<{
  owner: string;
  repo: string;
}> = ({ owner, repo }) => {
  const addRepository = useRepoStore((s) => s.addRepository);
  useEffect(() => {
    addRepository({ owner, repo });
  }, [addRepository, owner, repo]);
  return null;
};
