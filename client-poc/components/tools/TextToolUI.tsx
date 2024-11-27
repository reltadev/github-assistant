"use client";

import { makeAssistantToolUI } from "@assistant-ui/react";
import { MousePointerClickIcon } from "lucide-react";

export const TextToolUI = makeAssistantToolUI<
  Record<string, never>,
  Record<string, never>
>({
  toolName: "text",
  render: ({ result }) => {
    if (!result)
      return (
        <div className="flex items-center gap-1 animate-pulse">
          <MousePointerClickIcon className="size-4" />
          <span>Querying Relta...</span>
        </div>
      );

    return (
      <div className="flex items-center gap-1">
        <MousePointerClickIcon className="size-4" />
        <span>Queried Relta</span>
      </div>
    );
  },
});
