import AppsIcon from "@mui/icons-material/Apps";
import { Box, Container, IconButton } from "@mui/material";
import React, { FC, useState } from "react";

import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";

import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { EntryBreadcrumbs } from "components/entry/EntryBreadcrumbs";
import { EntryControlMenu } from "components/entry/EntryControlMenu";
import { EntryHistoryList } from "components/entry/EntryHistoryList";
import { usePage } from "hooks/usePage";
import { useTypedParams } from "hooks/useTypedParams";
import { aironeApiClient } from "repository/AironeApiClient";

export const EntryHistoryListPage: FC = () => {
  const { entryId } = useTypedParams<{ entityId: number; entryId: number }>();

  const [page, changePage] = usePage();

  const [entryAnchorEl, setEntryAnchorEl] = useState<HTMLButtonElement | null>(
    null
  );

  const entry = useAsyncWithThrow(async () => {
    return entryId != undefined
      ? await aironeApiClient.getEntry(entryId)
      : undefined;
  }, [entryId]);

  const histories = useAsyncWithThrow(async () => {
    return await aironeApiClient.getEntryHistories(entryId, page);
  }, [entryId, page]);

  return (
    <Box className="container">
      <EntryBreadcrumbs entry={entry.value} title="変更履歴" />

      <PageHeader title={entry.value?.name ?? ""} description="変更履歴">
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
      </PageHeader>

      {histories.loading || !histories.value ? (
        <Loading />
      ) : (
        <Container>
          <EntryHistoryList
            entityId={entry.value?.schema?.id ?? 0}
            entryId={entryId}
            histories={histories.value}
            page={page}
            changePage={changePage}
          />
        </Container>
      )}
    </Box>
  );
};
