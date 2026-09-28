import { JobSerializers } from "@dmm-com/airone-apiclient-typescript-fetch";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import MenuIcon from "@mui/icons-material/Menu";
import PersonIcon from "@mui/icons-material/Person";
import TaskIcon from "@mui/icons-material/Task";
import {
  AppBar,
  Badge,
  Box,
  Button,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemText,
  ListSubheader,
  Menu,
  MenuItem,
  Toolbar,
  Typography,
  TypographyTypeMap,
  useMediaQuery,
} from "@mui/material";
import { OverridableComponent } from "@mui/material/OverridableComponent";
import { styled, useTheme } from "@mui/material/styles";
import { FC, Fragment, MouseEvent, useMemo, useState } from "react";
import { Link } from "react-router";

import { useTranslation } from "../../hooks/useTranslation";

import { SearchBox } from "components/common/SearchBox";
import { useHoverMenus } from "hooks/useHoverMenus";
import { useInterval } from "hooks/useInterval";
import { useJobCompletionNotification } from "hooks/useJobCompletionNotification";
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

// Every responsive rule in this header is scoped below the `lg` breakpoint,
// so the header renders exactly as before on desktop screens regardless of
// how many menus a deployment adds.
const TitleBox = styled(Box)(({ theme }) => ({
  display: "flex",
  alignItems: "center",
  [theme.breakpoints.down("lg")]: {
    minWidth: 0,
  },
}));

const Title = styled(Typography)(({ theme }) => ({
  color: "white",
  textDecoration: "none",
  // Truncate a long site title rather than wrapping it out of the toolbar.
  [theme.breakpoints.down("lg")]: {
    minWidth: 0,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
})) as OverridableComponent<TypographyTypeMap>;

const Version = styled(Typography)(({ theme }) => ({
  color: "#FFFFFF8A",
  paddingLeft: "20px",
  maxWidth: "64px",
  overflow: "hidden",
  textOverflow: "ellipsis",
  whiteSpace: "nowrap",
  [theme.breakpoints.down("sm")]: {
    display: "none",
  },
}));

const NavToggleButton = styled(IconButton)(({ theme }) => ({
  color: "white",
  marginRight: "8px",
  [theme.breakpoints.up("md")]: {
    display: "none",
  },
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

const NavMenuBox = styled(MenuBox)(({ theme }) => ({
  [theme.breakpoints.down("lg")]: {
    "& > a, & > div > button": {
      flexShrink: 0,
      whiteSpace: "nowrap",
    },
  },
  [theme.breakpoints.down("md")]: {
    display: "none",
  },
}));

const ActionMenuBox = styled(MenuBox)(({ theme }) => ({
  [theme.breakpoints.down("lg")]: {
    minWidth: 0,
    "& > a": {
      flexShrink: 0,
      whiteSpace: "nowrap",
    },
  },
  // Without the inline navigation the title is what gives up space.
  [theme.breakpoints.down("md")]: {
    flexShrink: 0,
  },
}));

const SearchBoxWrapper = styled(Box)(({ theme }) => ({
  display: "flex",
  alignItems: "center",
  width: "240px",
  // Let the search box give up space before the toolbar starts clipping.
  [theme.breakpoints.down("lg")]: {
    minWidth: "120px",
  },
  [theme.breakpoints.down("sm")]: {
    display: "none",
  },
}));

const NavDrawerBox = styled("nav")({
  width: "280px",
  maxWidth: "80vw",
});

// The header search box is hidden on the smallest screens, so it is offered
// inside the navigation drawer instead.
const NavMenuSearchBox = styled(Box)(({ theme }) => ({
  padding: "8px 16px",
  [theme.breakpoints.up("sm")]: {
    display: "none",
  },
}));

export const Header: FC = () => {
  const serverContext = ServerContext.getInstance();

  const { t } = useTranslation();
  const [query, submitQuery] = useSimpleSearch();

  const [userAnchorEl, setUserAnchorEl] = useState<HTMLButtonElement | null>();
  const [jobAnchorEl, setJobAnchorEl] = useState<HTMLButtonElement | null>();
  const [navOpen, setNavOpen] = useState(false);

  // The drawer is only reachable below `md`; close it if the window is
  // widened past that, since its toggle button disappears there.
  const theme = useTheme();
  const isWide = useMediaQuery(theme.breakpoints.up("md"));
  if (isWide && navOpen) {
    setNavOpen(false);
  }
  const { getTriggerProps, getMenuProps } = useHoverMenus();

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

  useJobCompletionNotification(recentJobs);

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
            <NavToggleButton
              aria-label={t("openNavigationMenu")}
              aria-controls="nav-drawer"
              aria-expanded={navOpen}
              onClick={() => setNavOpen(true)}
            >
              <MenuIcon />
            </NavToggleButton>
            <Drawer
              id="nav-drawer"
              anchor="left"
              open={navOpen}
              onClose={() => setNavOpen(false)}
            >
              <NavDrawerBox>
                <NavMenuSearchBox>
                  <SearchBox
                    placeholder="Search"
                    defaultValue={query}
                    onKeyPress={(e, value) => {
                      if (e.key === "Enter") {
                        // Closing the drawer moves focus back to the toggle
                        // button, which would otherwise be clicked by this
                        // Enter key and reopen the drawer.
                        e.preventDefault();
                        setNavOpen(false);
                        submitQuery(value);
                      }
                    }}
                  />
                </NavMenuSearchBox>
                <List
                  component="div"
                  onClick={(e) => {
                    // Close the drawer once the user picks a destination.
                    if ((e.target as HTMLElement).closest("a")) {
                      setNavOpen(false);
                    }
                  }}
                >
                  <ListItemButton component={Link} to={listCategoryPath()}>
                    <ListItemText primary={t("categories")} />
                  </ListItemButton>
                  <ListItemButton component={Link} to={entitiesPath()}>
                    <ListItemText primary={t("entities")} />
                  </ListItemButton>
                  <ListItemButton component={Link} to={advancedSearchPath()}>
                    <ListItemText primary={t("advancedSearch")} />
                  </ListItemButton>
                  <ListSubheader component="div">
                    {t("management")}
                  </ListSubheader>
                  <ListItemButton component={Link} to={usersPath()}>
                    <ListItemText primary={t("manageUsers")} />
                  </ListItemButton>
                  <ListItemButton component={Link} to={groupsPath()}>
                    <ListItemText primary={t("manageGroups")} />
                  </ListItemButton>
                  <ListItemButton component={Link} to={rolesPath()}>
                    <ListItemText primary={t("manageRoles")} />
                  </ListItemButton>
                  <ListItemButton component={Link} to={triggersPath()}>
                    <ListItemText primary={t("manageTriggers")} />
                  </ListItemButton>
                  {serverContext?.extendedHeaderMenus.map((menu, index) => (
                    <Fragment key={index}>
                      <ListSubheader component="div">{menu.name}</ListSubheader>
                      {menu.children.map((child, childIndex) => (
                        <ListItemButton
                          key={childIndex}
                          component="a"
                          href={child.url}
                        >
                          <ListItemText primary={child.name} />
                        </ListItemButton>
                      ))}
                    </Fragment>
                  ))}
                  {serverContext?.legacyUiDisabled === false && (
                    <ListItemButton component="a" href="/dashboard/">
                      <ListItemText primary={t("previousVersion")} />
                    </ListItemButton>
                  )}
                </List>
              </NavDrawerBox>
            </Drawer>

            <TitleBox>
              <Title fontSize="24px" component={Link} to={topPath()}>
                {serverContext?.title}
              </Title>
              <Version fontSize="12px" title={serverContext?.version}>
                {serverContext?.version}
              </Version>
            </TitleBox>

            <NavMenuBox>
              <Button component={Link} to={listCategoryPath()}>
                {t("categories")}
              </Button>
              <Button component={Link} to={entitiesPath()}>
                {t("entities")}
              </Button>
              <Button component={Link} to={advancedSearchPath()}>
                {t("advancedSearch")}
              </Button>
              <Box {...getTriggerProps("management")}>
                <Button>
                  {t("management")}
                  <KeyboardArrowDownIcon fontSize="small" />
                </Button>
                <Menu {...getMenuProps("management")}>
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
                </Menu>
              </Box>

              {/* If there is another menu settings are passed from Server,
                  this represent another menu*/}
              {serverContext?.extendedHeaderMenus.map((menu, index) => (
                <Box key={index} {...getTriggerProps(index)}>
                  <Button>
                    {menu.name}
                    <KeyboardArrowDownIcon fontSize="small" />
                  </Button>
                  <Menu {...getMenuProps(index)}>
                    {menu.children.map((child, childIndex) => (
                      <MenuItem key={childIndex} component="a" href={child.url}>
                        {child.name}
                      </MenuItem>
                    ))}
                  </Menu>
                </Box>
              ))}
            </NavMenuBox>

            <ActionMenuBox justifyContent="flex-end">
              {serverContext?.legacyUiDisabled === false && (
                <Button
                  href="/dashboard/"
                  sx={{ display: { xs: "none", md: "inline-flex" } }}
                >
                  {t("previousVersion")}
                </Button>
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
                  onKeyPress={(e, value) => {
                    e.key === "Enter" && submitQuery(value);
                  }}
                  inputSx={{ height: "42px", "& input": { py: "9px" } }}
                />
              </SearchBoxWrapper>
            </ActionMenuBox>
          </StyledToolbar>
        </StyledAppBar>
      </Fixed>
    </Frame>
  );
};
