import { useParams } from "react-router-dom";

export const useTypedParams = <
  Params extends { [K in keyof Params]?: any },
>() => {
  return useParams<Params>();
};
