import { FlatNamespace, i18n, KeyPrefix } from "i18next";
import { useTranslation as _useTranslation } from "react-i18next";
import { FallbackNs, UseTranslationOptions } from "react-i18next";
import { $Tuple } from "react-i18next/helpers";

import { TranslationKey } from "../i18n/config";

export type UseTranslationResponse = [
  t: (key: TranslationKey) => string,
  i18n: i18n,
  ready: boolean,
] & {
  t: (key: TranslationKey) => string;
  i18n: i18n;
  ready: boolean;
};
export function useTranslation<
  Ns extends FlatNamespace | $Tuple<FlatNamespace> | undefined = undefined,
  KPrefix extends KeyPrefix<FallbackNs<Ns>> = undefined,
>(ns?: Ns, options?: UseTranslationOptions<KPrefix>): UseTranslationResponse {
  const response = _useTranslation(ns, options);

  // thin wrapper forces the key to be predefined
  const t = (key: TranslationKey): string => {
    return response.t(key);
  };

  return {
    ...response,
    t,
  };
}
