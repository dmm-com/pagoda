import PersonIcon from "@mui/icons-material/Person";
import TaskIcon from "@mui/icons-material/Task";
import {
  alpha,
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
import { grey } from "@mui/material/colors";
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
} from "../Routes";
import { getRecentJobs } from "../utils/AironeAPIClient";
import { DjangoContext } from "../utils/DjangoContext";

const useStyles = makeStyles<Theme>((theme) => ({
  centeritem: {
    paddingLeft: "10%",
    paddingRight: "10%",
  },
  menu: {
    margin: theme.spacing(0, 1),
  },
  title: {
    color: "white",
  },
  version_description: {
    color: "#FFFFFF8A",
  },
  search: {
    display: "flex",
    borderRadius: theme.shape.borderRadius,
    backgroundColor: alpha(theme.palette.common.white, 0.15),
    "&:hover": {
      backgroundColor: alpha(theme.palette.common.white, 0.25),
    },
    margin: theme.spacing(0, 1),
    [theme.breakpoints.up("sm")]: {
      width: "auto",
    },
  },
  searchTextFieldInput: {
    "&::placeholder": {
      color: "white",
    },
  },
}));

export const Header: FC = () => {
  const classes = useStyles();

  const [userAnchorEl, setUserAnchorEl] = useState<HTMLButtonElement | null>();
  const [jobAnchorEl, setJobAnchorEl] = useState<HTMLButtonElement | null>();

  const djangoContext = DjangoContext.getInstance();

  const recentJobs = useAsync(async () => {
    return getRecentJobs()
      .then((data) => data.json())
      .then((data) => data["result"]);
  });

  return (
    <Box>
      <AppBar position="static" className={classes.centeritem}>
        <Toolbar>
          {/* FIX ME. I want to remove this style coding in component */}
          <Box sx={{ alignItems: "flex-end", display: "flex", color: "white" }}>
            <Typography
              // make margin with title and version description
              sx={{ mr: "10px" }}
              variant="h5"
              color="inherit"
              className={classes.title}
            >
              AirOne
            </Typography>

            <Typography
              className={classes.version_description}
              ml={"20px"}
              mr={"30px"}
              fontSize={"16px"}
            >
              {djangoContext.version}
            </Typography>
          </Box>

          <Box
            className={classes.menu}
            sx={{ flexGrow: 1, display: "flex", color: "white" }}
          >
            <Button color="inherit" href={entitiesPath()}>
              エンティティ一覧
            </Button>
            <Button color="inherit" href={advancedSearchPath()}>
              高度な検索
            </Button>
            <Button color="inherit" href={usersPath()}>
              ユーザ管理
            </Button>
            <Button color="inherit" href={groupsPath()}>
              グループ管理
            </Button>
          </Box>

          <Box className={classes.menu}>
            <IconButton
              aria-controls="job-menu"
              aria-haspopup="true"
              onClick={(e) => setJobAnchorEl(e.currentTarget)}
              style={{ color: grey[50] }}
            >
              {!recentJobs.loading && (
                <Badge badgeContent={recentJobs.value.length} color="secondary">
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
            <IconButton
              aria-controls="user-menu"
              aria-haspopup="true"
              onClick={(e) => setUserAnchorEl(e.currentTarget)}
              style={{ color: grey[50] }}
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
                <Link to={userPath(djangoContext.user.id)}>ユーザ設定</Link>
              </MenuItem>
              <MenuItem>
                <a href="/auth/logout/">ログアウト</a>
              </MenuItem>
            </Menu>
          </Box>
        </Toolbar>
      </AppBar>
    </Box>
  );
};
