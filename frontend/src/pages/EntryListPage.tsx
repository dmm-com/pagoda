import AppsIcon from "@mui/icons-material/Apps";
import { Box, Container, IconButton } from "@mui/material";
import React, { FC, useState } from "react";

import { PageHeader } from "components/common/PageHeader";
import { EntityBreadcrumbs } from "components/entity/EntityBreadcrumbs";
import { EntityControlMenu } from "components/entity/EntityControlMenu";
import { EntryImportModal } from "components/entry/EntryImportModal";
import { EntryList } from "components/entry/EntryList";
import { useAsyncWithThrow } from "hooks/useAsyncWithThrow";
import { usePageTitle } from "hooks/usePageTitle";
import { useTypedParams } from "hooks/useTypedParams";
import { aironeApiClient } from "repository/AironeApiClient";
import { TITLE_TEMPLATES } from "services";

interface Props {
  canCreateEntry?: boolean;
}

export const EntryListPage: FC<Props> = ({ canCreateEntry = true }) => {
  const { entityId } = useTypedParams<{ entityId: number }>();

  const [entityAnchorEl, setEntityAnchorEl] =
    useState<HTMLButtonElement | null>(null);
  const [openImportModal, setOpenImportModal] = React.useState(false);

  const entity = useAsyncWithThrow(async () => {
    return await aironeApiClient.getEntity(entityId);
  });

  usePageTitle(entity.loading ? "読み込み中..." : TITLE_TEMPLATES.entryList, {
    prefix: entity.value?.name,
  });

  return (
    <Box>
      <EntityBreadcrumbs entity={entity.value} />

      <PageHeader
        title={entity.value?.name ?? ""}
        description="アイテム一覧"
        targetId={entity.value?.id}
        hasOngoingProcess={entity.value?.hasOngoingChanges}
      >
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

      <Container>
        <EntryList entityId={entityId} canCreateEntry={canCreateEntry} />
      </Container>
      <EntryImportModal
        openImportModal={openImportModal}
        closeImportModal={() => setOpenImportModal(false)}
      />
    </Box>
  );
};
