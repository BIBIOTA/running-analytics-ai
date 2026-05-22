export type ApiClientOptions<TBody = unknown> = {
  url: string;
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  headers?: HeadersInit;
  data?: TBody;
  params?: Record<string, unknown>;
  signal?: AbortSignal;
};

const API_PREFIX = "/api";

const serializeSearchParams = (params?: Record<string, unknown>) => {
  const searchParams = new URLSearchParams();

  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (Array.isArray(value)) {
      value.forEach((item) => {
        if (item !== undefined && item !== null) {
          searchParams.append(key, String(item));
        }
      });
    } else if (value !== undefined && value !== null) {
      searchParams.set(key, String(value));
    }
  });

  return searchParams;
};

const parseResponseBody = async <TResponse>(response: Response): Promise<TResponse> => {
  const text = await response.text();

  if (!text) {
    return undefined as TResponse;
  }

  if (response.headers.get("content-type")?.includes("application/json")) {
    try {
      return JSON.parse(text) as TResponse;
    } catch {
      return text as TResponse;
    }
  }

  return text as TResponse;
};

const getErrorMessage = (body: unknown, fallback: string) => {
  if (typeof body === "object" && body !== null) {
    const detail = "detail" in body ? body.detail : undefined;
    const message = "message" in body ? body.message : undefined;

    if (typeof detail === "string") {
      return detail;
    }

    if (typeof message === "string") {
      return message;
    }
  }

  return fallback;
};

export async function apiClient<TResponse, TBody = unknown>({
  url,
  method,
  headers,
  data,
  params,
  signal,
}: ApiClientOptions<TBody>): Promise<TResponse> {
  const searchParams = serializeSearchParams(params);

  const response = await fetch(`${API_PREFIX}${url}${searchParams.size ? `?${searchParams}` : ""}`, {
    method,
    headers: {
      Accept: "application/json",
      ...(data !== undefined ? { "Content-Type": "application/json" } : {}),
      ...headers,
    },
    body: data !== undefined ? JSON.stringify(data) : undefined,
    signal,
  });

  if (!response.ok) {
    const fallback = `API request failed: ${response.status}`;
    const body = await parseResponseBody<unknown>(response);

    throw new Error(getErrorMessage(body, fallback));
  }

  if (response.status === 204) {
    return undefined as TResponse;
  }

  return parseResponseBody<TResponse>(response);
}
