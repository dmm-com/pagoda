import { DependencyList } from "react";
import { useAsync } from "react-use";
import {
  FunctionReturningPromise,
  PromiseType,
} from "react-use/lib/misc/types";

import { isResponseError, toError } from "../services/AironeAPIErrorUtil";

export declare type AsyncState<T> =
  | {
      loading: boolean;
      value?: undefined;
    }
  | {
      loading: true;
      value?: T;
    }
  | {
      loading: false;
      value?: undefined;
    }
  | {
      loading: false;
      value: T;
    };

// A thin wrapper of useAsync() in react-use, but it will throw an error
export const useAsyncWithThrow = <T extends FunctionReturningPromise>(
  fn: T,
  deps?: DependencyList
): AsyncState<PromiseType<ReturnType<T>>> => {
  const raw = useAsync(fn, deps);

  if (raw.error != null) {
    if (isResponseError(raw.error)) {
      const httpError = toError(raw.error.response);
      if (httpError != null) {
        throw httpError;
      }
    }
    throw raw.error;
  }

  return {
    loading: raw.loading,
    value: raw.value,
  };
};
