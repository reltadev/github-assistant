import { generateId } from "ai";

interface ReltaApiConfig {
  owner: string;
  repo_name: string;
  baseUrl?: string;
}

export type RepoInfo = {
  owner: string;
  last_pipeline_run: string | null;
  id: number;
  loaded_issues: boolean;
  loaded_stars: boolean;
  repo_name: string;
  pipeline_status: "SUCCESS" | "RUNNING" | "FAILED";
  loaded_pull_requests: boolean;
  loaded_commits: boolean;
};

export class ReltaApiClient {
  private readonly baseUrl: string;
  private readonly owner: string;
  private readonly repo_name: string;

  constructor({
    owner,
    repo_name,
    baseUrl = "https://gh-assistant.relta.dev/",
  }: ReltaApiConfig) {
    this.baseUrl = baseUrl;
    this.owner = owner;
    this.repo_name = repo_name;
  }

  private async fetchJson(
    endpoint: string,
    options: {
      method?: string;
      query?: object;
      body?: object;
      sendRepo?: boolean;
    } = {}
  ) {
    const repoData = {
      owner: this.owner,
      repo_name: this.repo_name,
    };

    const queryParams = new URLSearchParams({
      ...(options.sendRepo ?? true ? repoData : undefined),
      ...options.query,
    }).toString();

    const url = `${this.baseUrl}${endpoint}${
      queryParams ? `?${queryParams}` : ""
    }`;

    const response = await fetch(url, {
      method: options.method,
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      ...(options.body ? { body: JSON.stringify(options.body) } : {}),
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getDataQuery(
    prompt: string
  ): Promise<{ rows: object[]; id: string; sql: string }> {
    const { sql, sql_result, chat } = (await this.fetchJson("data", {
      method: "POST",
      body: { prompt },
    })) as { sql_result: object[]; sql: string; chat: { id: string } };

    return { rows: sql_result ?? [], sql, id: chat.id };
  }

  async getTextQuery(
    prompt: string
  ): Promise<{ text: string; sql_result: object[]; sql: string; id: string }> {
    const result = (await this.fetchJson("prompt", {
      method: "POST",
      body: { prompt },
    })) as {
      text?: string;
      detail?: string;
      chat: { id: string };
      sql_result: object[];
      sql: string;
    };

    return {
      text: result.text ?? result.detail ?? JSON.stringify(result),
      sql: result.sql,
      sql_result: result.sql_result,
      id: result.chat.id,
    };
  }

  async submitFeedback(
    chatId: string,
    type: string,
    message: object
  ): Promise<{ pr_url?: string }> {
    const result = (await this.fetchJson("feedback", {
      method: "POST",
      query: { chat_id: chatId },
      body: { type, message },
    })) as { pr_url?: string };
    return result;
  }

  async getRepoInfo(): Promise<RepoInfo> {
    return await this.fetchJson("repo-info", {
      query: {
        request_id: generateId(),
      },
    });
  }

  static async getRepos(): Promise<RepoInfo[]> {
    return await new ReltaApiClient({ owner: "", repo_name: "" }).fetchJson(
      "repos",
      { sendRepo: false }
    );
  }

  async loadGithubData(access_token: string): Promise<RepoInfo> {
    return await this.fetchJson("load-github-data", {
      method: "POST",
      query: {
        access_token,
      },
    });
  }
}
