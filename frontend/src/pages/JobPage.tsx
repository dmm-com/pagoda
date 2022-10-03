import ReplayIcon from "@mui/icons-material/Replay";
import {
  Box,
  Button,
  Container,
  Divider,
  Pagination,
  Stack,
  Theme,
  Typography,
} from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC, useMemo, useState } from "react";
import { Link, useHistory } from "react-router-dom";
import { useAsync, useToggle } from "react-use";

import { aironeApiClientV2 } from "../apiclient/AironeApiClientV2";
import { JobList as ConstJobList } from "../utils/Constants";

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
  const history = useHistory();

  const params = new URLSearchParams(location.search);
  const [page, setPage] = useState<number>(
    params.has("page") ? Number(params.get("page")) : 1
  );
  const [refresh, toggleRefresh] = useToggle(false);

  const jobs = useAsync(async () => {
    return await aironeApiClientV2.getJobs(page);
  }, [page, refresh]);

  const handleChangePage = (newPage: number) => {
    setPage(newPage);

    history.push({
      pathname: location.pathname,
      search: `?page=${newPage}`,
    });
  };

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
              onChange={(e, page) => handleChangePage(page)}
              color="primary"
            />
          </Stack>
        </Box>
      </Box>
    </Box>
  );
};
