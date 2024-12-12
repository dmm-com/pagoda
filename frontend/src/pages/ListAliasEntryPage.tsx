import AppsIcon from "@mui/icons-material/Apps";
import { Box, Container, IconButton, Grid } from "@mui/material";
import { useSnackbar } from "notistack";
import React, { FC, useState } from "react";
import { useNavigate } from "react-router-dom";

import { EntityControlMenu } from "components/entity/EntityControlMenu";
import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";
import { useTypedParams } from "../hooks/useTypedParams";
import { EntryImportModal } from "components/entry/EntryImportModal";

import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { SubmitButton } from "components/common/SubmitButton";
import {
  CopyForm as DefaultCopyForm,
  CopyFormProps,
} from "components/entry/CopyForm";
import { EntryBreadcrumbs } from "components/entry/EntryBreadcrumbs";
import { usePrompt } from "hooks/usePrompt";
import { aironeApiClient } from "repository/AironeApiClient";
import { entityEntriesPath, entryDetailsPath } from "routes/Routes";
import { EntityBreadcrumbs } from "components/entity/EntityBreadcrumbs";

interface Props {
  CopyForm?: FC<CopyFormProps>;
}

export const ListAliasEntryPage: FC<Props> = ({ CopyForm = DefaultCopyForm }) => {
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();

  const [entityAnchorEl, setEntityAnchorEl] =
    useState<HTMLButtonElement | null>(null);
  const [openImportModal, setOpenImportModal] = React.useState(false);

  const { entityId } = useTypedParams<{
    entityId: number;
  }>();

  const entity = useAsyncWithThrow(async () => {
    return await aironeApiClient.getEntity(entityId);
  }, [entityId]);

  // (TODO) get all corresponding aliases of entity

  return (
    <Box>
      <EntityBreadcrumbs entity={entity.value} title="エイリアス設定" />

      <PageHeader title={entity.value?.name ?? ""} description="エイリアス設定">
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
        {/* show all Aliases that are associated with each Items */}
        <Grid container spacing={2}>
          <Grid item xs={4} sx={{ height: "500px" }}>
            <>xs=8</>
          </Grid>
          <Grid item xs={8} sx={{ height: "500px" }}>
            <>xs=4</>
          </Grid>
        </Grid>
      </Container>

      <EntryImportModal
        openImportModal={openImportModal}
        closeImportModal={() => setOpenImportModal(false)}
      />
    </Box>
  );
};