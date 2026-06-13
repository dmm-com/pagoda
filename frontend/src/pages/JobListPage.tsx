import ReplayIcon from "@mui/icons-material/Replay";
import {
  Box,
  Button,
  Container,
  FormControlLabel,
  Switch,
  Typography,
} from "@mui/material";
import { FC, Suspense, useMemo, useState } from "react";
import { useLocation } from "react-router";

import { usePagodaSWR } from "../hooks/usePagodaSWR";

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
import { ServerContext } from "services/ServerContext";

const JobListContent: FC<{
  page: number;
  changePage: (page: number) => void;
  targetId?: number;
  allUsers?: boolean;
}> = ({ page, changePage, targetId, allUsers }) => {
  const { data: jobs, mutate: refreshJobs } = usePagodaSWR(
    ["jobs", page, targetId, allUsers],
    () => aironeApiClient.getJobs(page, targetId, undefined, allUsers),
    { suspense: true },
  );

  return (
    <Container maxWidth="xl">
      <Box display="flex" justifyContent="flex-end" mb={2}>
        <Button
          variant="outlined"
          color="success"
          onClick={() => refreshJobs()}
        >
          <ReplayIcon /> ジョブ一覧を更新
        </Button>
      </Box>
      <JobList jobs={jobs.results ?? []} showUser={allUsers} />
      <PaginationFooter
        count={jobs.count ?? 0}
        maxRowCount={JobListParam.MAX_ROW_COUNT}
        page={page}
        changePage={changePage}
      />
    </Container>
  );
};

export const JobListPage: FC = () => {
  const location = useLocation();
  const isSuperuser = ServerContext.getInstance()?.user?.isSuperuser === true;

  const { page, changePage } = usePage();
  const [allUsers, setAllUsers] = useState(false);

  const { targetId } = useMemo(() => {
    const params = new URLSearchParams(location.search);
    const targetId = params.get("target_id");
    return {
      targetId: targetId ? Number(targetId) : undefined,
    };
  }, [location.search]);

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={AironeLink} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">ジョブ一覧</Typography>
      </AironeBreadcrumbs>

      <PageHeader title="ジョブ一覧">
        {isSuperuser && (
          <FormControlLabel
            control={
              <Switch
                checked={allUsers}
                onChange={(e) => setAllUsers(e.target.checked)}
              />
            }
            label="全ユーザーのジョブを表示"
          />
        )}
      </PageHeader>

      <Suspense fallback={<Loading />}>
        <JobListContent
          page={page}
          changePage={changePage}
          targetId={targetId}
          allUsers={allUsers ? true : undefined}
        />
      </Suspense>
    </Box>
  );
};
