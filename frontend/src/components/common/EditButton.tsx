import EditIcon from "@mui/icons-material/Edit";
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

export const EditButton: FC<Props> = ({ to, children }) => {
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
};
