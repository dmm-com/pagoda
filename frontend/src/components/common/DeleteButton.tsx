import DeleteIcon from "@mui/icons-material/Delete";
import { Theme } from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC, ReactElement, SyntheticEvent } from "react";

import { ConfirmableButton } from "./ConfirmableButton";

const useStyles = makeStyles<Theme>((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

interface Props {
  handleDelete: (e: SyntheticEvent) => void;
  startIcon?: ReactElement;
}

export const DeleteButton: FC<Props> = ({
  handleDelete,
  children,
  startIcon,
}) => {
  const classes = useStyles();

  return (
    <ConfirmableButton
      variant="contained"
      color="secondary"
      className={classes.button}
      startIcon={startIcon ?? <DeleteIcon />}
      dialogTitle="本当に削除しますか？"
      onClickYes={handleDelete}
    >
      {children ?? "'"}
    </ConfirmableButton>
  );
};
