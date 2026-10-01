import { FlatNamespace, i18n, KeyPrefix } from "i18next";
import { useCallback } from "react";
import { useTranslation as _useTranslation } from "react-i18next";
import { FallbackNs, UseTranslationOptions } from "react-i18next";

import { TranslationKey, TranslationOptions } from "../i18n/config";

type TranslateFunction = (
  key: TranslationKey,
  options?: TranslationOptions,
) => string;

type NamespaceTuple<T> = readonly [T?, ...T[]];

export type UseTranslationResponse = [
  t: TranslateFunction,
  i18n: i18n,
  ready: boolean,
] & {
  t: TranslateFunction;
  i18n: i18n;
  ready: boolean;
};
export function useTranslation<
  Ns extends
    | FlatNamespace
    | NamespaceTuple<FlatNamespace>
    | undefined = undefined,
  KPrefix extends KeyPrefix<FallbackNs<Ns>> = undefined,
>(ns?: Ns, options?: UseTranslationOptions<KPrefix>): UseTranslationResponse {
  const response = _useTranslation(ns, options);

  // thin wrapper forces the key to be predefined; memoized so that `t` keeps
  // a stable identity across renders (safe to use in hook dependency arrays)
  const responseT = response.t;
  const t: TranslateFunction = useCallback(
    (key, translationOptions) => responseT(key, translationOptions),
    [responseT],
  );

  // Build an array with named properties to support both
  // array destructuring (const [t, i18n, ready] = ...) and
  // object access (result.t, result.i18n, result.ready).
  const result = Object.assign([t, response.i18n, response.ready], {
    t,
    i18n: response.i18n,
    ready: response.ready,
  });
  return result as unknown as UseTranslationResponse;
}
