import AddIcon from "@mui/icons-material/Add";
import { Box, Button } from "@mui/material";
import Grid from "@mui/material/Grid2";
import React, { FC, useState } from "react";
import { Link } from "react-router";

import { EntryListCard } from "./EntryListCard";

import { Loading } from "components/common/Loading";
import { PaginationFooter } from "components/common/PaginationFooter";
import { SearchBox } from "components/common/SearchBox";
import { useAsyncWithThrow } from "hooks/useAsyncWithThrow";
import { usePage } from "hooks/usePage";
import { aironeApiClient } from "repository/AironeApiClient";
import { newEntryPath } from "routes/Routes";
import { EntryListParam } from "services/Constants";
import { normalizeToMatch } from "services/StringUtil";

interface Props {
  entityId: number;
  canCreateEntry?: boolean;
}

export const EntryList: FC<Props> = ({ entityId, canCreateEntry = true }) => {
  const { page, query, changePage, changeQuery } = usePage();
  const [toggle, setToggle] = useState(false);

  const entries = useAsyncWithThrow(async () => {
    return await aironeApiClient.getEntries(entityId, true, page, query);
  }, [entityId, page, query, toggle]);

  const handleChangeQuery = changeQuery;

  return (
    <Box>
      {/* This box shows search box and create button */}
      <Box display="flex" justifyContent="space-between" mb="16px">
        <Box width="600px">
          <SearchBox
            placeholder="アイテムを絞り込む"
            defaultValue={query}
            onKeyPress={(e) => {
              e.key === "Enter" &&
                handleChangeQuery(
                  normalizeToMatch((e.target as HTMLInputElement).value ?? ""),
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
          新規アイテムを作成
        </Button>
      </Box>

      {/* This box shows each entry Cards */}
      {entries.loading ? (
        <Loading />
      ) : (
        <Grid container spacing={2} id="entry_list">
          {entries.value?.results?.map((entry) => {
            return (
              <Grid size={4} key={entry.id}>
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
      <PaginationFooter
        count={entries.value?.count ?? 0}
        maxRowCount={EntryListParam.MAX_ROW_COUNT}
        page={page}
        changePage={changePage}
      />
    </Box>
  );
};
