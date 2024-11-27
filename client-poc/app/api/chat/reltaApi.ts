const MOCK_BASE_URL = "http://localhost:3002/api/mock";
const BASE_URL =
  "http://github-assistant-alb-1250589316.us-east-1.elb.amazonaws.com";

export const getDataQuery = async (query: string) => {
  const response = await fetch(`${MOCK_BASE_URL}/dataQuery`, {
    method: "POST",
    body: JSON.stringify({ query }),
  });
  const { rows } = (await response.json()) as { rows: object[] };
  return rows;
};
export const getTextQuery = async (
  org: string,
  repo: string,
  prompt: string
) => {
  const response = await fetch(
    `${BASE_URL}/prompt?org=${org}&repo_name=${repo}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ prompt }),
    }
  );
  const { text } = (await response.json()) as { text: string };
  return text;
};

export const submitFeedback = async (type: string, message: string) => {
  console.log(type, message);
};
