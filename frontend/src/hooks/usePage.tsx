import { startTransition, useCallback, useMemo } from "react";
import { useNavigate, useLocation } from "react-router";

type UsePageReturn = {
  page: number;
  query: string;
  changePage: (page: number) => void;
  changeQuery: (query: string) => void;
};

/**
 * A hook provides page number and query to perform pagination and filtering.
 */
export const usePage = (): UsePageReturn => {
  const location = useLocation();
  const navigate = useNavigate();

  const { page, query } = useMemo(() => {
    const params = new URLSearchParams(location.search);
    const pageParam = params.get("page");
    const pageNumber = pageParam ? Number(pageParam) : 1;
    return {
      page: isNaN(pageNumber) ? 1 : pageNumber,
      query: params.has("query")
        ? decodeURIComponent(params.get("query") ?? "")
        : "",
    };
  }, [location.search]);

  const changePage = useCallback(
    (newPage: number) => {
      startTransition(() => {
        const params = new URLSearchParams(location.search);
        params.set("page", newPage.toString());
        navigate({
          pathname: location.pathname,
          search: params.toString(),
        });
      });
    },
    [location.pathname, location.search, navigate],
  );

  const changeQuery = useCallback(
    (newQuery: string) => {
      startTransition(() => {
        const params = new URLSearchParams();
        if (newQuery) {
          params.set("query", encodeURIComponent(newQuery));
        }
        params.set("page", "1");
        navigate({
          pathname: location.pathname,
          search: params.toString(),
        });
      });
    },
    [location.pathname, navigate],
  );

  return { page, query, changePage, changeQuery };
};
