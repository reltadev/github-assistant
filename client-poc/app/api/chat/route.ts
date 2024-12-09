import { openai } from "@ai-sdk/openai";
import { getEdgeRuntimeResponse } from "@assistant-ui/react/edge";
import { generateObject } from "ai";
import { z } from "zod";
import { ReltaApiClient } from "../../../lib/reltaApi";

export const maxDuration = 30;

const model = openai("gpt-4o");

const classifyChartType = async (rows: object[]) => {
  const {
    object: { type },
  } = await generateObject({
    model,
    system:
      "You are a helpful assistant that answers questions about a GitHub repository. Identify the correct chart type based on the provided data.",
    prompt: JSON.stringify({ rows }),
    schema: z.object({ type: z.enum(["bar", "line", "pie"]) }),
  });
  return type;
};

const getRouterSystemPrompt = (
  repoName: string
) => `You are a helpful assistant that answers questions about the following GitHub repository:

Selected Repository: ${repoName}

You can use natural language queries to answer questions the user has about the repository.

If a question is best answered by displaying a graph/chart, use the "chart" tool.
If a question is about a single data point (e.g. "who made the most recent commit?"), use the "text" tool.

When printing a chart, ONLY call the provided function call. This will print the chart to the user. Do not use images.`;

export const POST = async (request: Request) => {
  const { owner, repo, ...requestData } = await request.json();

  const relta = new ReltaApiClient({
    owner,
    repo_name: repo,
  });

  return getEdgeRuntimeResponse({
    options: {
      model,
      system: getRouterSystemPrompt(`${owner}/${repo}`),
      tools: {
        chart: {
          description:
            "Query the GitHub metadata with the provided natural language query, and return the data as a table, which will be automatically displayed to the user in the form of a chart or table.",
          parameters: z.object({
            query: z.string().describe("The query to provide the agent."),
          }),
          execute: async (requestData) => {
            const rows = await relta.getDataQuery(requestData.query);
            const type = await classifyChartType(rows);
            return {
              type,
              rows,
              hint: "The chart is being displayed the user.",
            };
          },
        },
        text: {
          description:
            "Query GitHub metadata with the provided natural language query, and return a natural language answer.",
          parameters: z.object({
            query: z.string().describe("The query to provide the agent."),
          }),
          execute: async (requestData) => {
            const text = await relta.getTextQuery(requestData.query);
            return text;
          },
        },
      },
    },
    requestData,
    abortSignal: request.signal,
  });
};
