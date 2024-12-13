"use client";

import { useEdgeRuntime } from "@assistant-ui/react";
import { Thread } from "@assistant-ui/react";
import { makeMarkdownText } from "@assistant-ui/react-markdown";
import { ChartToolUI } from "./tools/ChartToolUI";
import { TextToolUI } from "./tools/TextToolUI";

const MarkdownText = makeMarkdownText();

type MyAssistantProps = {
  owner: string;
  repo: string;
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
          console.log({ chatId, type, message });
          await fetch(`/feedback`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ owner, repo, chatId, type, message }),
          })
            .then((response) => response.json())
            .then((data) => console.log("Feedback submitted:", data))
            .catch((error) =>
              console.error("Error submitting feedback:", error)
            );
        },
      },
    },
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
    />
  );
}
