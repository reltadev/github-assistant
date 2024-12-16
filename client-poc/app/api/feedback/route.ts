import { ReltaApiClient } from "../../../lib/reltaApi";

export const POST = async (request: Request) => {
  const { owner, repo, chatId, type, message } = await request.json();

  const relta = new ReltaApiClient({
    owner,
    repo_name: repo,
  });

  await relta.submitFeedback(chatId, type, message);
  return new Response("Feedback submitted", { status: 200 });
};
