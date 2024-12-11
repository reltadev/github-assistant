import { create } from "zustand";
import { persist } from "zustand/middleware";

export const defaultRepos = [
  { owner: "Yonom", repo: "assistant-ui" },
  { owner: "langchain-ai", repo: "langchain" },
  { owner: "openai", repo: "whisper" },
  // { owner: "joaomdmoura", repo: "crewai" },
  // { owner: "jerryjliu", repo: "llama_index" },
  // { owner: "huggingface", repo: "transformers" },
  // { owner: "openai", repo: "gpt-3" },
  // { owner: "openai", repo: "DALL-E" },
  // { owner: "CompVis", repo: "stable-diffusion" },
  // { owner: "anthropics", repo: "anthropic-ai" },
];

type Repository = {
  owner: string;
  repo: string;
};

type RepoState = {
  repositories: Repository[];
  addRepository: (repo: Repository) => void;
  deleteRepository: (owner: string, repo: string) => void;
};

export const useRepoStore = create<RepoState>()(
  persist(
    (set, get) => ({
      repositories: [],
      addRepository: (newRepo) => {
        const { repositories } = get();

        // Check if newRepo matches one of the default repositories
        const isDefault = defaultRepos.some(
          (def) => def.owner === newRepo.owner && def.repo === newRepo.repo
        );
        if (isDefault) {
          // Ignore addition if it's a default repo
          return;
        }

        // prevent duplicates among user repos
        const alreadyExists = repositories.some(
          (r) => r.owner === newRepo.owner && r.repo === newRepo.repo
        );
        if (alreadyExists) {
          return;
        }

        set({ repositories: [...repositories, newRepo] });
      },
      deleteRepository: (owner, repo) => {
        const { repositories } = get();
        set({
          repositories: repositories.filter(
            (r) => !(r.owner === owner && r.repo === repo)
          ),
        });
      },
    }),
    {
      name: "myKey", // The key under which the state is stored in localStorage
    }
  )
);
