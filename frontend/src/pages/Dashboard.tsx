import SearchIcon from "@mui/icons-material/Search";
import { Box, InputAdornment, Typography } from "@mui/material";
import { alpha, TextField, Theme } from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC, useState } from "react";
import { Link, useHistory } from "react-router-dom";
import { useAsync } from "react-use";

import { entityEntriesPath, searchPath } from "../Routes";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import { Loading } from "../components/common/Loading";
import { getEntities } from "../utils/AironeAPIClient";
import { EntityStatus } from "../utils/Constants";

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

  const entities = useAsync(async () => {
    const resp = await getEntities();
    const data = await resp.json();
    return data.entities.filter((e) => e.status & EntityStatus.TOP_LEVEL);
  });

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

        {entities.loading ? (
          <Loading />
        ) : (
          <Box
            mt="100px"
            width="600px"
            display="flex"
            flexWrap="wrap"
            gap="25px 40px"
          >
            {entities.value.map((entity) => (
              <Typography
                color="primary"
                component={Link}
                to={entityEntriesPath(entity.id)}
                style={{ textDecoration: "none" }}
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
