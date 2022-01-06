import SearchIcon from "@mui/icons-material/Search";
import { Box, InputAdornment, Typography } from "@mui/material";
import { alpha, TextField, Theme } from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC, useState } from "react";
import { useHistory } from "react-router-dom";

import { searchPath } from "../Routes";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";

const useStyles = makeStyles<Theme>((theme) => ({
  container: {
    display: "flex",
    width: "100%",
    flexDirection: "column",
    alignItems: "center",
  },
  search: {
    display: "flex",
    borderRadius: theme.shape.borderRadius,
    backgroundColor: alpha(theme.palette.common.white, 0.15),
    "&:hover": {
      backgroundColor: alpha(theme.palette.common.white, 0.25),
    },
    margin: theme.spacing(0, 1),
  },
  searchTextFieldInput: {
    background: "#0000000B",
    "&::placeholder": {
      color: "white",
    },
  },
}));

export const Dashboard: FC = () => {
  const classes = useStyles();
  const history = useHistory();

  const [entryQuery, setEntryQuery] = useState("");

  const handleSearchQuery = (event) => {
    if (event.key === "Enter") {
      history.push(`${searchPath()}?entry_name=${entryQuery}`);
    }
  };

  return (
    <Box>
      <AironeBreadcrumbs>
        <Typography color="textPrimary">Top</Typography>
      </AironeBreadcrumbs>

      <Box className={classes.container}>
        <Box className={classes.search} mt="200px" width="600px">
          <TextField
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            variant="outlined"
            size="small"
            placeholder="Search"
            sx={{
              background: "#0000000B",
            }}
            fullWidth={true}
            onChange={(e) => setEntryQuery(e.target.value)}
            onKeyPress={handleSearchQuery}
          />
        </Box>

        <Box
          mt="100px"
          width="600px"
          display="flex"
          flexWrap="wrap"
          gap="25px 40px"
        >
          <Typography flexGrow={1}>Server</Typography>
          <Typography flexGrow={1}>VM</Typography>
          <Typography flexGrow={1}>Network</Typography>
          <Typography flexGrow={1}>aaaaaaaaaaaaaaaaaaaaaa</Typography>
          <Typography flexGrow={1}>bbb</Typography>
          <Typography flexGrow={1}>Server</Typography>
          <Typography flexGrow={1}>VM</Typography>
          <Typography flexGrow={1}>Network</Typography>
          <Typography flexGrow={1}>aaaaaaaaaaaaaaaaaaaaaa</Typography>
          <Typography flexGrow={1}>bbb</Typography>
          <Typography flexGrow={1}>Server</Typography>
          <Typography flexGrow={1}>VM</Typography>
          <Typography flexGrow={1}>Network</Typography>
          <Typography flexGrow={1}>aaaaaaaaaaaaaaaaaaaaaa</Typography>
          <Typography flexGrow={1}>bbb</Typography>
        </Box>
      </Box>
    </Box>
  );
};
