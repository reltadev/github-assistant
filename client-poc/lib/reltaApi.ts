interface ReltaApiConfig {
  owner: string;
  repo_name: string;
  baseUrl?: string;
}

type RepoInfo = {
  owner: string;
  last_pipeline_run: string | null;
  id: number;
  loaded_issues: boolean;
  loaded_stars: boolean;
  repo_name: string;
  pipeline_status: "SUCCESS";
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
      body?: object;
      repoLocation?: "query" | "body" | "none";
    } = {}
  ) {
    const repoData = {
      owner: this.owner,
      repo_name: this.repo_name,
    };

    const queryParams =
      (options.repoLocation ?? "query") === "query"
        ? new URLSearchParams(repoData).toString()
        : "";

    const body =
      options.repoLocation === "body"
        ? { ...repoData, ...options.body }
        : options.body;

    const url = `${this.baseUrl}${endpoint}${
      queryParams ? `?${queryParams}` : ""
    }`;

    const response = await fetch(url, {
      method: options.method,
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      ...(body ? { body: JSON.stringify(body) } : {}),
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getDataQuery(prompt: string): Promise<object[]> {
    const { sql_result } = (await this.fetchJson("data", {
      method: "POST",
      body: { prompt },
    })) as { sql_result: object[] };

    return sql_result ?? [];
  }

  async getTextQuery(prompt: string): Promise<string> {
    const result = (await this.fetchJson("prompt", {
      method: "POST",
      body: { prompt },
    })) as { text?: string; detail?: string };

    return result.text ?? result.detail ?? JSON.stringify(result);
  }

  async submitFeedback(type: string, message: object): Promise<void> {
    await this.fetchJson("feedback", {
      method: "POST",
      body: { type, message },
    });
  }

  async getRepoInfo(): Promise<RepoInfo> {
    return await this.fetchJson("repo-info");
  }

  static async getRepos(): Promise<RepoInfo[]> {
    return await new ReltaApiClient({ owner: "", repo_name: "" }).fetchJson(
      "repos",
      { repoLocation: "none" }
    );
  }

  async loadGithubData(access_token: string): Promise<void> {
    await this.fetchJson("load-github-data", {
      method: "POST",
      repoLocation: "body",
      body: {
        access_token,
        load_issues: true,
        load_pull_requests: true,
        load_stars: true,
        load_commits: true,
      },
    });
  }
}
