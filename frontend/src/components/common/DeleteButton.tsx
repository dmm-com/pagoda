import { makeStyles } from "@material-ui/core/styles";
import DeleteIcon from "@material-ui/icons/Delete";
import React, { FC, ReactElement } from "react";

import { ConfirmableButton } from "./ConfirmableButton";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

interface Props {
  handleDelete: (e: any) => void;
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
