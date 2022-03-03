import AppsIcon from "@mui/icons-material/Apps";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import {
  Box,
  Chip,
  Container,
  Grid,
  IconButton,
  Stack,
  Typography,
} from "@mui/material";
import React, { FC, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Element, scroller } from "react-scroll";
import { useAsync } from "react-use";

import { entitiesPath, entityEntriesPath, topPath } from "Routes";
import { aironeApiClientV2 } from "apiclient/AironeApiClientV2";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { EntryAttributes } from "components/entry/EntryAttributes";
import { EntryControlMenu } from "components/entry/EntryControlMenu";
import { EntryReferral } from "components/entry/EntryReferral";

export const EntryDetailsPage: FC = () => {
  const { entityId } = useParams<{ entityId: number }>();
  const { entryId } = useParams<{ entryId: number }>();

  const [entryAnchorEl, setEntryAnchorEl] =
    useState<HTMLButtonElement | null>();

  const entry = useAsync(async () => {
    return await aironeApiClientV2.getEntry(entryId);
  }, [entryId]);

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
          <Box flexGrow="1">
            {!entry.loading && (
              <Typography variant="h2" align="center">
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
