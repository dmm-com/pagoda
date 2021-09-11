import React, { useRef, useState } from "react";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import Typography from "@material-ui/core/Typography";
import { Link } from "react-router-dom";
import Button from "@material-ui/core/Button";
import { makeStyles } from "@material-ui/core/styles";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

export function Import({}) {
  const classes = useStyles();
  const [files, setFiles] = useState([]);
  const filesRef = useRef(null);

  const onChange = (event) => {
    setFiles(event.target.files);
  };

  const onSubmit = (event) => {
    // TODO handle files

    console.log(files);
    event.preventDefault();
  };

  return (
    <div className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to="/new-ui/">
          Top
        </Typography>
        <Typography>インポート</Typography>
      </AironeBreadcrumbs>

      <form onSubmit={onSubmit}>
        <div>
          <input type="file" onChange={onChange} ref={filesRef} />

          <Button
            className={classes.button}
            type="submit"
            variant="contained"
            color="secondary"
          >
            保存
          </Button>
        </div>
      </form>
      <Typography>(注：CSV 形式のデータはインポートできません)</Typography>
    </div>
  );
}
