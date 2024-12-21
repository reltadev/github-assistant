import { ReltaApiClient } from "../../../lib/reltaApi";

export const POST = async (request: Request) => {
  const { owner, repo, chatId, type, message } = await request.json();

  const relta = new ReltaApiClient({
    owner,
    repo_name: repo,
  });
  console.log(chatId, type, message);
  const result = await relta.submitFeedback(chatId, type, message);
  return Response.json(result, { status: 200 });
};
