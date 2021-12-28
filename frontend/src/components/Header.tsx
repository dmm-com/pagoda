import AccountBox from "@mui/icons-material/AccountBox";
import FormatListBulletedIcon from "@mui/icons-material/FormatListBulleted";
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
  TextField,
  Theme,
  Toolbar,
  Typography,
} from "@mui/material";
import { grey } from "@mui/material/colors";
import { makeStyles } from "@mui/styles";
import React, { FC, useState } from "react";
import { Link, useHistory } from "react-router-dom";
import { useAsync } from "react-use";

import { jobsPath, searchPath, topPath, userPath } from "../Routes";
import { getRecentJobs } from "../utils/AironeAPIClient";
import { DjangoContext } from "../utils/DjangoContext";

const useStyles = makeStyles<Theme>((theme) => ({
  root: {
    //flexGrow: 1,
  },
  centeritem: {
    paddingLeft: "10%",
    paddingRight: "10%",
  },
  menu: {
    margin: theme.spacing(0, 1),
  },
  title: {
    //flexGrow: 1,
    color: "white",
  },
  shortcut: {
    flexGrow: 1,
    flexDirection: "row",
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
  searchIcon: {
    padding: theme.spacing(0, 2),
    height: "100%",
    position: "absolute",
    pointerEvents: "none",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  searchTextFieldInput: {
    "&::placeholder": {
      color: "white",
    },
  },
}));

export const Header: FC = () => {
  const classes = useStyles();
  const history = useHistory();

  const [userAnchorEl, setUserAnchorEl] = useState<HTMLButtonElement | null>();
  const [jobAnchorEl, setJobAnchorEl] = useState<HTMLButtonElement | null>();

  const djangoContext = DjangoContext.getInstance();

  const recentJobs = useAsync(async () => {
    return getRecentJobs()
      .then((data) => data.json())
      .then((data) => data["result"]);
  });

  const [entryQuery, setEntryQuery] = useState("");

  const handleSearchQuery = (event) => {
    if (event.key === "Enter") {
      history.push(`${searchPath()}?entry_name=${entryQuery}`);
    }
  };

  return (
    <Box className={classes.root}>
      <AppBar position="static" className={classes.centeritem}>
        <Toolbar>
          {/* FIX ME. I want to remove this style coding in component */}
          <Box sx={{ alignItems: 'flex-end', display: 'flex'}}>
              <Typography
                variant="h6"
                className={classes.title}
                component={Link}
                to={topPath()}
              >
                AirOne(New UI)
              </Typography>
              <Typography>
                {djangoContext.version}
              </Typography>
          </Box>

					<Box className={classes.menu}>
            {/* FIX ME!!! */}
						<Menu open={open} className={classes.shortcut}>
							<MenuItem>
								<Typography textAlign="center">エンティティ一覧</Typography>
							</MenuItem>
							<MenuItem>
								<Typography textAlign="center">高度な検索</Typography>
							</MenuItem>
							<MenuItem>
								<Typography textAlign="center">ユーザ管理</Typography>
							</MenuItem>
							<MenuItem>
								<Typography textAlign="center">グループ管理</Typography>
							</MenuItem>
						</Menu>
					</Box>

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
              <MenuItem>
                <Link to={userPath(djangoContext.user.id)}>ユーザ設定</Link>
              </MenuItem>
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
          </Box>

          <Box className={classes.search}>
            <TextField
              InputProps={{
                classes: { input: classes.searchTextFieldInput },
              }}
              variant="outlined"
              size="small"
              placeholder="Search…"
              onChange={(e) => setEntryQuery(e.target.value)}
              onKeyPress={handleSearchQuery}
            />
            <Button
              variant="contained"
              component={Link}
              to={`${searchPath()}?entry_name=${entryQuery}`}
            >
              検索
            </Button>
          </Box>
        </Toolbar>
      </AppBar>
    </Box>
  );
};
