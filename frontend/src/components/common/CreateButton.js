import Button from "@material-ui/core/Button";
import AddIcon from "@material-ui/icons/Add";
import { Link } from "react-router-dom";
import React from "react";
import { makeStyles } from "@material-ui/core/styles";
import PropTypes from "prop-types";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

export default function CreateButton({ to, children }) {
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
