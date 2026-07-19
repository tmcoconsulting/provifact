import { handleRequest } from "./router";
import type { WorkerEnv } from "./env";
import { HttpError, jsonResponse } from "./security";

export default {
  async fetch(request: Request, env: WorkerEnv): Promise<Response> {
    const requestId = crypto.randomUUID();
    const url = new URL(request.url);
    try {
      const response = await handleRequest(request, env);
      const securedResponse = new Response(response.body, response);
      securedResponse.headers.set("X-Request-ID", requestId);
      logEvent(
        requestId,
        safeMethod(request.method),
        safeRoute(url.pathname),
        response.status,
        "request_completed",
      );
      return securedResponse;
    } catch (error) {
      if (error instanceof HttpError) {
        logEvent(
          requestId,
          safeMethod(request.method),
          safeRoute(url.pathname),
          error.status,
          error.code,
        );
        return jsonResponse(
          {
            error: error.code,
            message: error.message,
            human_review_required: true,
          },
          error.status,
          { "X-Request-ID": requestId },
        );
      }
      logEvent(
        requestId,
        safeMethod(request.method),
        safeRoute(url.pathname),
        500,
        "unhandled_error",
      );
      return jsonResponse(
        {
          error: "internal_error",
          message: "EvidenceOps could not complete the request",
          human_review_required: true,
        },
        500,
        { "X-Request-ID": requestId },
      );
    }
  },
} satisfies ExportedHandler<Env>;

function logEvent(
  requestId: string,
  method: string,
  path: string,
  status: number,
  event: string,
): void {
  console.log(
    JSON.stringify({
      event,
      request_id: requestId,
      method,
      path,
      status,
    }),
  );
}

function safeMethod(method: string): "GET" | "POST" | "OTHER" {
  if (method === "GET" || method === "POST") {
    return method;
  }
  return "OTHER";
}

function safeRoute(
  path: string,
): "api-narrative" | "api-other" | "api-status" | "static" {
  if (path === "/api/narrative") {
    return "api-narrative";
  }
  if (path === "/api/status") {
    return "api-status";
  }
  if (path.startsWith("/api/")) {
    return "api-other";
  }
  return "static";
}
