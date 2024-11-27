import { openai } from "@ai-sdk/openai";
import { getEdgeRuntimeResponse } from "@assistant-ui/react/edge";
import { generateObject } from "ai";
import { z } from "zod";
import { getDataQuery, getTextQuery } from "./reltaApi";

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
If a question is about a single data point (e.g. "who made the most recent commit?"), use the "text" tool.`;

export const POST = async (request: Request) => {
  const { org, repo, ...requestData } = await request.json();

  return getEdgeRuntimeResponse({
    options: {
      model,
      system: getRouterSystemPrompt(`${org}/${repo}`),
      tools: {
        chart: {
          description:
            "Query the GitHub metadata with the provided natural language query, and return the data as a table, which will be automatically displayed to the user in the form of a chart or table.",
          parameters: z.object({
            query: z.string().describe("The query to provide the agent."),
          }),
          execute: async (requestData) => {
            const rows = await getDataQuery(requestData.query);
            const type = await classifyChartType(rows);
            return { type, rows };
          },
        },
        text: {
          description:
            "Query GitHub metadata with the provided natural language query, and return a natural language answer.",
          parameters: z.object({
            query: z.string().describe("The query to provide the agent."),
          }),
          execute: async (requestData) => {
            const text = await getTextQuery(org, repo, requestData.query);
            return text;
          },
        },
      },
    },
    requestData,
    abortSignal: request.signal,
  });
};
