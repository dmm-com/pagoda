import AppsIcon from "@mui/icons-material/Apps";
import { Box, Container, IconButton } from "@mui/material";
import React, { FC, useState } from "react";

import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { EntityBreadcrumbs } from "components/entity/EntityBreadcrumbs";
import { EntityControlMenu } from "components/entity/EntityControlMenu";
import { EntityHistoryList } from "components/entity/EntityHistoryList";
import { EntryImportModal } from "components/entry/EntryImportModal";
import { useAsyncWithThrow } from "hooks/useAsyncWithThrow";
import { usePage } from "hooks/usePage";
import { useTypedParams } from "hooks/useTypedParams";
import { aironeApiClient } from "repository/AironeApiClient";

export const EntityHistoryPage: FC = () => {
  const { entityId } = useTypedParams<{ entityId: number }>();

  const [page, changePage] = usePage();

  const [entityAnchorEl, setEntityAnchorEl] =
    useState<HTMLButtonElement | null>(null);
  const [openImportModal, setOpenImportModal] = React.useState(false);

  const entity = useAsyncWithThrow(async () => {
    return await aironeApiClient.getEntity(entityId);
  }, [entityId]);
  const histories = useAsyncWithThrow(async () => {
    return await aironeApiClient.getEntityHistories(entityId, page);
  }, [entityId, page]);

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

      {histories.loading || !histories.value ? (
        <Loading />
      ) : (
        <Container>
          <EntityHistoryList
            histories={histories.value}
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
