import { makeStyles } from "@material-ui/core/styles";
import React, { useState } from "react";
import Button from "@material-ui/core/Button";
import PropTypes from "prop-types";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

export default function WebhookForm({
}) {
  const classes = useStyles();

  return (
    <div>
      <Button
        className={classes.button}
        type="submit"
        variant="contained"
        color="secondary"
      >
        Add Webhook
      </Button>
    </div>
  );
}
