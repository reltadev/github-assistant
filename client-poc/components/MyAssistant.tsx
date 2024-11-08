"use client";

import { useEdgeRuntime } from "@assistant-ui/react";
import { Thread } from "@assistant-ui/react";
import { useLocalRuntime } from "@assistant-ui/react";
import { makeMarkdownText } from "@assistant-ui/react-markdown";

const MarkdownText = makeMarkdownText();

export function MyAssistant() {
  const runtime = useLocalRuntime({ api: "/api/chat" });

  return (
    <Thread
      assistantMessage={{ components: { Text: MarkdownText } }}
    />
  );
}
