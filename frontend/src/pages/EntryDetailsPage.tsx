import AppsIcon from "@mui/icons-material/Apps";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import {
  Box,
  Button,
  Chip,
  Container,
  Dialog,
  DialogContent,
  DialogTitle,
  Grid,
  IconButton,
  Stack,
  Theme,
  Typography,
} from "@mui/material";
import { makeStyles } from "@mui/styles";
import { ErrorBoundary } from "react-error-boundary";
import React, { FC, useState } from "react";
import { Link } from "react-router-dom";
import { Element, scroller } from "react-scroll";
import { useAsync } from "react-use";

import { useTypedParams } from "../hooks/useTypedParams";

import { entitiesPath, entityEntriesPath, topPath } from "Routes";
import { aironeApiClientV2 } from "apiclient/AironeApiClientV2";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { EntryAttributes } from "components/entry/EntryAttributes";
import { EntryControlMenu } from "components/entry/EntryControlMenu";
import { EntryReferral } from "components/entry/EntryReferral";


const useStyles = makeStyles<Theme>((theme) => ({
  errorDescription: {
    marginTop: theme.spacing(2),
    marginBottom: theme.spacing(2),
  },
  errorDetails: {
    marginTop: theme.spacing(1),
    marginBottom: theme.spacing(1),
  },
  buttons: {
    marginTop: theme.spacing(2),
    marginBottom: theme.spacing(2),
    display: "flex",
    justifyContent: "flex-end",
  },
}));

interface Props {
  error: Error;
}

const ErrorFallbackHoge: FC<Props> = ({ error }) => {
  console.log('[onix/ErrorFallbackHoge(00)]');
  const classes = useStyles();
  const [open, setOpen] = useState(true);

  const handleClickGoToTop = () => {
    location.href = topPath();
  };

  return (
    <Dialog open={open} onClose={() => setOpen(false)}>
      <DialogTitle>ABCD</DialogTitle>
      <DialogContent>
        <Box className={classes.errorDescription}>
          <Typography>
            不明なエラーが発生しました。トップページに戻って操作し直してください(Hoge)
          </Typography>
          <Typography>
            エラーが繰り返し発生する場合は管理者にお問い合わせください
          </Typography>
        </Box>
        <Box className={classes.errorDetails}>
          <Typography variant="body2">
            エラー詳細: {error.toString()}
          </Typography>
        </Box>
        <Box className={classes.buttons}>
          <Button
            variant="outlined"
            color="secondary"
            onClick={handleClickGoToTop}
          >
            トップページに戻る
          </Button>
        </Box>
      </DialogContent>
    </Dialog>
  );
};

const ErrorHandlerHoge: FC = ({ children }) => {
  console.log('[onix/ErrorHandlerHoge(00)]');
  return (
    <ErrorBoundary FallbackComponent={ErrorFallbackHoge}>{children}</ErrorBoundary>
  );
};

export const EntryDetailsPage: FC = () => {
  const { entityId, entryId } =
    useTypedParams<{ entityId: number; entryId: number }>();

  const [entryAnchorEl, setEntryAnchorEl] =
    useState<HTMLButtonElement | null>();

  const entry = useAsync(async () => {
    return await aironeApiClientV2.getEntry(entryId);
  }, [entryId]);

  return (
    <ErrorHandlerHoge>
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
    </ErrorHandlerHoge>
  );
};
