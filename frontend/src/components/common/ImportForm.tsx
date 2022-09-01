import { Box, Button, Input, Theme, Typography } from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC, useState } from "react";
import { useHistory } from "react-router-dom";

const useStyles = makeStyles<Theme>((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

interface Props {
  importFunc: (formData: FormData) => Promise<any>;
  redirectPath: string;
}

export const ImportForm: FC<Props> = ({ importFunc, redirectPath }) => {
  const classes = useStyles();
  const history = useHistory();
  const [file, setFile] = useState<string>();

  const onChange = (event) => {
    setFile(event.target.files[0]);
  };

  const onSubmit = async (event) => {
    console.log('[onix/ImportForm.onSubmit(00)] file: ', file);
    if (file) {
      const formData = new FormData();
      formData.append("file", file);

      await importFunc(formData);
      // history.push(redirectPath);
    }

    event.preventDefault();
  };

  return (
    <Box>
      <form onSubmit={onSubmit}>
        <Box>
          <Input type="file" onChange={onChange} />
          <Button
            className={classes.button}
            type="submit"
            variant="contained"
            color="secondary"
          >
            保存
          </Button>
        </Box>
      </form>
      <Typography>(注：CSV 形式のデータはインポートできません)</Typography>
    </Box>
  );
};
