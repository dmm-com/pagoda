import EditIcon from "@mui/icons-material/Edit";
import { Button } from "@mui/material";
import { makeStyles } from "@mui/styles";
import PropTypes from "prop-types";
import React from "react";
import { Link } from "react-router-dom";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

export function EditButton({ to, children }) {
  const classes = useStyles();

  return (
    <Button
      variant="contained"
      color="primary"
      className={classes.button}
      startIcon={<EditIcon />}
      component={Link}
      to={to}
    >
      {children}
    </Button>
  );
}

EditButton.propTypes = {
  to: PropTypes.string.isRequired,
  children: PropTypes.any.isRequired,
};
