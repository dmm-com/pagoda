import { makeStyles } from "@material-ui/core/styles";
import DeleteIcon from "@material-ui/icons/Delete";
import PropTypes from "prop-types";
import React from "react";

import { ConfirmableButton } from "./ConfirmableButton";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

export function DeleteButton({
  handleDelete,
  children,
  startIcon = <DeleteIcon />,
}) {
  const classes = useStyles();

  return (
    <ConfirmableButton
      variant="contained"
      color="secondary"
      className={classes.button}
      startIcon={startIcon}
      dialogTitle="本当に削除しますか？"
      onClickYes={handleDelete}
    >
      {children}
    </ConfirmableButton>
  );
}

DeleteButton.propTypes = {
  handleDelete: PropTypes.func.isRequired,
  startIcon: PropTypes.element,
  children: PropTypes.any.isRequired,
};
