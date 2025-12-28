import { useParams } from "react-router";

interface UseTypedParamsOptions {
  allowEmpty?: boolean;
}

export const useTypedParams = <
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  Params extends { [K in keyof Params]: any },
>(
  options: UseTypedParamsOptions = {},
): Required<Params> => {
  const { allowEmpty = false } = options;
  const params = useParams();

  const keys = Object.keys(params);
  if (!allowEmpty && keys.length === 0) {
    throw new Error("No URL parameters found");
  }

  const allFieldsDefined = keys.every((key) => params[key] !== undefined);
  if (!allFieldsDefined) {
    throw new Error("Some required URL parameters are missing");
  }

  return params as unknown as Required<Params>;
};
