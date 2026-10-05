import { useParams } from "react-router";

import { NotFoundError } from "../services/Exceptions";

interface IdParamsSpec<R extends string, O extends string> {
  required?: readonly R[];
  optional?: readonly O[];
}

export type IdParams<R extends string, O extends string> = {
  [K in R]: number;
} & {
  [K in O]: number | undefined;
};

const ID_PATTERN = /^\d+$/;

const parseId = (key: string, raw: string): number => {
  if (!ID_PATTERN.test(raw)) {
    throw new NotFoundError(`Invalid URL parameter "${key}": ${raw}`);
  }
  return Number(raw);
};

/**
 * Read numeric ID parameters (e.g. ":entityId") from the current route.
 *
 * URL parameters are always strings at runtime; this hook converts them to
 * numbers so the returned values match their declared types. A missing
 * required parameter or a non-numeric value raises NotFoundError.
 */
export const useIdParams = <R extends string = never, O extends string = never>(
  spec: IdParamsSpec<R, O>,
): IdParams<R, O> => {
  const params = useParams();
  const result: Record<string, number | undefined> = {};

  for (const key of spec.required ?? []) {
    const raw = params[key];
    if (raw === undefined) {
      throw new NotFoundError(`Missing URL parameter "${key}"`);
    }
    result[key] = parseId(key, raw);
  }

  for (const key of spec.optional ?? []) {
    const raw = params[key];
    result[key] = raw === undefined ? undefined : parseId(key, raw);
  }

  // Every key declared in spec has been assigned above.
  return result as IdParams<R, O>;
};
