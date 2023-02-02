import AppsIcon from "@mui/icons-material/Apps";
import LockIcon from "@mui/icons-material/Lock";
import { Box, Container, IconButton, Typography } from "@mui/material";
import React, { FC, useState } from "react";
import { Link } from "react-router-dom";

import { EntityControlMenu } from "../components/entity/EntityControlMenu";
import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";
import { useTypedParams } from "../hooks/useTypedParams";

import { entitiesPath, topPath } from "Routes";
import { aironeApiClientV2 } from "apiclient/AironeApiClientV2";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { PageHeader } from "components/common/PageHeader";
import { EntryImportModal } from "components/entry/EntryImportModal";
import { EntryList } from "components/entry/EntryList";

interface Props {
  canCreateEntry?: boolean;
}

export const EntryListPage: FC<Props> = ({ canCreateEntry = true }) => {
  const { entityId } = useTypedParams<{ entityId: number }>();

  const [entityAnchorEl, setEntityAnchorEl] =
    useState<HTMLButtonElement | null>(null);
  const [openImportModal, setOpenImportModal] = React.useState(false);

  const entity = useAsyncWithThrow(async () => {
    return await aironeApiClientV2.getEntity(entityId);
  });

  return (
    <Box>
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography component={Link} to={entitiesPath()}>
          エンティティ一覧
        </Typography>
        <Box sx={{ display: "flex" }}>
          <Typography color="textPrimary">
            {entity.loading ? "" : entity.value?.name}
          </Typography>
          {!entity.loading && entity.value?.isPublic === false && <LockIcon />}
        </Box>
      </AironeBreadcrumbs>

      <PageHeader title={entity.value?.name ?? ""} description="エントリ一覧">
        <Box width="50px">
          <IconButton
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
