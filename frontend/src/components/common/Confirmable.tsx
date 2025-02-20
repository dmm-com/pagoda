import { Box, Button, Dialog, DialogActions, DialogTitle, DialogContent } from "@mui/material";
import React, { ReactElement, FC, SyntheticEvent, useState } from "react";

interface Props {
  componentGenerator: (handleOpen: () => void) => ReactElement;
  dialogTitle: string;
  onClickYes: (e: SyntheticEvent) => void;
  content?: ReactElement;
}

export const Confirmable: FC<Props> = ({
  componentGenerator,
  dialogTitle,
  onClickYes,
  content,
}) => {
  const [open, setOpen] = useState(false);

  const handleOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleConfirmed = (event: SyntheticEvent) => {
    setOpen(false);
    onClickYes(event);
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
          <>
            {content}
          </>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleConfirmed} color="primary" autoFocus>
            Yes
          </Button>
          <Button onClick={handleClose} color="primary">
            No
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
