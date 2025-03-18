import { useParams } from "react-router";

export const useTypedParams = <
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  Params extends { [K in keyof Params]: any },
>() => {
  const params = useParams() as unknown as Partial<Params>;

  const allFieldsDefined = Object.keys(params).every(
    (key) => params[key as keyof Params] !== undefined,
  );
  if (!allFieldsDefined) {
    throw new Error("Some required URL parameters are missing");
  }

  return params as Required<Params>;
};
