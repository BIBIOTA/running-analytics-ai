import { afterEach, describe, expect, test, vi } from "vitest";
import { apiClient } from "./http";

const jsonResponse = (body: unknown, init?: ResponseInit) =>
  new Response(JSON.stringify(body), {
    headers: { "content-type": "application/json" },
    ...init,
  });

describe("apiClient", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  test("uses response detail when an API request fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse({ detail: "Token expired" }, { status: 401 })),
    );

    await expect(apiClient({ url: "/auth/me", method: "GET" })).rejects.toThrow("Token expired");
  });

  test("returns undefined for an empty successful response body", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("", { status: 200 })));

    await expect(apiClient({ url: "/empty", method: "GET" })).resolves.toBeUndefined();
  });

  test("returns text for non-JSON successful responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("data: chunk", { headers: { "content-type": "text/event-stream" } })),
    );

    await expect(apiClient({ url: "/ai/ask", method: "POST", data: { prompt: "hi" } })).resolves.toBe(
      "data: chunk",
    );
  });

  test("serializes array query parameters as repeated keys", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    await apiClient({
      url: "/activities",
      method: "GET",
      params: { ids: ["1", "2"], filter: "run" },
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/activities?ids=1&ids=2&filter=run",
      expect.objectContaining({ method: "GET" }),
    );
  });

  test("only sends content-type and body when request data is present", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    await apiClient({ url: "/activities", method: "GET" });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/activities",
      expect.objectContaining({
        body: undefined,
        headers: { Accept: "application/json" },
      }),
    );
  });
});
