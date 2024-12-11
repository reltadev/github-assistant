"use server";

import { ReltaApiClient } from "./reltaApi";

export const getRepoInfo = async (owner: string, repo: string) => {
  return new ReltaApiClient({ owner, repo_name: repo }).getRepoInfo();
};
