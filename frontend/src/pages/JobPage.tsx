import { Box, Button, Theme, Typography } from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC } from "react";
import { Link } from "react-router-dom";
import { useAsync } from "react-use";

import { aironeApiClientV2 } from "../apiclient/AironeApiClientV2";

import { topPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { JobList } from "components/job/JobList";

const useStyles = makeStyles<Theme>((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
  entityName: {
    margin: theme.spacing(1),
  },
}));

export const JobPage: FC = () => {
  const classes = useStyles();

  const jobs = useAsync(async () => {
    return aironeApiClientV2.getJobs();
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

      {jobs.loading ? <Loading /> : <JobList jobs={jobs.value} />}
    </Box>
  );
};
