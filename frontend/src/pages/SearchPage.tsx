import SearchIcon from "@mui/icons-material/Search";
import {
  Box,
  Typography,
  Container,
  InputAdornment,
  TextField,
  TableCell,
  TableRow,
} from "@mui/material";
import React, { FC, useState } from "react";
import { Link, useHistory, useLocation } from "react-router-dom";
import { useAsync } from "react-use";

import { topPath, searchPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { PaginatedTable } from "components/common/PaginatedTable";
import { getEntrySearch } from "utils/AironeAPIClient";

export const SearchPage: FC = () => {
  const location = useLocation();
  const history = useHistory();

  const params = new URLSearchParams(location.search);
  const query = params.get("query");

  const [searchQuery, setSearchQuery] = useState(query);

  const searchEntries = useAsync(async () => {
    if (query.length > 0) {
      const resp = await getEntrySearch(query);
      const data = await resp.json();
      return data;
    } else {
      return [];
    }
  });

  const handleSearchQuery = (event) => {
    if (event.key === "Enter") {
      history.push(`${searchPath()}?query=${searchQuery}`);
      history.go(0);
    }
  };

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">検索結果</Typography>
      </AironeBreadcrumbs>

      <Container maxWidth="lg">
        <Box width="600px">
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
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={handleSearchQuery}
            value={searchQuery}
          />
        </Box>
        {!searchEntries.loading ? (
          <PaginatedTable
            rows={searchEntries.value}
            tableHeadRow={
              <TableRow>
                <TableCell>
                  <Typography>エントリ名</Typography>
                </TableCell>
              </TableRow>
            }
            tableBodyRowGenerator={(entry: { id: number; name: string }) => (
              <TableRow key={entry.id}>
                <TableCell>
                  {/* TODO link to entry detail page */}
                  <Typography>{entry.name}</Typography>
                </TableCell>
              </TableRow>
            )}
            rowsPerPageOptions={[100, 250, 1000]}
          />
        ) : (
          <Loading />
        )}
      </Container>
    </Box>
  );
};
