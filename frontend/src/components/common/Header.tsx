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
import PopupState, { bindHover, bindMenu } from "material-ui-popup-state";
import HoverMenu from "material-ui-popup-state/HoverMenu";
import React, { FC, MouseEvent, useMemo, useState } from "react";
import { Link } from "react-router";
import { useInterval } from "react-use";

import { useTranslation } from "../../hooks/useTranslation";

import { SearchBox } from "components/common/SearchBox";
import { useSimpleSearch } from "hooks/useSimpleSearch";
import { aironeApiClient } from "repository/AironeApiClient";
import {
  advancedSearchPath,
  entitiesPath,
  groupsPath,
  jobsPath,
  listCategoryPath,
  loginPath,
  rolesPath,
  topPath,
  triggersPath,
  userPath,
  usersPath,
} from "routes/Routes";
import {
  JobOperations,
  JobRefreshIntervalMilliSec,
  JobStatuses,
} from "services/Constants";
import {
  getLatestCheckDate,
  jobTargetLabel,
  updateLatestCheckDate,
} from "services/JobUtil";
import { ServerContext } from "services/ServerContext";

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
  const serverContext = ServerContext.getInstance();

  const { t } = useTranslation();
  const [query, submitQuery] = useSimpleSearch();

  const [userAnchorEl, setUserAnchorEl] = useState<HTMLButtonElement | null>();
  const [jobAnchorEl, setJobAnchorEl] = useState<HTMLButtonElement | null>();
  const [latestCheckDate, setLatestCheckDate] = useState<Date | null>(
    getLatestCheckDate(),
  );
  const [recentJobs, setRecentJobs] = useState<Array<JobSerializers>>([]);

  useInterval(async () => {
    try {
      setRecentJobs(await aironeApiClient.getRecentJobs());
    } catch (e) {
      console.warn("failed to get recent jobs. will auto retried ...");
    }
  }, JobRefreshIntervalMilliSec);

  const uncheckedJobsCount = useMemo(() => {
    return latestCheckDate != null
      ? (recentJobs.filter((job) => job.createdAt > latestCheckDate).length ??
          0)
      : recentJobs.length;
  }, [latestCheckDate, recentJobs]);

  const handleLogout = async () => {
    await aironeApiClient.postLogout();
    window.location.href = `${loginPath()}?next=${window.location.pathname}`;
  };

  const handleOpenMenu = async (e: MouseEvent<HTMLButtonElement>) => {
    setJobAnchorEl(e.currentTarget);

    try {
      setRecentJobs(await aironeApiClient.getRecentJobs());
    } catch (e) {
      console.warn("failed to get recent jobs. will auto retried ...");
    }
    updateLatestCheckDate(new Date());
    setLatestCheckDate(getLatestCheckDate());
  };

  return (
    <Frame>
      <Fixed style={{ backgroundColor: serverContext?.headerColor }}>
        <StyledAppBar
          position="static"
          elevation={0}
          style={{ backgroundColor: serverContext?.headerColor }}
        >
          <StyledToolbar variant="dense">
            <TitleBox>
              <Title fontSize="24px" component={Link} to={topPath()}>
                {serverContext?.title}
              </Title>
              <Version fontSize="12px" title={serverContext?.version}>
                {serverContext?.version}
              </Version>
            </TitleBox>

            <MenuBox>
              <Button component={Link} to={listCategoryPath()}>
                {t("categories")}
              </Button>
              <Button component={Link} to={entitiesPath()}>
                {t("entities")}
              </Button>
              <Button component={Link} to={advancedSearchPath()}>
                {t("advancedSearch")}
              </Button>
              <PopupState variant="popover" popupId="basic">
                {(popupState) => (
                  <React.Fragment>
                    <Button {...bindHover(popupState)}>
                      {t("management")}
                      <KeyboardArrowDownIcon fontSize="small" />
                    </Button>
                    <HoverMenu {...bindMenu(popupState)}>
                      <MenuItem component={Link} to={usersPath()}>
                        {t("manageUsers")}
                      </MenuItem>
                      <MenuItem component={Link} to={groupsPath()}>
                        {t("manageGroups")}
                      </MenuItem>
                      <MenuItem component={Link} to={rolesPath()}>
                        {t("manageRoles")}
                      </MenuItem>
                      <MenuItem component={Link} to={triggersPath()}>
                        {t("manageTriggers")}
                      </MenuItem>
                    </HoverMenu>
                  </React.Fragment>
                )}
              </PopupState>

              {/* If there is another menu settings are passed from Server,
                  this represent another menu*/}
              {serverContext?.extendedHeaderMenus.map((menu, index) => (
                <PopupState variant="popover" popupId={menu.name} key={index}>
                  {(popupState) => (
                    <React.Fragment>
                      <Button {...bindHover(popupState)}>
                        {menu.name}
                        <KeyboardArrowDownIcon fontSize="small" />
                      </Button>
                      <HoverMenu {...bindMenu(popupState)}>
                        {menu.children.map((child, index) => (
                          <MenuItem key={index} component="a" href={child.url}>
                            {child.name}
                          </MenuItem>
                        ))}
                      </HoverMenu>
                    </React.Fragment>
                  )}
                </PopupState>
              ))}
            </MenuBox>

            <MenuBox justifyContent="flex-end">
              {serverContext?.legacyUiDisabled === false && (
                <Button href="/dashboard/">{t("previousVersion")}</Button>
              )}
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
                  {serverContext?.user?.username ?? "不明なユーザ"}{" "}
                  {t("currentUser")}
                </MenuItem>
                <Divider light />
                <MenuItem
                  component={Link}
                  to={userPath(serverContext?.user?.id ?? 0)}
                >
                  {t("userSetting")}
                </MenuItem>
                <MenuItem onClick={() => handleLogout()}>
                  {t("logout")}
                </MenuItem>
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
                        <a href={`/job/api/v2/${job.id}/download?encode=utf-8`}>
                          {jobTargetLabel(job)}
                        </a>
                      ) : (
                        <Typography>{jobTargetLabel(job)}</Typography>
                      )}
                    </MenuItem>
                  ))
                ) : (
                  <MenuItem>
                    <Typography>{t("noRunningJobs")}</Typography>
                  </MenuItem>
                )}
                <Divider light />
                <MenuItem component={Link} to={jobsPath()}>
                  {t("jobs")}
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
