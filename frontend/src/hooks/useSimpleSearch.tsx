import { useCallback, useMemo } from "react";
import { useNavigate, useLocation } from "react-router-dom";

import { topPath } from "../Routes";

type Query = string | undefined;

export const useSimpleSearch = (): [Query, (query: Query) => void] => {
  const location = useLocation();
  const navigate = useNavigate();

  const query = useMemo(() => {
    const params = new URLSearchParams(location.search);
    return params.get("simple_search_query") ?? undefined;
  }, [location.search]);

  const submitQuery = useCallback(
    (query: Query) => {
      navigate({
        pathname: topPath(),
        search: query != null ? `simple_search_query=${query}` : undefined,
      });
    },
    [navigate]
  );

  return [query, submitQuery];
};
