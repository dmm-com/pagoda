import { useCallback, useEffect, useState } from "react";
import { useHistory, useLocation } from "react-router-dom";

/**
 * A hook provides page number to perform pagination.
 *
 */
export const usePage = (): [number, (page: number) => void] => {
  const location = useLocation();
  const history = useHistory();

  const [page, setPage] = useState<number>(1);

  const changePage = useCallback(
    (newPage: number) => {
      setPage(newPage);

      const params = new URLSearchParams(location.search);
      params.set("page", newPage.toString());

      history.push({
        pathname: location.pathname,
        search: params.toString(),
      });
    },
    [location.pathname, location.search],
  );

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    setPage(params.has("page") ? Number(params.get("page")) : 1);
  }, [location.search]);

  return [page, changePage];
};
