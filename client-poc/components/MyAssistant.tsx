"use client";

import { Composer, useEdgeRuntime } from "@assistant-ui/react";
import { Thread } from "@assistant-ui/react";
import { makeMarkdownText } from "@assistant-ui/react-markdown";
import { ChartToolUI } from "./tools/ChartToolUI";
import { TextToolUI } from "./tools/TextToolUI";
import { create } from "zustand";
import { GitPullRequest, LoaderCircleIcon, LoaderIcon } from "lucide-react";

const MarkdownText = makeMarkdownText();

type MyAssistantProps = {
  owner: string;
  repo: string;
};

const useFeedbackState = create<{ isLoading?: boolean; prUrl?: string }>(
  () => ({})
);

const MyComposer = () => {
  const { isLoading, prUrl } = useFeedbackState((state) => state);
  return (
    <>
      {!!isLoading && (
        <div className="flex  gap-2 border rounded-lg w-full mb-3 px-4 py-3">
          <LoaderCircleIcon className="animate-spin" />{" "}
          <div>
            <p className="font-semibold">
              Creating a PR based on your feedback
            </p>
            <p>Loading...</p>
          </div>
        </div>
      )}
      {!!prUrl && (
        <div className="flex  gap-2 border rounded-lg w-full mb-3 px-4 py-3">
          <GitPullRequest />{" "}
          <div>
            <p className="font-semibold">
              PR #{prUrl.split("/").at(-1)} created based on your feedback
            </p>
            <a className="underline" href={prUrl}>
              {prUrl}
            </a>
          </div>
        </div>
      )}

      <Composer />
      <p className="self-end pt-1.5">
        powered by{" "}
        <a className="underline" href="https://github.com/github/Assistant-UI">
          assistant-ui
        </a>{" "}
        and{" "}
        <a className="underline" href="https://relta.dev">
          Relta
        </a>
      </p>
    </>
  );
};

export function MyAssistant({ owner, repo }: MyAssistantProps) {
  const runtime = useEdgeRuntime({
    api: "/api/chat",
    body: { owner, repo },
    adapters: {
      feedback: {
        submit: async ({ type, message }) => {
          const chatId =
            message.content
              .map((c) =>
                c.type === "tool-call"
                  ? (c.result as { id?: string } | undefined)?.id
                  : undefined
              )
              .filter(Boolean)[0] ?? "-";

          if (type === "negative") {
            useFeedbackState.setState({ isLoading: true });
          }
          const { pr_url } = await fetch(`/api/feedback`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ owner, repo, chatId, type, message }),
          })
            .then((response) => response.json())
            .catch((error) =>
              console.error("Error submitting feedback:", error)
            )
            .finally(() => useFeedbackState.setState({ isLoading: false }));

          useFeedbackState.setState({ prUrl: pr_url }, true);
        },
      },
    },
    maxSteps: 4,
    unstable_AISDKInterop: true,
  });

  return (
    <Thread
      runtime={runtime}
      assistantMessage={{ components: { Text: MarkdownText } }}
      tools={[ChartToolUI, TextToolUI]}
      welcome={{
        suggestions: [
          { prompt: "How many new stars per day over the last month?" },
          {
            prompt: "Who are the top contributors to this repository?",
          },
        ],
      }}
      components={{ Composer: MyComposer }}
    />
  );
}
