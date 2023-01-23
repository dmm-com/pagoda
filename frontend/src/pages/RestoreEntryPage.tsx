import AppsIcon from "@mui/icons-material/Apps";
import { Box, Container, IconButton, Typography } from "@mui/material";
import React, { FC, useState } from "react";
import { Link } from "react-router-dom";
import { useAsync } from "react-use";

import { EntityControlMenu } from "../components/entity/EntityControlMenu";
import { EntryImportModal } from "../components/entry/EntryImportModal";
import { RestorableEntryList } from "../components/entry/RestorableEntryList";
import { useTypedParams } from "../hooks/useTypedParams";

import { entitiesPath, entityEntriesPath, topPath } from "Routes";
import { aironeApiClientV2 } from "apiclient/AironeApiClientV2";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";

export const RestoreEntryPage: FC = () => {
  const { entityId } = useTypedParams<{ entityId: number }>();

  const params = new URLSearchParams(location.search);
  const keyword = params.get("keyword");

  const [entityAnchorEl, setEntityAnchorEl] =
    useState<HTMLButtonElement | null>(null);
  const [openImportModal, setOpenImportModal] = React.useState(false);

  const entity = useAsync(async () => {
    return await aironeApiClientV2.getEntity(entityId);
  });

  if (entity.loading) {
    return <Loading />;
  }

  return (
    <Box>
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography component={Link} to={entitiesPath()}>
          エンティティ一覧
        </Typography>
        <Typography
          component={Link}
          to={entityEntriesPath(entity.value?.id ?? 0)}
        >
          {entity.value?.name} エントリ一覧
        </Typography>
        <Typography>{entity.value?.name} 削除エントリの復旧</Typography>
      </AironeBreadcrumbs>

      <Container maxWidth="lg" sx={{ marginTop: "111px" }}>
        {/* NOTE: This Box component that has CSS tuning should be custom component */}
        <Box
          display="flex"
          sx={{ borderBottom: 1, borderColor: "gray", mb: "64px", pb: "64px" }}
        >
          <Box width="50px" />
          <Box flexGrow="1">
            {!entity.loading && (
              <Typography variant="h2" align="center">
                {entity.value?.name}
              </Typography>
            )}
            <Typography variant="h4" align="center">
              削除エントリの復旧
            </Typography>
          </Box>
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
            <EntryImportModal
              openImportModal={openImportModal}
              closeImportModal={() => setOpenImportModal(false)}
            />
          </Box>
        </Box>

        <RestorableEntryList entityId={entityId} initialKeyword={keyword} />
      </Container>
    </Box>
  );
};
