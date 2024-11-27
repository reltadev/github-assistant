"use client";

import { useEdgeRuntime } from "@assistant-ui/react";
import { Thread } from "@assistant-ui/react";
import { makeMarkdownText } from "@assistant-ui/react-markdown";
import { ChartToolUI } from "./tools/ChartToolUI";
import { TextToolUI } from "./tools/TextToolUI";

const MarkdownText = makeMarkdownText();

type MyAssistantProps = {
  org: string;
  repo: string;
};

export function MyAssistant({ org, repo }: MyAssistantProps) {
  const runtime = useEdgeRuntime({
    api: "/api/chat",
    body: { org, repo },
    adapters: {
      feedback: {
        submit: async ({ type, message }) => {
          console.log({ type, message });
          await fetch(`/feedback`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ type, message }),
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
    />
  );
}
