import { Dialog, DialogActions, DialogTitle } from "@material-ui/core";
import Button from "@material-ui/core/Button";
import PropTypes from "prop-types";
import React from "react";

export default function ConfirmableButton({
  variant,
  color,
  className,
  startIcon,
  component,
  to,
  children,
  dialogTitle,
  onClickYes,
}) {
  const [open, setOpen] = React.useState(false);

  const handleOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleConfirmed = (event) => {
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
}

ConfirmableButton.propTypes = {
  dialogTitle: PropTypes.string.isRequired,
  onClickYes: PropTypes.func.isRequired,
};
