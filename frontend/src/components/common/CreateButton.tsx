import AddIcon from "@mui/icons-material/Add";
import { Button, Theme } from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC } from "react";
import { Link } from "react-router-dom";

const useStyles = makeStyles<Theme>((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

interface Props {
  to: string;
}

export const CreateButton: FC<Props> = ({ to, children }) => {
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
};
