import useSWR, { type Key, type SWRConfiguration, type SWRResponse } from "swr";

import { isResponseError, toError } from "../services/AironeAPIErrorUtil";

export function wrapFetcher<T>(fetcher: () => Promise<T>): () => Promise<T> {
  return async () => {
    try {
      return await fetcher();
    } catch (e) {
      if (e instanceof Error && isResponseError(e)) {
        const httpError = toError(e.response);
        if (httpError != null) throw httpError;
      }
      throw e;
    }
  };
}

// Overload: suspense mode — data is always T
export function usePagodaSWR<T>(
  key: Key,
  fetcher: () => Promise<T>,
  config: Omit<SWRConfiguration<T>, "suspense"> & { suspense: true },
): Omit<SWRResponse<T>, "data"> & { data: T };

// Overload: normal mode — data is T | undefined
export function usePagodaSWR<T>(
  key: Key,
  fetcher: (() => Promise<T>) | null,
  config?: SWRConfiguration<T>,
): SWRResponse<T>;

// Implementation
export function usePagodaSWR<T>(
  key: Key,
  fetcher: (() => Promise<T>) | null,
  config?: SWRConfiguration<T>,
): SWRResponse<T> {
  const result = useSWR<T>(key, fetcher ? wrapFetcher(fetcher) : null, config);

  if (result.error != null) {
    throw result.error;
  }

  return result;
}
