import AppsIcon from "@mui/icons-material/Apps";
import { Box, Container, IconButton, Typography } from "@mui/material";
import React, { FC, useCallback, useMemo, useState } from "react";
import { Link, useHistory, useLocation } from "react-router-dom";
import { useAsync } from "react-use";

import { entitiesPath, entityPath, entryDetailsPath, topPath } from "../Routes";
import { aironeApiClientV2 } from "../apiclient/AironeApiClientV2";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import { Loading } from "../components/common/Loading";
import { EntryControlMenu } from "../components/entry/EntryControlMenu";
import { EntryHistoryList } from "../components/entry/EntryHistoryList";
import { useTypedParams } from "../hooks/useTypedParams";
import { EntryHistoryList as ConstEntryHistoryList } from "../utils/Constants";

export const EntryHistoryListPage: FC = () => {
  const { entryId } = useTypedParams<{ entryId: number }>();

  const history = useHistory();
  const location = useLocation();

  const [page, setPage] = useState(1);
  const [entryAnchorEl, setEntryAnchorEl] =
    useState<HTMLButtonElement | null>();

  const entry = useAsync(async () => {
    return entryId != undefined
      ? await aironeApiClientV2.getEntry(entryId)
      : undefined;
  }, [entryId]);
  const histories = useAsync(async () => {
    return await aironeApiClientV2.getEntryHistories(entryId, page);
  }, [entryId, page]);

  const handleChangePage = useCallback((newPage: number) => {
    setPage(newPage);

    history.push({
      pathname: location.pathname,
      search: `?page=${newPage}`,
    });
  }, []);

  const maxPage = useMemo(() => {
    if (histories.loading) {
      return 0;
    }
    return Math.ceil(
      histories.value.count / ConstEntryHistoryList.MAX_ROW_COUNT
    );
  }, [histories.loading, histories.value?.count]);

  return (
    <Box className="container">
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography component={Link} to={entitiesPath()}>
          エンティティ一覧
        </Typography>
        {!entry.loading && (
          <Typography component={Link} to={entityPath(entry.value.schema.id)}>
            {entry.value.schema.name}
          </Typography>
        )}
        {!entry.loading && (
          <Typography
            component={Link}
            to={entryDetailsPath(entry.value.schema.id, entry.value.id)}
          >
            {entry.value.name}
          </Typography>
        )}
        {!entry.loading && (
          <Typography color="textPrimary">{`${entry.value.name} 変更履歴`}</Typography>
        )}
      </AironeBreadcrumbs>

      <Container maxWidth="lg" sx={{ marginTop: "111px" }}>
        {/* NOTE: This Box component that has CSS tuning should be custom component */}
        <Box
          display="flex"
          sx={{ borderBottom: 1, borderColor: "gray", mb: "64px", pb: "64px" }}
        >
          <Box width="50px" />
          <Box flexGrow="1">
            {!entry.loading && (
              <Typography
                variant="h2"
                align="center"
                sx={{
                  margin: "auto",
                  maxWidth: "md",
                  textOverflow: "ellipsis",
                  overflow: "hidden",
                  whiteSpace: "nowrap",
                }}
              >
                {entry.value.name}
              </Typography>
            )}
            <Typography variant="h4" align="center">
              変更履歴
            </Typography>
          </Box>
          <Box width="50px">
            <IconButton
              onClick={(e) => {
                setEntryAnchorEl(e.currentTarget);
              }}
            >
              <AppsIcon />
            </IconButton>
            <EntryControlMenu
              entityId={entry.value?.schema?.id}
              entryId={entryId}
              anchorElem={entryAnchorEl}
              handleClose={() => setEntryAnchorEl(null)}
            />
          </Box>
        </Box>
        <Box>
          {histories.loading ? (
            <Loading />
          ) : (
            <EntryHistoryList
              histories={histories.value.results}
              entryId={entryId}
              page={page}
              maxPage={maxPage}
              handleChangePage={handleChangePage}
            />
          )}
        </Box>
      </Container>
    </Box>
  );
};
