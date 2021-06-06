import Button from "@material-ui/core/Button";
import {Dialog, DialogActions, DialogTitle, TableCell} from "@material-ui/core";
import React from "react";
import PropTypes from "prop-types";

export default function ConfirmableButton(props) {
    const [open, setOpen] = React.useState(false);

    const handleOpen = () => {
        setOpen(true);
    };

    const handleClose = () => {
        setOpen(false);
    };

    const handleConfirmed = (event) => {
        setOpen(false);
        props.onClickYes(event);
    };

    return (
        <div>
            <Button onClick={handleOpen} {...props} />
            <Dialog
                open={open}
                onClose={handleClose}
                aria-labelledby="alert-dialog-title"
                aria-describedby="alert-dialog-description"
            >
                <DialogTitle id="alert-dialog-title">{props.dialogTitle}</DialogTitle>
                <DialogActions>
                    <Button onClick={handleClose} color="primary">
                        No
                    </Button>
                    <Button onClick={handleConfirmed} color="primary" autoFocus>
                        Yes
                    </Button>
                </DialogActions>
            </Dialog>
        </div>
    );
}

ConfirmableButton.propTypes = {
    dialogTitle: PropTypes.string.isRequired,
    onClickYes: PropTypes.func.isRequired,
};
