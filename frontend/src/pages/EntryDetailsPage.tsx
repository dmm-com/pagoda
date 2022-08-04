import AppsIcon from "@mui/icons-material/Apps";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import {
  Box,
  Chip,
  Container,
  Grid,
  IconButton,
  Stack,
  Theme,
  Typography,
} from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC, useState } from "react";
import { Link, useHistory } from "react-router-dom";
import { Element, scroller } from "react-scroll";
import { useAsync } from "react-use";

import { useTypedParams } from "../hooks/useTypedParams";

import {
  entitiesPath,
  entityEntriesPath,
  entryDetailsPath,
  restoreEntryPath,
  topPath,
} from "Routes";
import { aironeApiClientV2 } from "apiclient/AironeApiClientV2";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { EntryAttributes } from "components/entry/EntryAttributes";
import { EntryControlMenu } from "components/entry/EntryControlMenu";
import { EntryReferral } from "components/entry/EntryReferral";
import { FailedToGetEntry } from "utils/Exceptions";

const useStyles = makeStyles<Theme>((theme) => ({
  title: {
    height: "72px",
    maxWidth: "700px",
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
}));

export const EntryDetailsPage: FC = () => {
  const classes = useStyles();

  const { entityId, entryId } =
    useTypedParams<{ entityId: number; entryId: number }>();
  const history = useHistory();

  const [entryAnchorEl, setEntryAnchorEl] =
    useState<HTMLButtonElement | null>();

  const entry = useAsync(async () => {
    return await aironeApiClientV2.getEntry(entryId);
  }, [entryId]);

  if (!entry.loading && entry.error) {
    throw new FailedToGetEntry(
      "Failed to get Entry from AirOne APIv2 endpoint"
    );
  }

  // When user specifies invalid entityId, redirect to the page that is correct entityId
  if (!entry.loading && entry.value.schema.id != entityId) {
    history.replace(entryDetailsPath(entry.value.schema.id, entryId));
  }

  // If it'd been deleted, show restore-entry page instead
  if (!entry.loading && !entry.value.isActive) {
    history.replace(restoreEntryPath(entry.value.schema.id, entry.value.name));
  }

  return (
    <Box display="flex" flexDirection="column" flexGrow="1">
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography component={Link} to={entitiesPath()}>
          エンティティ一覧
        </Typography>
        {!entry.loading && (
          <Typography
            component={Link}
            to={entityEntriesPath(entry.value.schema.id)}
          >
            {entry.value.schema.name}
          </Typography>
        )}
        {!entry.loading && (
          <Typography color="textPrimary">{entry.value.name}</Typography>
        )}
      </AironeBreadcrumbs>

      <Container maxWidth="lg" sx={{ pt: "112px" }}>
        <Box display="flex">
          <Box width="50px" />
          <Box
            flexGrow="1"
            display="flex"
            flexDirection="column"
            alignItems="center"
          >
            {!entry.loading && (
              <Typography variant="h2" align="center" className={classes.title}>
                {entry.value.name}
              </Typography>
            )}
            <Typography variant="h4" align="center">
              エントリ詳細
            </Typography>
          </Box>
          <Box width="50px">
            <IconButton
              onClick={(e) => {
                setEntryAnchorEl(e.currentTarget);
              }}
            >
              <AppsIcon />
            </IconButton>
            <EntryControlMenu
              entityId={entityId}
              entryId={entryId}
              anchorElem={entryAnchorEl}
              handleClose={() => setEntryAnchorEl(null)}
            />
          </Box>
        </Box>
      </Container>
      <Stack
        direction="row"
        spacing={1}
        sx={{ justifyContent: "center", pt: "16px", pb: "64px" }}
      >
        <Chip
          icon={<ArrowDropDownIcon />}
          label="項目一覧"
          clickable={true}
          variant="outlined"
          onClick={() => scroller.scrollTo("attr_list", { smooth: true })}
          sx={{
            flexDirection: "row-reverse",
            "& span": {
              pr: "0px",
            },
            "& svg": {
              pr: "8px",
            },
          }}
        />
      </Stack>

      <Grid
        container
        flexGrow="1"
        columns={6}
        sx={{ borderTop: 1, borderColor: "#0000008A" }}
      >
        <Grid
          item
          xs={1}
          sx={{
            py: "64px",
            borderRight: 1,
            borderColor: "#0000008A",
          }}
        >
          <EntryReferral entityId={entityId} entryId={entryId} />
        </Grid>
        <Grid item xs={4}>
          <Box p="32px">
            <Element name="attr_list" />
            <Typography p="32px" fontSize="32px" align="center">
              項目一覧
            </Typography>
            {entry.loading ? (
              <Loading />
            ) : (
              <EntryAttributes attributes={entry.value.attrs} />
            )}
          </Box>
        </Grid>
        <Grid item xs={1} />
      </Grid>
    </Box>
  );
};
