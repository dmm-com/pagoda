import AddIcon from "@mui/icons-material/Add";
import {
  Box,
  Button,
  Grid,
  Pagination,
  Stack,
  Typography,
} from "@mui/material";
import React, { FC, useState } from "react";
import { Link, useHistory, useLocation } from "react-router-dom";

import { useAsyncWithThrow } from "../../hooks/useAsyncWithThrow";
import { usePage } from "../../hooks/usePage";
import { normalizeToMatch } from "../../services/StringUtil";

import { EntryListCard } from "./EntryListCard";

import { newEntryPath } from "Routes";
import { Loading } from "components/common/Loading";
import { SearchBox } from "components/common/SearchBox";
import { aironeApiClientV2 } from "repository/AironeApiClientV2";
import { EntryList as ConstEntryList } from "services/Constants";

interface Props {
  entityId: number;
  canCreateEntry?: boolean;
}

export const EntryList: FC<Props> = ({ entityId, canCreateEntry = true }) => {
  const location = useLocation();
  const history = useHistory();

  const [page, changePage] = usePage();

  const params = new URLSearchParams(location.search);

  const [query, setQuery] = useState<string>(params.get("query") ?? "");
  const [keyword, setKeyword] = useState(query ?? "");
  const [toggle, setToggle] = useState(false);

  const entries = useAsyncWithThrow(async () => {
    return await aironeApiClientV2.getEntries(entityId, true, page, query);
  }, [page, query, toggle]);

  const handleChangeQuery = (newQuery?: string) => {
    changePage(1);
    setQuery(newQuery ?? "");

    history.push({
      pathname: location.pathname,
      search: newQuery ? `?query=${newQuery}` : "",
    });
  };

  const totalPageCount = entries.loading
    ? 0
    : Math.ceil((entries.value?.count ?? 0) / ConstEntryList.MAX_ROW_COUNT);

  return (
    <Box>
      {/* This box shows search box and create button */}
      <Box display="flex" justifyContent="space-between" mb="16px">
        <Box width="600px">
          <SearchBox
            placeholder="エントリを絞り込む"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onKeyPress={(e) => {
              e.key === "Enter" &&
                handleChangeQuery(
                  keyword.length > 0 ? normalizeToMatch(keyword) : "",
                );
            }}
          />
        </Box>
        <Button
          color="secondary"
          variant="contained"
          disabled={!canCreateEntry}
          component={Link}
          to={newEntryPath(entityId)}
          sx={{ borderRadius: "24px" }}
        >
          <AddIcon />
          新規エントリを作成
        </Button>
      </Box>

      {/* This box shows each entry Cards */}
      {entries.loading ? (
        <Loading />
      ) : (
        <Grid container spacing={2} id="entry_list">
          {entries.value?.results?.map((entry) => {
            return (
              <Grid item xs={4} key={entry.id}>
                <EntryListCard
                  entityId={entityId}
                  entry={entry}
                  setToggle={() => setToggle(!toggle)}
                />
              </Grid>
            );
          })}
        </Grid>
      )}
      <Box display="flex" justifyContent="center" alignItems="center" my="30px">
        <Typography>
          {ConstEntryList.MAX_ROW_COUNT * (page - 1) + 1}-{" "}
          {Math.min(
            ConstEntryList.MAX_ROW_COUNT * page,
            entries.value?.count ?? 0,
          )}{" "}
          / {entries.value?.count ?? 0} 件
        </Typography>
        <Stack spacing={2}>
          <Pagination
            id="entry_page"
            siblingCount={0}
            boundaryCount={1}
            count={totalPageCount}
            page={page}
            onChange={(_, newPage) => changePage(newPage)}
            color="primary"
          />
        </Stack>
      </Box>
    </Box>
  );
};
