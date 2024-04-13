import AppsIcon from "@mui/icons-material/Apps";
import { Box, Container, IconButton } from "@mui/material";
import React, { FC, useState } from "react";

import { EntityControlMenu } from "../components/entity/EntityControlMenu";
import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";
import { useTypedParams } from "../hooks/useTypedParams";

import { PageHeader } from "components/common/PageHeader";
import { EntityBreadcrumbs } from "components/entity/EntityBreadcrumbs";
import { EntryImportModal } from "components/entry/EntryImportModal";
import { EntryList } from "components/entry/EntryList";
import { aironeApiClient } from "repository/AironeApiClient";

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

  return (
    <Box>
      <EntityBreadcrumbs entity={entity.value} />

      <PageHeader title={entity.value?.name ?? ""} description="エントリ一覧" hasOngoingProcess={entity.value?.hasOngoingChanges}>
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
