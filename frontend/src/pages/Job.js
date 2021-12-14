import { Box } from "@material-ui/core";
import Button from "@material-ui/core/Button";
import Typography from "@material-ui/core/Typography";
import { makeStyles } from "@material-ui/core/styles";
import React from "react";
import { Link } from "react-router-dom";
import { useAsync } from "react-use";

import { topPath } from "../Routes";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import { JobList } from "../components/job/JobList";
import { getJobs } from "../utils/AironeAPIClient";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
  entityName: {
    margin: theme.spacing(1),
  },
}));

export function Job({}) {
  const classes = useStyles();

  const jobs = useAsync(async () => {
    const resp = await getJobs();
    return await resp.json();
  }, []);

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">ジョブ一覧</Typography>
      </AironeBreadcrumbs>

      <Box className="row">
        <Box className="col">
          <Box className="float-left">
            <Button
              className={classes.button}
              variant="outlined"
              color="primary"
            >
              全件表示
            </Button>
          </Box>
          <Box className="float-right"></Box>
        </Box>
      </Box>

      {!jobs.loading && <JobList jobs={jobs.value} />}
    </Box>
  );
}
