import { ReltaApiClient } from "../../../lib/reltaApi";

export const POST = async (request: Request) => {
  const { owner, repo, type, message } = await request.json();

  const relta = new ReltaApiClient({
    owner,
    repo_name: repo,
  });

  await relta.submitFeedback(type, message);
  return new Response("Feedback submitted", { status: 200 });
};
