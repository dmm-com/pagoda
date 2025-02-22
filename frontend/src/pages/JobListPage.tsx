import ReplayIcon from "@mui/icons-material/Replay";
import { Box, Button, Container, Typography } from "@mui/material";
import React, { FC, useMemo } from "react";
import { useLocation } from "react-router";
import { useToggle } from "react-use";

import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";

import { AironeLink } from "components";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { PaginationFooter } from "components/common/PaginationFooter";
import { JobList } from "components/job/JobList";
import { usePage } from "hooks/usePage";
import { aironeApiClient } from "repository/AironeApiClient";
import { topPath } from "routes/Routes";
import { JobListParam } from "services/Constants";

export const JobListPage: FC = () => {
  const location = useLocation();

  const [page, changePage] = usePage();
  const [refresh, toggleRefresh] = useToggle(false);

  const { targetId } = useMemo(() => {
    const params = new URLSearchParams(location.search);
    const targetId = params.get("target_id");
    return {
      targetId: targetId ? Number(targetId) : undefined,
    };
  }, [location.search]);

  const jobs = useAsyncWithThrow(async () => {
    return await aironeApiClient.getJobs(page, targetId);
  }, [page, targetId, refresh]);

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={AironeLink} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">ジョブ一覧</Typography>
      </AironeBreadcrumbs>

      <PageHeader title="ジョブ一覧">
        <Button
          variant="outlined"
          color="success"
          onClick={() => toggleRefresh()}
        >
          <ReplayIcon /> ジョブ一覧を更新
        </Button>
      </PageHeader>

      {jobs.loading ? (
        <Loading />
      ) : (
        <Container>
          <JobList jobs={jobs.value?.results ?? []} />
          <PaginationFooter
            count={jobs.value?.count ?? 0}
            maxRowCount={JobListParam.MAX_ROW_COUNT}
            page={page}
            changePage={changePage}
          />
        </Container>
      )}
    </Box>
  );
};
