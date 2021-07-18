import { makeStyles } from "@material-ui/core/styles";
import React, { useEffect, useState } from "react";
import {
  List,
  ListItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@material-ui/core";
import Typography from "@material-ui/core/Typography";
import { Link } from "react-router-dom";
import Button from "@material-ui/core/Button";
import Paper from "@material-ui/core/Paper";
import AironeBreadcrumbs from "../components/common/AironeBreadcrumbs";
import { getJobs } from "../utils/AironeAPIClient";
import { useAsync } from "react-use";
import JobList from "../components/job/JobList";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
  entityName: {
    margin: theme.spacing(1),
  },
}));

export default function Job({}) {
  const classes = useStyles();

  const jobs = useAsync(async () => getJobs().then((resp) => resp.json()), []);

  return (
    <div className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to="/new-ui/">
          Top
        </Typography>
        <Typography color="textPrimary">ジョブ一覧</Typography>
      </AironeBreadcrumbs>

      <div className="row">
        <div className="col">
          <div className="float-left">
            <Button
              className={classes.button}
              variant="outlined"
              color="primary"
            >
              全件表示
            </Button>
          </div>
          <div className="float-right"></div>
        </div>
      </div>

      {!jobs.loading && <JobList jobs={jobs.value} />}
    </div>
  );
}
