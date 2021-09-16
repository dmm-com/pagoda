import React from "react";
import { makeStyles } from "@material-ui/core/styles";
import PropTypes from "prop-types";
import ConfirmableButton from "./ConfirmableButton";
import DeleteIcon from "@material-ui/icons/Delete";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

export default function DeleteButton({ handleDelete, children }) {
  const classes = useStyles();

  return (
    <ConfirmableButton
      variant="contained"
      color="secondary"
      className={classes.button}
      startIcon={<DeleteIcon />}
      dialogTitle="本当に削除しますか？"
      onClickYes={handleDelete}
    >
      {children}
    </ConfirmableButton>
  );
}

DeleteButton.propTypes = {
  handleDelete: PropTypes.func.isRequired,
  children: PropTypes.any.isRequired,
};
