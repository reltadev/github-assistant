import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { PlusCircle, PlusIcon } from "lucide-react";
import Link from "next/link";

const repositories = [
  { name: "CrewAI", orgId: "joaomdmoura/crewAI", id: "joaomdmoura&crewAI" },
  {
    name: "LangChain",
    orgId: "langchain-ai/langchain",
    id: "langchain-ai&langchain",
  },
  {
    name: "LlamaIndex",
    orgId: "jerryjliu/llama_index",
    id: "jerryjliu&llama_index",
  },
  {
    name: "Transformers",
    orgId: "huggingface/transformers",
    id: "huggingface&transformers",
  },
  { name: "Whisper", orgId: "openai/whisper", id: "openai&whisper" },
  { name: "GPT-3", orgId: "openai/gpt-3", id: "openai&gpt-3" },
  { name: "DALL-E", orgId: "openai/DALL-E", id: "openai&DALL-E" },
  {
    name: "Stable Diffusion",
    orgId: "CompVis/stable-diffusion",
    id: "CompVis&stable-diffusion",
  },
  {
    name: "Anthropic",
    orgId: "anthropics/anthropic-ai",
    id: "anthropics&anthropic-ai",
  },
  {
    name: "Midjourney",
    orgId: "midjourney/midjourney",
    id: "midjourney&midjourney",
  },
];

export default function RepoSelection() {
  return (
    <div className="container mx-auto px-4 py-8 min-h-dvh flex flex-col justify-center">
      <div>
        <h1 className="text-3xl font-bold text-center mb-8">
          Which repository do you want to explore?
        </h1>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
          {repositories.map((repo) => (
            <Link href={`/repo/${repo.id}`} key={repo.id}>
              <Card className="aspect-[5/3] hover:bg-muted/20 transition-all hover:shadow-md shadow-none">
                <CardHeader>
                  <h2 className="text-xl font-semibold mb-1">{repo.name}</h2>
                  <p className="text-sm text-gray-500">{repo.orgId}</p>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>

        <div className="border-t border-gray-200 my-8"></div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
          <Link href="/new-repo">
            <Card className="aspect-[5/3] hover:bg-muted/20 transition-all shadow-none border-dashed border-2">
              <CardHeader className="flex flex-row items-center gap-2">
                <PlusIcon className="size-4" />
                <h2 className="leading-0 !mt-0">Import Repository</h2>
              </CardHeader>
            </Card>
          </Link>
        </div>
      </div>
    </div>
  );
}
