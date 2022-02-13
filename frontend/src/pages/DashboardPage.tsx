import SearchIcon from "@mui/icons-material/Search";
import { Box, InputAdornment, Typography } from "@mui/material";
import { alpha, TextField, Theme } from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC, useState } from "react";
import { Link, useHistory } from "react-router-dom";
import { useAsync } from "react-use";

import { entityEntriesPath, searchPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { getEntities } from "utils/AironeAPIClient";

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

const EntityStatus = {
  TOP_LEVEL: 1 << 0,
  CREATING: 1 << 1,
  EDITING: 1 << 2,
};

export const DashboardPage: FC = () => {
  const classes = useStyles();
  const history = useHistory();

  const [entryQuery, setEntryQuery] = useState("");

  const entities = useAsync(async () => {
    const resp = await getEntities();
    const data = await resp.json();
    return data.entities.filter((e) => e.status & EntityStatus.TOP_LEVEL);
  });

  const handleSearchQuery = (event) => {
    if (event.key === "Enter") {
      history.push(`${searchPath()}?query=${entryQuery}`);
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

        {entities.loading ? (
          <Loading />
        ) : (
          <Box
            mt="80px"
            width="600px"
            display="flex"
            flexWrap="wrap"
            gap="25px 40px"
          >
            {entities.value.map((entity, index) => (
              <Typography
                key={index}
                color="primary"
                component={Link}
                to={entityEntriesPath(entity.id)}
                style={{ textDecoration: "none" }}
                flexGrow="1"
              >
                {entity.name}
              </Typography>
            ))}
          </Box>
        )}
      </Box>
    </Box>
  );
};
