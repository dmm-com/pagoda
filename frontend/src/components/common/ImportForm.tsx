import { Box, Button, Input, Theme, Typography } from "@mui/material";
import { makeStyles } from "@mui/styles";
import { useSnackbar } from "notistack";
import React, { FC, useState } from "react";
import { useHistory } from "react-router-dom";

const useStyles = makeStyles<Theme>((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

interface Props {
  // FIXME describe concrete types
  importFunc: (importData: any) => Promise<any>;
}

export const ImportForm: FC<Props> = ({ importFunc }) => {
  const classes = useStyles();
  const history = useHistory();
  const [file, setFile] = useState<File>();
  const { enqueueSnackbar } = useSnackbar();

  const onChange = (event) => {
    setFile(event.target.files[0]);
  };

  const onClick = async () => {
    if (file) {
      const fileReader = new FileReader();
      fileReader.readAsText(file);

      fileReader.onload = async () => {
        try {
          await importFunc(fileReader.result);
          history.go(0);
        } catch (e) {
          enqueueSnackbar(e, { variant: "error" });
        }
      };
    }
  };

  return (
    <Box>
      <Box>
        <Input type="file" onChange={onChange} />
        <Button
          className={classes.button}
          type="submit"
          variant="contained"
          color="secondary"
          onClick={onClick}
        >
          保存
        </Button>
      </Box>
      <Typography>(注：CSV 形式のデータはインポートできません)</Typography>
    </Box>
  );
};
