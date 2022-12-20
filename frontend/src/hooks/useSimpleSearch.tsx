import { useCallback, useMemo } from "react";
import { useHistory, useLocation } from "react-router-dom";

import { topPath } from "../Routes";

type Query = string | null;

export const useSimpleSearch = (): [Query, (query: Query) => void] => {
  const location = useLocation();
  const history = useHistory();

  const query = useMemo(() => {
    const params = new URLSearchParams(location.search);
    return params.get("simple_search_query");
  }, [location.search]);

  const submitQuery = useCallback(
    (query: string) => {
      history.push({
        pathname: topPath(),
        search: `simple_search_query=${query}`,
      });
    },
    [history]
  );

  return [query, submitQuery];
};
