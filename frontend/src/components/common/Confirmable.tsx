import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogTitle,
  DialogContent,
} from "@mui/material";
import { ReactElement, FC, SyntheticEvent, useState } from "react";

interface Props {
  componentGenerator: (handleOpen: () => void) => ReactElement;
  dialogTitle: string;
  onClickYes: (e: SyntheticEvent) => void | Promise<void>;
  content?: ReactElement;
}

export const Confirmable: FC<Props> = ({
  componentGenerator,
  dialogTitle,
  onClickYes,
  content,
}) => {
  const [open, setOpen] = useState(false);
  const [processing, setProcessing] = useState(false);

  const handleOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    if (processing) return;
    setOpen(false);
  };

  const handleConfirmed = async (event: SyntheticEvent) => {
    if (processing) return;
    setProcessing(true);
    try {
      await onClickYes(event);
    } finally {
      setProcessing(false);
      setOpen(false);
    }
  };

  return (
    <Box>
      {componentGenerator(handleOpen)}
      <Dialog
        open={open}
        onClose={handleClose}
        aria-labelledby="alert-dialog-title"
        aria-describedby="alert-dialog-description"
      >
        <DialogTitle id="alert-dialog-title">{dialogTitle}</DialogTitle>
        <DialogContent>
          <>{content}</>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={handleConfirmed}
            color="primary"
            autoFocus
            disabled={processing}
          >
            Yes
          </Button>
          <Button onClick={handleClose} color="primary" disabled={processing}>
            No
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
