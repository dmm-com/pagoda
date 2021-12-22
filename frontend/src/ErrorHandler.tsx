import {
  Box,
  Button,
  Dialog,
  DialogContent,
  DialogTitle,
  Theme,
  Typography,
} from "@mui/material";
import { makeStyles } from "@mui/styles";
import PropTypes from "prop-types";
import React, { FC, useState } from "react";
import { ErrorBoundary } from "react-error-boundary";

import { topPath } from "./Routes";

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

const ErrorFallback: FC<Props> = ({ error }) => {
  const classes = useStyles();
  const [open, setOpen] = useState(true);

  const handleClickGoToTop = () => {
    location.href = topPath();
  };

  return (
    <Dialog open={open} onClose={() => setOpen(false)}>
      <DialogTitle>エラーが発生しました</DialogTitle>
      <DialogContent>
        <Box className={classes.errorDescription}>
          <Typography>
            不明なエラーが発生しました。トップページに戻って操作し直してください
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

export const ErrorHandler: FC = ({ children }) => {
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>{children}</ErrorBoundary>
  );
};

ErrorHandler.propTypes = {
  children: PropTypes.any.isRequired,
};
