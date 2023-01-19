import {
  Box,
  Button,
  Dialog,
  DialogContent,
  DialogTitle,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useCallback, useEffect, useState } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { useError } from "react-use";

import { ForbiddenErrorPage } from "./pages/ForbiddenErrorPage";
import { NotFoundErrorPage } from "./pages/NotFoundErrorPage";
import { ForbiddenError, NotFoundError } from "./utils/Exceptions";
import { toError } from "./utils/ResponseUtil";

import { topPath } from "Routes";

const ErrorDescription = styled(Box)(({ theme }) => ({
  marginTop: theme.spacing(2),
  marginBottom: theme.spacing(2),
}));

const ErrorDetails = styled(Box)(({ theme }) => ({
  marginTop: theme.spacing(1),
  marginBottom: theme.spacing(1),
}));

const Buttons = styled(Box)(({ theme }) => ({
  marginTop: theme.spacing(2),
  marginBottom: theme.spacing(2),
  display: "flex",
  justifyContent: "flex-end",
}));

interface GenericErrorProps {
  children: string;
}

interface Props {
  error: Error;
}

const GenericError: FC<GenericErrorProps> = ({ children }) => {
  const [open, setOpen] = useState(true);

  const handleClickGoToTop = () => {
    location.href = topPath();
  };

  return (
    <Dialog open={open} onClose={() => setOpen(false)}>
      <DialogTitle>エラーが発生しました</DialogTitle>
      <DialogContent>
        <ErrorDescription>
          <Typography>
            不明なエラーが発生しました。トップページに戻って操作し直してください
          </Typography>
          <Typography>
            エラーが繰り返し発生する場合は管理者にお問い合わせください
          </Typography>
        </ErrorDescription>
        <ErrorDetails>
          <Typography variant="body2">エラー詳細: {children}</Typography>
        </ErrorDetails>
        <Buttons>
          <Button
            variant="outlined"
            color="secondary"
            onClick={handleClickGoToTop}
          >
            トップページに戻る
          </Button>
        </Buttons>
      </DialogContent>
    </Dialog>
  );
};

const ErrorFallback: FC<Props> = ({ error }) => {
  switch (error.name) {
    case ForbiddenError.errorName:
      return <ForbiddenErrorPage />;
    case NotFoundError.errorName:
      return <NotFoundErrorPage />;
    default:
      return <GenericError>{error.toString()}</GenericError>;
  }
};

const ErrorBridge: FC<{ children: React.ReactNode }> = ({ children }) => {
  const dispatchError = useError();

  const handleUnhandledRejection = useCallback(
    (event: PromiseRejectionEvent) => {
      if (event.reason instanceof Response) {
        const httpError = toError(event.reason);
        if (httpError != null) {
          dispatchError(httpError);
        }
      }
      dispatchError(event.reason);
    },
    []
  );

  useEffect(() => {
    window.addEventListener("unhandledrejection", handleUnhandledRejection);
    return () => {
      window.removeEventListener(
        "unhandledrejection",
        handleUnhandledRejection
      );
    };
  }, [handleUnhandledRejection]);

  return <>{children}</>;
};

export const ErrorHandler: FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <ErrorBridge>{children}</ErrorBridge>
    </ErrorBoundary>
  );
};
