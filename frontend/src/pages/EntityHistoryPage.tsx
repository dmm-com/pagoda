import AppsIcon from "@mui/icons-material/Apps";
import { Box, Container, IconButton } from "@mui/material";
import React, { FC, useMemo, useState } from "react";
import { useAsync } from "react-use";

import { EntityControlMenu } from "../components/entity/EntityControlMenu";
import { EntityHistoryList } from "../components/entity/EntityHistoryList";
import { EntryImportModal } from "../components/entry/EntryImportModal";
import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";
import { usePage } from "../hooks/usePage";
import { useTypedParams } from "../hooks/useTypedParams";
import { aironeApiClientV2 } from "../repository/AironeApiClientV2";
import { EntityHistoryList as ConstEntityHistoryList } from "../services/Constants";

import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { EntityBreadcrumbs } from "components/entity/EntityBreadcrumbs";

export const EntityHistoryPage: FC = () => {
  const { entityId } = useTypedParams<{ entityId: number }>();

  const [page, changePage] = usePage();

  const [entityAnchorEl, setEntityAnchorEl] =
    useState<HTMLButtonElement | null>(null);
  const [openImportModal, setOpenImportModal] = React.useState(false);

  const entity = useAsyncWithThrow(async () => {
    return await aironeApiClientV2.getEntity(entityId);
  }, [entityId]);
  const histories = useAsync(async () => {
    return await aironeApiClientV2.getEntityHistories(entityId, page);
  }, [entityId, page]);

  const totalPageCount = useMemo(() => {
    return histories.loading
      ? 0
      : Math.ceil(
          (histories.value?.count ?? 0) / ConstEntityHistoryList.MAX_ROW_COUNT
        );
  }, [histories.loading, histories.value]);

  return (
    <Box className="container">
      <EntityBreadcrumbs entity={entity.value} title="変更履歴" />

      <PageHeader title={entity.value?.name ?? ""} description="変更履歴">
        <Box width="50px">
          <IconButton
            id="entity_menu"
            onClick={(e) => {
              setEntityAnchorEl(e.currentTarget);
            }}
          >
            <AppsIcon />
          </IconButton>
          <EntityControlMenu
            entityId={entityId}
            anchorElem={entityAnchorEl}
            handleClose={() => setEntityAnchorEl(null)}
            setOpenImportModal={setOpenImportModal}
          />
        </Box>
      </PageHeader>

      {histories.loading ? (
        <Loading />
      ) : (
        <Container>
          <EntityHistoryList
            histories={histories.value?.results ?? []}
            totalPageCount={totalPageCount}
            maxRowCount={ConstEntityHistoryList.MAX_ROW_COUNT}
            page={page}
            changePage={changePage}
          />
        </Container>
      )}

      <EntryImportModal
        openImportModal={openImportModal}
        closeImportModal={() => setOpenImportModal(false)}
      />
    </Box>
  );
};
