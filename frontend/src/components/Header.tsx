import { JobSerializers } from "@dmm-com/airone-apiclient-typescript-fetch";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import PersonIcon from "@mui/icons-material/Person";
import TaskIcon from "@mui/icons-material/Task";
import {
  AppBar,
  Badge,
  Box,
  Button,
  Divider,
  IconButton,
  Menu,
  MenuItem,
  Toolbar,
  Typography,
  TypographyTypeMap,
} from "@mui/material";
import { OverridableComponent } from "@mui/material/OverridableComponent";
import { styled } from "@mui/material/styles";
import React, { FC, MouseEvent, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useInterval } from "react-use";

import { useSimpleSearch } from "../hooks/useSimpleSearch";
import { aironeApiClientV2 } from "../repository/AironeApiClientV2";
import {
  JobOperations,
  JobRefreshIntervalMilliSec,
  JobStatuses,
} from "../services/Constants";
import {
  getLatestCheckDate,
  jobTargetLabel,
  updateLatestCheckDate,
} from "../services/JobUtil";

import { SearchBox } from "./common/SearchBox";

import {
  jobsPath,
  userPath,
  usersPath,
  groupsPath,
  entitiesPath,
  advancedSearchPath,
  loginPath,
  rolesPath,
  topPath,
} from "Routes";
import { postLogout } from "repository/AironeAPIClient";
import { DjangoContext } from "services/DjangoContext";

const Frame = styled(Box)(({}) => ({
  width: "100%",
  height: "56px",
}));

const Fixed = styled(Box)(({ theme }) => ({
  position: "fixed",
  zIndex: 2,
  width: "100%",
  backgroundColor: theme.palette.primary.main,
  display: "flex",
  justifyContent: "center",
}));

const StyledAppBar = styled(AppBar)(({ theme }) => ({
  maxWidth: theme.breakpoints.values.lg,
}));

const StyledToolbar = styled(Toolbar)(({}) => ({
  height: "56px",
}));

const TitleBox = styled(Box)(({}) => ({
  display: "flex",
  alignItems: "center",
}));

const Title = styled(Typography)(({}) => ({
  color: "white",
  textDecoration: "none",
})) as OverridableComponent<TypographyTypeMap>;

const Version = styled(Typography)(({}) => ({
  color: "#FFFFFF8A",
  paddingLeft: "20px",
  maxWidth: "64px",
  overflow: "hidden",
  textOverflow: "ellipsis",
  whiteSpace: "nowrap",
}));

const MenuBox = styled(Box)(({}) => ({
  flexGrow: 1,
  display: "flex",
  color: "white",
  marginLeft: "16px",
  "& a": {
    color: "inherit",
    margin: "0px 4px",
  },
  "& button": {
    color: "inherit",
    margin: "0px 4px",
  },
}));

const SearchBoxWrapper = styled(Box)(({}) => ({
  display: "flex",
  alignItems: "center",
  width: "240px",
}));

export const Header: FC = () => {
  const [query, submitQuery] = useSimpleSearch();

  const [settingAnchorEl, setSettingAnchorEl] =
    useState<HTMLButtonElement | null>();
  const [userAnchorEl, setUserAnchorEl] = useState<HTMLButtonElement | null>();
  const [jobAnchorEl, setJobAnchorEl] = useState<HTMLButtonElement | null>();
  const [latestCheckDate, setLatestCheckDate] = useState<Date | null>(
    getLatestCheckDate()
  );
  const [recentJobs, setRecentJobs] = useState<Array<JobSerializers>>([]);

  const djangoContext = DjangoContext.getInstance();

  useInterval(async () => {
    try {
      setRecentJobs(await aironeApiClientV2.getRecentJobs());
    } catch (e) {
      console.warn("failed to get recent jobs. will auto retried ...");
    }
  }, JobRefreshIntervalMilliSec);

  const uncheckedJobsCount = useMemo(() => {
    return latestCheckDate != null
      ? recentJobs.filter((job) => job.createdAt > latestCheckDate).length ?? 0
      : recentJobs.length;
  }, [latestCheckDate, recentJobs]);

  const handleLogout = () => {
    postLogout().then(() => {
      window.location.href = `${loginPath()}?next=${window.location.pathname}`;
    });
  };

  const handleOpenMenu = async (e: MouseEvent<HTMLButtonElement>) => {
    setJobAnchorEl(e.currentTarget);

    try {
      setRecentJobs(await aironeApiClientV2.getRecentJobs());
    } catch (e) {
      console.warn("failed to get recent jobs. will auto retried ...");
    }
    updateLatestCheckDate(new Date());
    setLatestCheckDate(getLatestCheckDate());
  };

  return (
    <Frame>
      <Fixed>
        <StyledAppBar position="static" elevation={0}>
          <StyledToolbar variant="dense">
            <TitleBox>
              <Title fontSize="24px" component={Link} to={topPath()}>
                AirOne
              </Title>
              <Version fontSize="12px" title={djangoContext?.version}>
                {djangoContext?.version}
              </Version>
            </TitleBox>

            <MenuBox>
              <Button component={Link} to={entitiesPath()}>
                エンティティ一覧
              </Button>
              <Button component={Link} to={advancedSearchPath()}>
                高度な検索
              </Button>
              <Button
                //onClick={(e) => setSettingAnchorEl(e.currentTarget)}
                onMouseOver={(e) => setSettingAnchorEl(e.currentTarget)}
              >
                管理機能
                <KeyboardArrowDownIcon fontSize="small" />
              </Button>
              <Menu
                id="setting-menu"
                anchorEl={settingAnchorEl}
                open={Boolean(settingAnchorEl)}
                onClose={() => setSettingAnchorEl(null)}
                MenuListProps={{ onMouseLeave: () => setSettingAnchorEl(null) }}
                keepMounted
              >
                <MenuItem component={Link} to={usersPath()}>
                  ユーザ管理
                </MenuItem>
                <MenuItem component={Link} to={groupsPath()}>
                  グループ管理
                </MenuItem>
                <MenuItem component={Link} to={rolesPath()}>
                  ロール管理
                </MenuItem>
              </Menu>
            </MenuBox>

            <MenuBox justifyContent="flex-end">
              <Button href="/dashboard/">旧デザイン</Button>
              <IconButton
                aria-controls="user-menu"
                aria-haspopup="true"
                onClick={(e) => setUserAnchorEl(e.currentTarget)}
              >
                <PersonIcon />
              </IconButton>
              <Menu
                id="user-menu"
                anchorEl={userAnchorEl}
                open={Boolean(userAnchorEl)}
                onClose={() => setUserAnchorEl(null)}
                keepMounted
              >
                <MenuItem>
                  {djangoContext?.user?.username ?? "不明なユーザ"}{" "}
                  としてログイン中
                </MenuItem>
                <Divider light />
                <MenuItem
                  component={Link}
                  to={userPath(djangoContext?.user?.id ?? 0)}
                >
                  ユーザ設定
                </MenuItem>
                <MenuItem onClick={() => handleLogout()}>ログアウト</MenuItem>
              </Menu>
              <IconButton
                aria-controls="job-menu"
                aria-haspopup="true"
                onClick={handleOpenMenu}
              >
                <Badge badgeContent={uncheckedJobsCount} color="secondary">
                  <TaskIcon />
                </Badge>
              </IconButton>
              <Menu
                anchorEl={jobAnchorEl}
                open={Boolean(jobAnchorEl)}
                onClose={() => setJobAnchorEl(null)}
                keepMounted
              >
                {recentJobs.length > 0 ? (
                  recentJobs.map((job) => (
                    <MenuItem key={job.id}>
                      {(job.operation == JobOperations.EXPORT_ENTRY ||
                        job.operation == JobOperations.EXPORT_SEARCH_RESULT ||
                        job.operation == JobOperations.EXPORT_ENTRY_V2 ||
                        job.operation ==
                          JobOperations.EXPORT_SEARCH_RESULT_V2) &&
                      job.status == JobStatuses.DONE ? (
                        <a href={`/job/api/v2/download/${job.id}`}>
                          {jobTargetLabel(job)}
                        </a>
                      ) : (
                        <Typography>{jobTargetLabel(job)}</Typography>
                      )}
                    </MenuItem>
                  ))
                ) : (
                  <MenuItem>
                    <Typography>実行タスクなし</Typography>
                  </MenuItem>
                )}
                <Divider light />
                <MenuItem component={Link} to={jobsPath()}>
                  ジョブ一覧
                </MenuItem>
              </Menu>
              <SearchBoxWrapper>
                <SearchBox
                  placeholder="Search"
                  defaultValue={query}
                  onKeyPress={(e) => {
                    e.key === "Enter" && submitQuery(e.target.value);
                  }}
                  inputSx={{ height: "42px", "& input": { py: "9px" } }}
                />
              </SearchBoxWrapper>
            </MenuBox>
          </StyledToolbar>
        </StyledAppBar>
      </Fixed>
    </Frame>
  );
};
