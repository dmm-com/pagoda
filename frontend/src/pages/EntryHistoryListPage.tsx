import AppsIcon from "@mui/icons-material/Apps";
import { Box, Container, IconButton, Typography } from "@mui/material";
import React, { FC, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAsync } from "react-use";

import { entitiesPath, entityPath, entryDetailsPath, topPath } from "../Routes";
import { aironeApiClientV2 } from "../apiclient/AironeApiClientV2";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import { Loading } from "../components/common/Loading";
import { EntryControlMenu } from "../components/entry/EntryControlMenu";
import { EntryHistoryList } from "../components/entry/EntryHistoryList";
import { usePage } from "../hooks/usePage";
import { useTypedParams } from "../hooks/useTypedParams";
import { EntryHistoryList as ConstEntryHistoryList } from "../utils/Constants";

export const EntryHistoryListPage: FC = () => {
  const { entryId } = useTypedParams<{ entryId: number }>();

  const [page, changePage] = usePage();

  const [entryAnchorEl, setEntryAnchorEl] = useState<HTMLButtonElement | null>(
    null
  );

  const entry = useAsync(async () => {
    return entryId != undefined
      ? await aironeApiClientV2.getEntry(entryId)
      : undefined;
  }, [entryId]);
  const histories = useAsync(async () => {
    return await aironeApiClientV2.getEntryHistories(entryId, page);
  }, [entryId, page]);

  const maxPage = useMemo(() => {
    if (histories.loading) {
      return 0;
    }
    return Math.ceil(
      histories.value?.count ?? 0 / ConstEntryHistoryList.MAX_ROW_COUNT
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
          <Typography
            component={Link}
            to={entityPath(entry.value?.schema?.id ?? 0)}
          >
            {entry.value?.schema?.name}
          </Typography>
        )}
        {!entry.loading && (
          <Typography
            component={Link}
            to={entryDetailsPath(
              entry.value?.schema?.id ?? 0,
              entry.value?.id ?? 0
            )}
          >
            {entry.value?.name}
          </Typography>
        )}
        {!entry.loading && (
          <Typography color="textPrimary">{`${entry.value?.name} 変更履歴`}</Typography>
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
                {entry.value?.name}
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
              entityId={entry.value?.schema?.id ?? 0}
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
              histories={histories.value?.results ?? []}
              entryId={entryId}
              page={page}
              maxPage={maxPage}
              handleChangePage={changePage}
            />
          )}
        </Box>
      </Container>
    </Box>
  );
};
