import ReplayIcon from "@mui/icons-material/Replay";
import {
  Box,
  Button,
  Container,
  FormControlLabel,
  MenuItem,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import { FC, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router";

import { usePagodaSWR } from "../hooks/usePagodaSWR";

import { AironeLink } from "components";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { PaginationFooter } from "components/common/PaginationFooter";
import { JobList } from "components/job/JobList";
import { usePage } from "hooks/usePage";
import { useTranslation } from "hooks/useTranslation";
import { aironeApiClient, JobSearchFilters } from "repository/AironeApiClient";
import { topPath } from "routes/Routes";
import { JobListParam, JobOperations, JobStatuses } from "services/Constants";
import { jobOperationLabel, jobStatusLabel } from "services/JobUtil";
import { ServerContext } from "services/ServerContext";

const filterKeys = [
  "job_id",
  "status",
  "operation",
  "user",
  "text",
  "created_after",
  "created_before",
  "include_hidden",
  "internal_only",
  "include_empty_success",
];

const getOperationGroups = () => {
  const groups = new Map<string, number[]>();
  const unknownLabel = jobOperationLabel(undefined);
  for (const operation of Object.values(JobOperations)) {
    const label = jobOperationLabel(operation);
    if (label === unknownLabel) continue;
    groups.set(label, [...(groups.get(label) ?? []), operation]);
  }
  return Array.from(groups, ([label, operations]) => ({
    label,
    operations,
    value: operations.join(","),
  }));
};

const groupedOperationValue = (raw: string): string => {
  const operation = Number(raw.split(",")[0]);
  return (
    getOperationGroups().find((group) => group.operations.includes(operation))
      ?.value ?? ""
  );
};

const readFilters = (params: URLSearchParams): JobSearchFilters => ({
  jobId: params.get("job_id") ?? "",
  status: params.get("status") ?? "",
  operation: groupedOperationValue(params.get("operation") ?? ""),
  user: params.get("user") ?? "",
  text: params.get("text") ?? "",
  createdAfter: params.get("created_after") ?? "",
  createdBefore: params.get("created_before") ?? "",
});

const JobListContent: FC<{
  page: number;
  changePage: (page: number) => void;
  targetId?: number;
  allUsers?: boolean;
  filters: JobSearchFilters;
}> = ({ page, changePage, targetId, allUsers, filters }) => {
  const { t } = useTranslation();
  const {
    data: jobs,
    isLoading,
    mutate: refreshJobs,
  } = usePagodaSWR(
    ["jobs", page, targetId, allUsers, filters],
    () => aironeApiClient.getJobs(page, targetId, undefined, allUsers, filters),
    { refreshInterval: 15_000 },
  );

  if (isLoading || !jobs) return <Loading />;

  return (
    <Container maxWidth="xl">
      <Box display="flex" justifyContent="flex-end" mb={2}>
        <Button
          variant="outlined"
          color="success"
          onClick={() => refreshJobs()}
        >
          <ReplayIcon />
          {` ${t("job.list.refresh")}`}
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
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const isSuperuser = ServerContext.getInstance()?.user?.isSuperuser === true;

  const { page, changePage } = usePage();
  const params = useMemo(
    () => new URLSearchParams(location.search),
    [location.search],
  );
  const filters = useMemo(() => readFilters(params), [params]);
  const [draft, setDraft] = useState(filters);
  const [previousSearch, setPreviousSearch] = useState(location.search);
  if (previousSearch !== location.search) {
    setPreviousSearch(location.search);
    setDraft(filters);
  }
  const allUsers = isSuperuser && params.get("all_users") === "true";

  const targetId = params.get("target_id")
    ? Number(params.get("target_id"))
    : undefined;

  const updateSearch = (next: URLSearchParams) => {
    next.set("page", "1");
    navigate({ pathname: location.pathname, search: next.toString() });
  };

  const submitSearch = () => {
    const next = new URLSearchParams(location.search);
    for (const key of filterKeys) next.delete(key);
    const values: Record<string, string | undefined> = {
      job_id: draft.jobId?.trim(),
      status: draft.status,
      operation: draft.operation,
      user: draft.user?.trim(),
      text: draft.text?.trim(),
      created_after: draft.createdAfter,
      created_before: draft.createdBefore,
    };
    for (const [key, value] of Object.entries(values)) {
      if (value) next.set(key, value);
    }
    updateSearch(next);
  };

  const clearSearch = () => {
    const next = new URLSearchParams(location.search);
    for (const key of filterKeys) next.delete(key);
    setDraft(readFilters(next));
    updateSearch(next);
  };

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={AironeLink} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">{t("job.list.title")}</Typography>
      </AironeBreadcrumbs>

      <PageHeader title={t("job.list.title")}>
        {isSuperuser && (
          <FormControlLabel
            control={
              <Switch
                checked={allUsers}
                onChange={(e) => {
                  const next = new URLSearchParams(location.search);
                  if (e.target.checked) next.set("all_users", "true");
                  else next.delete("all_users");
                  updateSearch(next);
                }}
              />
            }
            label={t("job.list.showAllUsers")}
          />
        )}
      </PageHeader>

      <Container maxWidth="xl">
        <Box
          component="div"
          role="search"
          onKeyDown={(event) => {
            if (
              event.key === "Enter" &&
              event.target instanceof HTMLInputElement
            ) {
              event.preventDefault();
              submitSearch();
            }
          }}
          display="flex"
          flexWrap="wrap"
          gap={2}
          mb={2}
        >
          <TextField
            size="small"
            label={t("job.list.jobId")}
            type="number"
            value={draft.jobId ?? ""}
            onChange={(e) => setDraft({ ...draft, jobId: e.target.value })}
          />
          <TextField
            select
            size="small"
            label={t("job.list.statusColumn")}
            value={draft.status ?? ""}
            onChange={(e) => setDraft({ ...draft, status: e.target.value })}
            sx={{ minWidth: 140 }}
          >
            <MenuItem value="">{t("job.list.any")}</MenuItem>
            {Object.values(JobStatuses).map((status) => (
              <MenuItem key={status} value={String(status)}>
                {jobStatusLabel(status)}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            select
            size="small"
            label={t("job.list.operationColumn")}
            value={draft.operation ?? ""}
            onChange={(e) => setDraft({ ...draft, operation: e.target.value })}
            sx={{ minWidth: 190 }}
          >
            <MenuItem value="">{t("job.list.any")}</MenuItem>
            {getOperationGroups().map(({ label, value }) => (
              <MenuItem key={value} value={value}>
                {label}
              </MenuItem>
            ))}
          </TextField>
          {isSuperuser && (
            <TextField
              size="small"
              label={t("job.list.userColumn")}
              value={draft.user ?? ""}
              onChange={(e) => setDraft({ ...draft, user: e.target.value })}
            />
          )}
          <TextField
            size="small"
            label={t("job.list.messageSearch")}
            value={draft.text ?? ""}
            onChange={(e) => setDraft({ ...draft, text: e.target.value })}
          />
          <Box display="flex" gap={2} sx={{ width: "min(446px, 100%)" }}>
            <TextField
              size="small"
              label={t("job.list.createdAfter")}
              type="datetime-local"
              sx={{ flex: "1 1 0", minWidth: 0 }}
              InputLabelProps={{ shrink: true }}
              value={draft.createdAfter ?? ""}
              onChange={(e) =>
                setDraft({ ...draft, createdAfter: e.target.value })
              }
            />
            <TextField
              size="small"
              label={t("job.list.createdBefore")}
              type="datetime-local"
              sx={{ flex: "1 1 0", minWidth: 0 }}
              InputLabelProps={{ shrink: true }}
              value={draft.createdBefore ?? ""}
              onChange={(e) =>
                setDraft({ ...draft, createdBefore: e.target.value })
              }
            />
          </Box>
          <Button type="button" variant="contained" onClick={submitSearch}>
            {t("job.list.search")}
          </Button>
          <Button type="button" onClick={clearSearch}>
            {t("job.list.clear")}
          </Button>
        </Box>
      </Container>

      <JobListContent
        page={page}
        changePage={changePage}
        targetId={targetId}
        allUsers={allUsers ? true : undefined}
        filters={filters}
      />
    </Box>
  );
};
