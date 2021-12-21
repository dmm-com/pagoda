import AddIcon from "@mui/icons-material/Add";
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

export function CreateButton({ to, children }) {
  const classes = useStyles();

  return (
    <Button
      variant="contained"
      color="primary"
      className={classes.button}
      startIcon={<AddIcon />}
      component={Link}
      to={to}
    >
      {children}
    </Button>
  );
}

CreateButton.propTypes = {
  to: PropTypes.string.isRequired,
  children: PropTypes.any.isRequired,
};
