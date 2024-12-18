import AppsIcon from "@mui/icons-material/Apps";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import {
  Box,
  Container,
  Grid,
  IconButton,
  ListItem,
  ListItemText,
  TextField,
} from "@mui/material";
import { useSnackbar } from "notistack";
import React, { FC, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";
import { useTypedParams } from "../hooks/useTypedParams";

import { PageHeader } from "components/common/PageHeader";
import { EntityBreadcrumbs } from "components/entity/EntityBreadcrumbs";
import { EntityControlMenu } from "components/entity/EntityControlMenu";
import {
  CopyFormProps,
  CopyForm as DefaultCopyForm,
} from "components/entry/CopyForm";
import { EntryImportModal } from "components/entry/EntryImportModal";
import { aironeApiClient } from "repository/AironeApiClient";

interface Props {
  CopyForm?: FC<CopyFormProps>;
}

export const ListAliasEntryPage: FC<Props> = ({
  CopyForm = DefaultCopyForm,
}) => {
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

  const entries = useAsyncWithThrow(async () => {
    return await aironeApiClient.getEntries(entityId, true, 1, "");
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
          {entries.value?.results.map((entry) => (
            <>
              <Grid
                item
                xs={4}
                //</>sx={{ height: "500px" }}
                display="flex"
                flexDirection="column"
              >
                <>{entry.name}</>
                <TextField size="small"></TextField>
              </Grid>
              <Grid
                item
                xs={8}
                //</>sx={{ height: "500px" }}
              >
                {entry.aliases.map((alias) => (
                  <ListItem
                    key={alias.id}
                    secondaryAction={
                      <IconButton>
                        <DeleteOutlineIcon />
                      </IconButton>
                    }
                  >
                    <ListItemText>{alias.name}</ListItemText>
                  </ListItem>
                ))}
              </Grid>
            </>
          ))}
        </Grid>
      </Container>

      <EntryImportModal
        openImportModal={openImportModal}
        closeImportModal={() => setOpenImportModal(false)}
      />
    </Box>
  );
};
