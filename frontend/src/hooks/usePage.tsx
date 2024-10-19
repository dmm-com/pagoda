import { useCallback, useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";

/**
 * A hook provides page number to perform pagination.
 *
 */
export const usePage = (): [number, (page: number) => void] => {
  const location = useLocation();
  const navigate = useNavigate();

  const [page, setPage] = useState<number>(1);

  const changePage = useCallback(
    (newPage: number) => {
      setPage(newPage);

      const params = new URLSearchParams(location.search);
      params.set("page", newPage.toString());

      navigate({
        pathname: location.pathname,
        search: params.toString(),
      });
    },
    [location.pathname, location.search, navigate]
  );

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    setPage(params.has("page") ? Number(params.get("page")) : 1);
  }, [location.search]);

  return [page, changePage];
};
