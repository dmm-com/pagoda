import AppsIcon from "@mui/icons-material/Apps";
import { Box, Container, IconButton, Typography } from "@mui/material";
import React, { FC, useState } from "react";
import { Link } from "react-router-dom";
import { useAsync } from "react-use";

import { EntityControlMenu } from "../components/entity/EntityControlMenu";
import { useTypedParams } from "../hooks/useTypedParams";

import { entitiesPath, topPath } from "Routes";
import { aironeApiClientV2 } from "apiclient/AironeApiClientV2";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { EntryList } from "components/entry/EntryList";

interface Props {
  canCreateEntry?: boolean;
}

export const EntryListPage: FC<Props> = ({ canCreateEntry = true }) => {
  const { entityId } = useTypedParams<{ entityId: number }>();

  const [entityAnchorEl, setEntityAnchorEl] =
    useState<HTMLButtonElement | null>();

  const entity = useAsync(async () => {
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
        <Typography color="textPrimary">
          {entity.loading ? "" : entity.value.name}
        </Typography>
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
                {entity.value.name}
              </Typography>
            )}
            <Typography variant="h4" align="center">
              エントリ一覧
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
            />
          </Box>
        </Box>

        {/* This describes all Entries in the rest of this page*/}
        <EntryList entityId={entityId} canCreateEntry={canCreateEntry} />
      </Container>
    </Box>
  );
};
