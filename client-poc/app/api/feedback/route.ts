import { submitFeedback } from "../../../lib/reltaApi";

export const POST = async (request: Request) => {
  const { type, message } = await request.json();
  await submitFeedback(type, message);
  return new Response("Feedback submitted", { status: 200 });
};
