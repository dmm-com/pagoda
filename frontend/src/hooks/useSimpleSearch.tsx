import { useCallback, useMemo } from "react";
import { useHistory, useLocation } from "react-router-dom";

import { topPath } from "../Routes";

type Query = string | undefined;

export const useSimpleSearch = (): [Query, (query: Query) => void] => {
  const location = useLocation();
  const history = useHistory();

  const query = useMemo(() => {
    const params = new URLSearchParams(location.search);
    return params.get("simple_search_query") ?? undefined;
  }, [location.search]);

  const submitQuery = useCallback(
    (query: Query) => {
      history.push({
        pathname: topPath(),
        search: query != null ? `simple_search_query=${query}` : undefined,
      });
    },
    [history],
  );

  return [query, submitQuery];
};
