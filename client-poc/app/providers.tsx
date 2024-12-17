"use client";

import { makeQueryClient } from "@/lib/makeQueryClient";
import { ClerkProvider } from "@clerk/nextjs";
import {
  isServer,
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";
import { PropsWithChildren } from "react";
import posthog from "posthog-js";
import { PostHogProvider } from "posthog-js/react";

let browserQueryClient: QueryClient | undefined = undefined;

export function getQueryClient() {
  if (isServer) {
    // Server: always make a new query client
    return makeQueryClient();
  } else {
    // Browser: make a new query client if we don't already have one
    if (!browserQueryClient) browserQueryClient = makeQueryClient();
    return browserQueryClient;
  }
}

if (typeof window !== "undefined") {
  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
    api_host: "/ingest",
    ui_host: "https://us.posthog.com",
    person_profiles: "identified_only", // or 'always' to create profiles for anonymous users as well
  });
}

export default function Providers({ children }: PropsWithChildren) {
  const queryClient = getQueryClient();

  return (
    <ClerkProvider>
      <PostHogProvider client={posthog}>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </PostHogProvider>
    </ClerkProvider>
  );
}
