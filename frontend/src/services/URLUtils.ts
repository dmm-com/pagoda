import { matchRoutes, useLocation } from "react-router-dom"

export type TypeURLParams = {
  [key: string]: string | undefined;
} | undefined;

export const getURLParams = (routePath: string | undefined): TypeURLParams => {
  const location = useLocation();

  const m = matchRoutes([{path: routePath ?? ""}], location);
  if (Array.isArray(m) && m.length > 0) {
    return m[0].params;
  }

  return {};
}
