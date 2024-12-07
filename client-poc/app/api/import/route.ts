import { ReltaApiClient } from "@/lib/reltaApi";
import { auth, clerkClient } from "@clerk/nextjs/server";

export const runtime = "edge";

export const maxDuration = 60;

export async function POST(request: Request) {
  const { owner, repo } = await request.json();

  const { userId } = await auth();
  if (!userId) throw new Error("User not signed in");

  const client = await clerkClient();
  const tokens = await client.users.getUserOauthAccessToken(
    userId,
    "oauth_github"
  );
  const accessToken = tokens.data[0].token;

  const info = await new ReltaApiClient({
    owner,
    repo_name: repo,
  }).loadGithubData(accessToken);

  return Response.json(info, { status: 200 });
}
