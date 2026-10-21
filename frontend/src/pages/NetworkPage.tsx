import {
  Container,
  Link as MuiLink,
  Pagination,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { FC } from "react";
import { Link } from "react-router";

import { Loading, SearchBox } from "components";
import { useSimpleSearch } from "hooks";
import { useAsync } from "hooks/useAsync";
import { useTranslation } from "hooks/useTranslation";
import { aironeApiClient } from "repository";
import { entryDetailsPath } from "routes";

const PAGE_SIZE = 30;

export const NetworkPage: FC = () => {
  const { t } = useTranslation();
  const [query, page, submitQuery, changePage] = useSimpleSearch();
  const entries = useAsync(
    async () =>
      query
        ? aironeApiClient.getNetworkSearchEntries(
            query,
            (page - 1) * PAGE_SIZE,
            PAGE_SIZE,
          )
        : { results: [], hasMore: false, totalHits: 0 },
    [query, page],
  );
  const totalHits = entries.value?.totalHits ?? 0;
  const totalPages = Math.ceil(totalHits / PAGE_SIZE);
  const visibleEntries = entries.value?.results ?? [];

  return (
    <Container sx={{ mt: 2 }}>
      <SearchBox
        placeholder={t("common.search")}
        defaultValue={query}
        onKeyPress={(event, value) => {
          if (event.key === "Enter") submitQuery(value);
        }}
        autoFocus
      />
      {entries.loading ? (
        <Loading />
      ) : entries.error ? (
        <Typography color="error">{entries.error.message}</Typography>
      ) : query ? (
        <>
          <Typography sx={{ mt: 3 }}>
            {t("networkSearch.summary", {
              totalHits: totalHits.toLocaleString(),
              totalPages: totalPages.toLocaleString(),
            })}
          </Typography>
          <TableContainer sx={{ mt: 2 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>{t("networkSearch.model")}</TableCell>
                  <TableCell>{t("networkSearch.item")}</TableCell>
                  <TableCell>{t("networkSearch.attribute")}</TableCell>
                  <TableCell>{t("networkSearch.value")}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {visibleEntries.flatMap((entry) =>
                  (entry.matches.length
                    ? entry.matches
                    : [{ name: "", value: "" }]
                  ).map((match, index) => (
                    <TableRow key={`${entry.id}-${index}`}>
                      <TableCell>{entry.schema?.name}</TableCell>
                      <TableCell>
                        <MuiLink
                          component={Link}
                          to={entryDetailsPath(entry.schema?.id ?? 0, entry.id)}
                        >
                          {entry.name}
                        </MuiLink>
                      </TableCell>
                      <TableCell>{match.name || "—"}</TableCell>
                      <TableCell
                        sx={{
                          whiteSpace: "pre-wrap",
                          overflowWrap: "anywhere",
                        }}
                      >
                        {match.value || "—"}
                      </TableCell>
                    </TableRow>
                  )),
                )}
              </TableBody>
            </Table>
          </TableContainer>
          {visibleEntries.length === 0 && (
            <Typography sx={{ mt: 2 }}>{t("networkSearch.empty")}</Typography>
          )}
          {totalPages > 0 && (
            <Stack spacing={1} alignItems="center" mt={3}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={(_, newPage) => changePage(newPage)}
                color="primary"
              />
            </Stack>
          )}
        </>
      ) : null}
    </Container>
  );
};
