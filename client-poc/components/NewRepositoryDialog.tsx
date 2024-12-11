"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { useAuth, useSignIn } from "@clerk/nextjs";
import { MouseEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";

const GITHUB_URL_REGEX =
  /^https?:\/\/(?:www\.)?github\.com\/(?<owner>[^\/]+)\/(?<repo>[^\/]+)(?:\/.*)?(?:\.git)?\/?$/;

const newRepoSchema = z.object({
  githubUrl: z
    .string()
    .url("Please enter a valid URL.")
    .regex(GITHUB_URL_REGEX, "Please enter a valid GitHub repository URL."),
});

type NewRepoFormData = z.infer<typeof newRepoSchema>;

type NewRepositoryDialogProps = {
  trigger: React.ReactNode;
};

export function NewRepositoryDialog({ trigger }: NewRepositoryDialogProps) {
  const form = useForm<NewRepoFormData>({
    resolver: zodResolver(newRepoSchema),
    defaultValues: { githubUrl: "" },
  });

  const searchParams = useSearchParams();

  const { signIn } = useSignIn();
  const auth = useAuth();
  const ensureLogin = async (e?: MouseEvent<HTMLButtonElement>) => {
    if (!auth.isLoaded) {
      e?.preventDefault();
      return false;
    }
    if (!auth.isSignedIn) {
      e?.preventDefault();
      await signIn?.authenticateWithRedirect({
        strategy: "oauth_github",
        redirectUrl: "/sso-callback",
        redirectUrlComplete: "/?open_new=true",
      });
      return false;
    }
    return true;
  };

  const router = useRouter();
  const onSubmit = async (data: NewRepoFormData) => {
    if (!ensureLogin()) return;

    const { owner, repo } =
      data.githubUrl.match(GITHUB_URL_REGEX)?.groups ?? {};
    if (!owner || !repo) return;

    await fetch("/api/import", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ owner, repo }),
    });
    router.push(`/repo/${owner}/${repo}`);
  };

  return (
    <Dialog defaultOpen={!!searchParams.get("open_new")}>
      <DialogTrigger onClick={ensureLogin}>{trigger}</DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>New Repository</DialogTitle>
          <DialogDescription>
            Add a new repository. We might ask you to sign in to GitHub to
            proceed. Only PUBLIC repositories are supported.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
            <FormField
              control={form.control}
              name="githubUrl"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>GitHub URL</FormLabel>
                  <FormControl>
                    <Input placeholder="https://github.com/..." {...field} />
                  </FormControl>
                  <FormDescription>
                    The GitHub URL of the repository you want to import.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="text-end">
              <Button type="submit">Import</Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
