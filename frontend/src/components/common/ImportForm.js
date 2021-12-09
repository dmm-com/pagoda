import { Box } from "@material-ui/core";
import Button from "@material-ui/core/Button";
import Typography from "@material-ui/core/Typography";
import { makeStyles } from "@material-ui/core/styles";
import { Input } from "@material-ui/icons";
import PropTypes from "prop-types";
import React, { useState } from "react";
import { useHistory } from "react-router-dom";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

export function ImportForm({ importFunc, redirectPath }) {
  const classes = useStyles();
  const history = useHistory();
  const [file, setFile] = useState([]);

  const onChange = (event) => {
    setFile(event.target.files[0]);
  };

  const onSubmit = (event) => {
    if (file) {
      const formData = new FormData();
      formData.append("file", file);

      importFunc(formData).then(() => history.push(redirectPath));
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
}

ImportForm.propTypes = {
  importFunc: PropTypes.func.isRequired,
  redirectPath: PropTypes.string.isRequired,
};
