import React, { useEffect, useState } from "react";
import { Link, useHistory } from "react-router-dom";
import { grey } from "@material-ui/core/colors";
import { fade, makeStyles } from "@material-ui/core/styles";
import AccountBox from "@material-ui/icons/AccountBox";
import FormatListBulletedIcon from "@material-ui/icons/FormatListBulleted";
import SearchIcon from "@material-ui/icons/Search";
import AppBar from "@material-ui/core/AppBar";
import Box from "@material-ui/core/Box";
import Button from "@material-ui/core/Button";
import IconButton from "@material-ui/core/IconButton";
import InputBase from "@material-ui/core/InputBase";
import Toolbar from "@material-ui/core/Toolbar";
import Typography from "@material-ui/core/Typography";
import { Badge, Divider, Menu, MenuItem } from "@material-ui/core";
import { getRecentJobs } from "../utils/AironeAPIClient";
import { useAsync } from "react-use";

const useStyles = makeStyles((theme) => ({
  root: {
    flexGrow: 1,
  },
  menu: {
    marginRight: theme.spacing(2),
  },
  title: {
    flexGrow: 1,
    color: "white",
  },

  search: {
    position: "relative",
    borderRadius: theme.shape.borderRadius,
    backgroundColor: fade(theme.palette.common.white, 0.15),
    "&:hover": {
      backgroundColor: fade(theme.palette.common.white, 0.25),
    },
    marginRight: theme.spacing(2),
    marginLeft: 0,
    width: "100%",
    [theme.breakpoints.up("sm")]: {
      marginLeft: theme.spacing(3),
      width: "auto",
    },
  },
  searchIcon: {
    padding: theme.spacing(0, 2),
    height: "100%",
    position: "absolute",
    pointerEvents: "none",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  inputRoot: {
    color: "inherit",
  },
  inputInput: {
    padding: theme.spacing(1, 1, 1, 0),
    // vertical padding + font size from searchIcon
    paddingLeft: `calc(1em + ${theme.spacing(4)}px)`,
    transition: theme.transitions.create("width"),
    width: "100%",
    [theme.breakpoints.up("md")]: {
      width: "20ch",
    },
  },
}));

export default function Header({}) {
  const classes = useStyles();
  const history = useHistory();

  const [userAnchorEl, setUserAnchorEl] = useState();
  const [jobAnchorEl, setJobAnchorEl] = useState();

  const recentJobs = useAsync(async () => {
    return getRecentJobs()
      .then((data) => data.json())
      .then((data) => data["result"]);
  });

  const [entryQuery, setEntryQuery] = useState("");

  const handleSearchQuery = (event) => {
    if (event.key === "Enter") {
      history.push(`/new-ui/search?entry_name=${entryQuery}`);
    }
  };

  return (
    <div className={classes.root}>
      <AppBar position="static">
        <Toolbar>
          <Typography
            variant="h6"
            className={classes.title}
            component={Link}
            to="/new-ui/"
          >
            AirOne(New UI)
          </Typography>

          <Box className={classes.menu}>
            <IconButton
              aria-controls="user-menu"
              aria-haspopup="true"
              onClick={(e) => setUserAnchorEl(e.currentTarget)}
              style={{ color: grey[50] }}
            >
              <AccountBox />
            </IconButton>
            <Menu
              id="user-menu"
              anchorEl={userAnchorEl}
              open={Boolean(userAnchorEl)}
              onClose={() => setUserAnchorEl(null)}
              keepMounted
            >
              <MenuItem>ユーザ設定</MenuItem>
              <MenuItem>
                <a href="/auth/logout/">ログアウト</a>
              </MenuItem>
            </Menu>

            <IconButton
              aria-controls="job-menu"
              aria-haspopup="true"
              onClick={(e) => setJobAnchorEl(e.currentTarget)}
              style={{ color: grey[50] }}
            >
              {!recentJobs.loading && (
                <Badge badgeContent={recentJobs.value.length} color="secondary">
                  <FormatListBulletedIcon />
                </Badge>
              )}
            </IconButton>
            <Menu
              id="job-menu"
              anchorEl={jobAnchorEl}
              open={Boolean(jobAnchorEl)}
              onClose={(e) => setJobAnchorEl(null)}
              keepMounted
            >
              {!recentJobs.loading &&
                recentJobs.value.map((recentJob) => (
                  <MenuItem>
                    <Typography
                      component={Link}
                      to={`/new-ui/jobs/${recentJob.id}`}
                    >
                      {recentJob.target.name}
                    </Typography>
                  </MenuItem>
                ))}
              <Divider light />
              <MenuItem>
                <Typography component={Link} to={`/new-ui/jobs`}>
                  ジョブ一覧
                </Typography>
              </MenuItem>
            </Menu>
          </Box>

          <div className={classes.search}>
            <div className={classes.searchIcon}>
              <SearchIcon />
            </div>
            <InputBase
              placeholder="Search…"
              classes={{
                root: classes.inputRoot,
                input: classes.inputInput,
              }}
              inputProps={{ "aria-label": "search" }}
              onChange={(e) => setEntryQuery(e.target.value)}
              onKeyPress={handleSearchQuery}
            />
            <Button
              variant="contained"
              component={Link}
              to={`/new-ui/search?entry_name=${entryQuery}`}
            >
              検索
            </Button>
          </div>
        </Toolbar>
      </AppBar>
    </div>
  );
}
