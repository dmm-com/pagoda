import AppsIcon from "@mui/icons-material/Apps";
import { Box, Container, Divider, IconButton, Typography } from "@mui/material";
import { FC, useState } from "react";

import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";

import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { EntryBreadcrumbs } from "components/entry/EntryBreadcrumbs";
import { EntryControlMenu } from "components/entry/EntryControlMenu";
import { EntryHistoryList } from "components/entry/EntryHistoryList";
import { EntrySelfHistoryList } from "components/entry/EntrySelfHistoryList";
import { usePage } from "hooks/usePage";
import { useTypedParams } from "hooks/useTypedParams";
import { aironeApiClient } from "repository/AironeApiClient";

export const EntryHistoryListPage: FC = () => {
  const { entryId } = useTypedParams<{ entityId: number; entryId: number }>();

  const { page: attributeHistoryPage, changePage: changeAttributeHistoryPage } =
    usePage();
  const { page: selfHistoryPage, changePage: changeSelfHistoryPage } =
    usePage();

  const [entryAnchorEl, setEntryAnchorEl] = useState<HTMLButtonElement | null>(
    null,
  );

  const entry = useAsyncWithThrow(async () => {
    return entryId != undefined
      ? await aironeApiClient.getEntry(entryId)
      : undefined;
  }, [entryId]);

  const histories = useAsyncWithThrow(async () => {
    return await aironeApiClient.getEntryHistories(
      entryId,
      attributeHistoryPage,
    );
  }, [entryId, attributeHistoryPage]);

  const selfHistories = useAsyncWithThrow(async () => {
    return await aironeApiClient.getEntrySelfHistories(
      entryId,
      selfHistoryPage,
    );
  }, [entryId, selfHistoryPage]);

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

      <Container>
        <Box sx={{ mb: 4 }}>
          <Typography
            variant="h6"
            sx={{ mb: 2, color: "#455A64", fontWeight: "bold" }}
          >
            アイテム変更履歴
          </Typography>
          {selfHistories.loading || !selfHistories.value ? (
            <Loading />
          ) : (
            <EntrySelfHistoryList
              entityId={entry.value?.schema?.id ?? 0}
              entryId={entryId}
              histories={selfHistories.value}
              page={selfHistoryPage}
              changePage={changeSelfHistoryPage}
            />
          )}
        </Box>

        <Divider sx={{ my: 3 }} />

        <Box>
          <Typography
            variant="h6"
            sx={{ mb: 2, color: "#455A64", fontWeight: "bold" }}
          >
            属性変更履歴
          </Typography>
          {histories.loading || !histories.value ? (
            <Loading />
          ) : (
            <EntryHistoryList
              entityId={entry.value?.schema?.id ?? 0}
              entryId={entryId}
              histories={histories.value}
              page={attributeHistoryPage}
              changePage={changeAttributeHistoryPage}
            />
          )}
        </Box>
      </Container>
    </Box>
  );
};
