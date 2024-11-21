const BASE_URL = "http://localhost:3002/api/mock";

export const getDataQuery = async (query: string) => {
  const response = await fetch(`${BASE_URL}/dataQuery`, {
    method: "POST",
    body: JSON.stringify({ query }),
  });
  const { rows } = (await response.json()) as { rows: object[] };
  return rows;
};
export const getTextQuery = async (query: string) => {
  const response = await fetch(`${BASE_URL}/textQuery`, {
    method: "POST",
    body: JSON.stringify({ query }),
  });
  const { text } = (await response.json()) as { text: string };
  return text;
};

export const submitFeedback = async (type: string, message: string) => {
  // TODO
};
