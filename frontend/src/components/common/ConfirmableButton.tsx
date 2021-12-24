import {
  Button,
  ButtonProps,
  Dialog,
  DialogActions,
  DialogTitle,
} from "@mui/material";
import React, { ElementType, FC, SyntheticEvent } from "react";

interface Props extends ButtonProps {
  component?: ElementType;
  to?: string;
  dialogTitle: string;
  onClickYes: (e: SyntheticEvent) => void;
}

export const ConfirmableButton: FC<Props> = ({
  variant,
  color,
  className,
  startIcon,
  component,
  to,
  children,
  dialogTitle,
  onClickYes,
}) => {
  const [open, setOpen] = React.useState(false);

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
    <span>
      <Button
        variant={variant}
        color={color}
        className={className}
        startIcon={startIcon}
        component={component}
        to={to}
        onClick={handleOpen}
      >
        {children}
      </Button>
      <Dialog
        open={open}
        onClose={handleClose}
        aria-labelledby="alert-dialog-title"
        aria-describedby="alert-dialog-description"
      >
        <DialogTitle id="alert-dialog-title">{dialogTitle}</DialogTitle>
        <DialogActions>
          <Button onClick={handleClose} color="primary">
            No
          </Button>
          <Button onClick={handleConfirmed} color="primary" autoFocus>
            Yes
          </Button>
        </DialogActions>
      </Dialog>
    </span>
  );
};
