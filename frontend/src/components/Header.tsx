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
  Theme,
  Toolbar,
  Typography,
} from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC, useState } from "react";
import { Link } from "react-router-dom";
import { useAsync } from "react-use";

import {
  jobsPath,
  userPath,
  usersPath,
  groupsPath,
  entitiesPath,
  advancedSearchPath,
  loginPath,
} from "Routes";
import { getRecentJobs, postLogout } from "utils/AironeAPIClient";
import { DjangoContext } from "utils/DjangoContext";

const useStyles = makeStyles<Theme>((theme) => ({
  frame: {
    width: "100%",
    height: "56px",
  },
  fixed: {
    position: "fixed",
    zIndex: 2,
    width: "100%",
    backgroundColor: theme.palette.primary.main,
    display: "flex",
    justifyContent: "center",
  },
  appBar: {
    maxWidth: theme.breakpoints.values.lg,
  },
  toolBar: {
    height: "56px",
  },
  titleBox: {
    display: "flex",
    alignItems: "center",
  },
  title: {
    color: "white",
  },
  version: {
    color: "#FFFFFF8A",
    padding: "0px 24px",
  },
  menuBox: {
    flexGrow: 1,
    display: "flex",
    color: "white",
    marginLeft: "24px",
    "& a": {
      color: "inherit",
      margin: "0px 4px",
    },
    "& button": {
      color: "inherit",
      margin: "0px 4px",
    },
  },
}));

export const Header: FC = () => {
  const classes = useStyles();

  const [userAnchorEl, setUserAnchorEl] = useState<HTMLButtonElement | null>();
  const [jobAnchorEl, setJobAnchorEl] = useState<HTMLButtonElement | null>();

  const djangoContext = DjangoContext.getInstance();

  const recentJobs = useAsync(async () => {
    const resp = await getRecentJobs();
    const data = await resp.json();
    return data["result"];
  });

  const handleLogout = () => {
    postLogout().then(() => {
      window.location.href = `${loginPath()}?next=${window.location.pathname}`;
    });
  };

  return (
    <Box className={classes.frame}>
      <Box className={classes.fixed}>
        <AppBar position="static" elevation={0} className={classes.appBar}>
          <Toolbar variant="dense" className={classes.toolBar}>
            <Box className={classes.titleBox}>
              <Typography fontSize="24px" className={classes.title}>
                AirOne
              </Typography>
              <Typography fontSize="16px" className={classes.version}>
                {djangoContext.version}
              </Typography>
            </Box>

            <Box className={classes.menuBox}>
              <Button href={entitiesPath()}>エンティティ一覧</Button>
              <Button href={advancedSearchPath()}>高度な検索</Button>
              <Button href={usersPath()}>ユーザ管理</Button>
              <Button href={groupsPath()}>グループ管理</Button>
            </Box>

            <Box justifyContent="flex-end" className={classes.menuBox}>
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
                disableScrollLock
              >
                <MenuItem>
                  <Link to={userPath(djangoContext.user.id)}>ユーザ設定</Link>
                </MenuItem>
                <MenuItem>
                  <Link to="#" onClick={() => handleLogout()}>
                    ログアウト
                  </Link>
                </MenuItem>
              </Menu>
              <IconButton
                aria-controls="job-menu"
                aria-haspopup="true"
                onClick={(e) => setJobAnchorEl(e.currentTarget)}
              >
                {!recentJobs.loading && (
                  <Badge
                    badgeContent={recentJobs.value.length}
                    color="secondary"
                  >
                    <TaskIcon />
                  </Badge>
                )}
              </IconButton>
              <Menu
                id="job-menu"
                anchorEl={jobAnchorEl}
                open={Boolean(jobAnchorEl)}
                onClose={() => setJobAnchorEl(null)}
                keepMounted
                disableScrollLock
              >
                {!recentJobs.loading && recentJobs.value.length > 0 ? (
                  recentJobs.value.map((recentJob) => (
                    <MenuItem key={recentJob.id}>
                      <Typography component={Link} to={jobsPath()}>
                        {recentJob.target.name}
                      </Typography>
                    </MenuItem>
                  ))
                ) : (
                  <MenuItem>
                    <Typography>実行タスクなし</Typography>
                  </MenuItem>
                )}
                <Divider light />
                <MenuItem>
                  <Typography component={Link} to={jobsPath()}>
                    ジョブ一覧
                  </Typography>
                </MenuItem>
              </Menu>
            </Box>
          </Toolbar>
        </AppBar>
      </Box>
    </Box>
  );
};
