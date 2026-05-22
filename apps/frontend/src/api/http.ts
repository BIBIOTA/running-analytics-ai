export type ApiClientOptions<TBody = unknown> = {
  url: string;
  method: string;
  headers?: HeadersInit;
  data?: TBody;
  params?: Record<string, unknown>;
  signal?: AbortSignal;
};

const API_PREFIX = "/api";

export async function apiClient<TResponse, TBody = unknown>({
  url,
  method,
  headers,
  data,
  params,
  signal,
}: ApiClientOptions<TBody>): Promise<TResponse> {
  const searchParams = new URLSearchParams();

  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      searchParams.set(key, String(value));
    }
  });

  const response = await fetch(`${API_PREFIX}${url}${searchParams.size ? `?${searchParams}` : ""}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    body: data === undefined ? undefined : JSON.stringify(data),
    signal,
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as TResponse;
  }

  return response.json() as Promise<TResponse>;
}
