import AppsIcon from "@mui/icons-material/Apps";
import { Box, Container, Divider, IconButton, Typography } from "@mui/material";
import { FC, Suspense, useState } from "react";

import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { EntryBreadcrumbs } from "components/entry/EntryBreadcrumbs";
import { EntryControlMenu } from "components/entry/EntryControlMenu";
import { EntryHistoryList } from "components/entry/EntryHistoryList";
import { EntrySelfHistoryList } from "components/entry/EntrySelfHistoryList";
import { usePage } from "hooks/usePage";
import { usePagodaSWR } from "hooks/usePagodaSWR";
import { useTranslation } from "hooks/useTranslation";
import { useTypedParams } from "hooks/useTypedParams";
import { aironeApiClient } from "repository/AironeApiClient";

const SelfHistorySection: FC<{
  entryId: number;
  entityId: number;
  page: number;
  changePage: (page: number) => void;
}> = ({ entryId, entityId, page, changePage }) => {
  const { data: selfHistories } = usePagodaSWR(
    ["entrySelfHistories", entryId, page],
    () => aironeApiClient.getEntrySelfHistories(entryId, page),
    { suspense: true },
  );

  return (
    <EntrySelfHistoryList
      entityId={entityId}
      entryId={entryId}
      histories={selfHistories}
      page={page}
      changePage={changePage}
    />
  );
};

const AttributeHistorySection: FC<{
  entryId: number;
  entityId: number;
  page: number;
  changePage: (page: number) => void;
}> = ({ entryId, entityId, page, changePage }) => {
  const { data: histories } = usePagodaSWR(
    ["entryHistories", entryId, page],
    () => aironeApiClient.getEntryHistories(entryId, page),
    { suspense: true },
  );

  return (
    <EntryHistoryList
      entityId={entityId}
      entryId={entryId}
      histories={histories}
      page={page}
      changePage={changePage}
    />
  );
};

const EntryHistoryListContent: FC = () => {
  const { t } = useTranslation();
  const { entryId } = useTypedParams<{ entityId: number; entryId: number }>();

  const { page: attributeHistoryPage, changePage: changeAttributeHistoryPage } =
    usePage();
  const { page: selfHistoryPage, changePage: changeSelfHistoryPage } =
    usePage();

  const [entryAnchorEl, setEntryAnchorEl] = useState<HTMLButtonElement | null>(
    null,
  );

  const { data: entry } = usePagodaSWR(
    ["entry", entryId],
    () => aironeApiClient.getEntry(entryId),
    { suspense: true },
  );

  return (
    <Box className="container">
      <EntryBreadcrumbs entry={entry} title={t("entry.common.changeHistory")} />

      <PageHeader
        title={entry.name ?? ""}
        description={t("entry.common.changeHistory")}
      >
        <Box width="50px">
          <IconButton
            onClick={(e) => {
              setEntryAnchorEl(e.currentTarget);
            }}
          >
            <AppsIcon />
          </IconButton>
          <EntryControlMenu
            entityId={entry.schema?.id ?? 0}
            entryId={entryId}
            anchorElem={entryAnchorEl}
            handleClose={() => setEntryAnchorEl(null)}
            permission={entry.permission}
            entityPermission={entry.schema?.permission}
          />
        </Box>
      </PageHeader>

      <Container>
        <Box sx={{ mb: 4 }}>
          <Typography
            variant="h6"
            sx={{ mb: 2, color: "#455A64", fontWeight: "bold" }}
          >
            {t("entry.historyPage.selfHistorySection")}
          </Typography>
          <Suspense fallback={<Loading />}>
            <SelfHistorySection
              entryId={entryId}
              entityId={entry.schema?.id ?? 0}
              page={selfHistoryPage}
              changePage={changeSelfHistoryPage}
            />
          </Suspense>
        </Box>

        <Divider sx={{ my: 3 }} />

        <Box>
          <Typography
            variant="h6"
            sx={{ mb: 2, color: "#455A64", fontWeight: "bold" }}
          >
            {t("entry.historyPage.attrHistorySection")}
          </Typography>
          <Suspense fallback={<Loading />}>
            <AttributeHistorySection
              entryId={entryId}
              entityId={entry.schema?.id ?? 0}
              page={attributeHistoryPage}
              changePage={changeAttributeHistoryPage}
            />
          </Suspense>
        </Box>
      </Container>
    </Box>
  );
};

export const EntryHistoryListPage: FC = () => {
  return (
    <Suspense fallback={<Loading />}>
      <EntryHistoryListContent />
    </Suspense>
  );
};
