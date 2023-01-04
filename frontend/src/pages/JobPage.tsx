import ReplayIcon from "@mui/icons-material/Replay";
import {
  Box,
  Button,
  Container,
  Divider,
  Pagination,
  Stack,
  Typography,
} from "@mui/material";
import React, { FC, useMemo } from "react";
import { Link } from "react-router-dom";
import { useAsync, useToggle } from "react-use";

import { aironeApiClientV2 } from "../apiclient/AironeApiClientV2";
import { usePage } from "../hooks/usePage";
import { JobList as ConstJobList } from "../utils/Constants";

import { topPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { JobList } from "components/job/JobList";

export const JobPage: FC = () => {
  const [page, changePage] = usePage();

  const [refresh, toggleRefresh] = useToggle(false);

  const jobs = useAsync(async () => {
    return await aironeApiClientV2.getJobs(page);
  }, [page, refresh]);

  const maxPage = useMemo(() => {
    if (jobs.loading) {
      return 0;
    }
    return Math.ceil(jobs.value.count / ConstJobList.MAX_ROW_COUNT);
  }, [jobs.loading, jobs.value?.count]);

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">ジョブ一覧</Typography>
      </AironeBreadcrumbs>

      <Container maxWidth="lg" sx={{ marginTop: "111px" }}>
        <Box mb="64px">
          <Typography variant="h2" align="center">
            ジョブ一覧
          </Typography>
        </Box>
      </Container>

      <Divider />

      <Box
        sx={{
          marginTop: "111px",
          paddingLeft: "10%",
          paddingRight: "10%",
          marginBottom: "10%",
        }}
      >
        <Box my="12px" display="flex" justifyContent="flex-end">
          <Button
            variant="outlined"
            color="success"
            onClick={() => toggleRefresh()}
          >
            <ReplayIcon /> ジョブ一覧を更新
          </Button>
        </Box>

        {jobs.loading ? <Loading /> : <JobList jobs={jobs.value.results} />}
        <Box display="flex" justifyContent="center" my="30px">
          <Stack spacing={2}>
            <Pagination
              count={maxPage}
              page={page}
              onChange={(e, page) => changePage(page)}
              color="primary"
            />
          </Stack>
        </Box>
      </Box>
    </Box>
  );
};
