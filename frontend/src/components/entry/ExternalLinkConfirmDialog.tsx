import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
} from "@mui/material";
import { FC, ReactNode, useState } from "react";

import { useTranslation } from "hooks/useTranslation";

interface Props {
  url: string;
  children: ReactNode;
}

export const ExternalLinkConfirmDialog: FC<Props> = ({ url, children }) => {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);

  return (
    <>
      <Box
        component="button"
        type="button"
        onClick={() => setOpen(true)}
        sx={{
          all: "unset",
          color: "primary.main",
          cursor: "pointer",
          textDecoration: "underline",
        }}
      >
        {children}
      </Box>
      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>{t("entry.externalLink.confirmTitle")}</DialogTitle>
        <DialogContent>
          <Box sx={{ wordBreak: "break-all" }}>{url}</Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)} color="primary">
            Cancel
          </Button>
          <Button
            onClick={() => {
              window.open(url, "_blank", "noopener,noreferrer");
              setOpen(false);
            }}
            color="primary"
            autoFocus
          >
            Open
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};
