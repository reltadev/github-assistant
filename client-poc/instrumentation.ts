import { registerOTel } from "@vercel/otel";
import { AISDKExporter } from "langsmith/vercel";

export function register() {
  registerOTel({
    serviceName: "github-assistant",
    traceExporter: new AISDKExporter(),
  });
}
