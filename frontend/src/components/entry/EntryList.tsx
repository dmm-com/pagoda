import AddIcon from "@mui/icons-material/Add";
import { Box, Button } from "@mui/material";
import Grid from "@mui/material/Grid2";
import { FC, Suspense } from "react";
import { Link } from "react-router";

import { EntryListCard } from "./EntryListCard";

import { Loading } from "components/common/Loading";
import { PaginationFooter } from "components/common/PaginationFooter";
import { SearchBox } from "components/common/SearchBox";
import { usePage } from "hooks/usePage";
import { usePagodaSWR } from "hooks/usePagodaSWR";
import { aironeApiClient } from "repository/AironeApiClient";
import { newEntryPath } from "routes/Routes";
import { EntryListParam } from "services/Constants";
import { normalizeToMatch } from "services/StringUtil";

interface Props {
  entityId: number;
  canCreateEntry?: boolean;
}

const EntryListContent: FC<Props> = ({ entityId, canCreateEntry = true }) => {
  const { page, query, changePage, changeQuery } = usePage();

  const { data: entries, mutate: refreshEntries } = usePagodaSWR(
    ["entries", entityId, true, page, query],
    () => aironeApiClient.getEntries(entityId, true, page, query),
    { suspense: true },
  );

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
      <Grid container spacing={2} id="entry_list">
        {entries.results?.map((entry) => {
          return (
            <Grid size={4} key={entry.id}>
              <EntryListCard
                entityId={entityId}
                entry={entry}
                setToggle={() => refreshEntries()}
              />
            </Grid>
          );
        })}
      </Grid>
      <PaginationFooter
        count={entries.count ?? 0}
        maxRowCount={EntryListParam.MAX_ROW_COUNT}
        page={page}
        changePage={changePage}
      />
    </Box>
  );
};

export const EntryList: FC<Props> = ({ entityId, canCreateEntry = true }) => {
  return (
    <Suspense fallback={<Loading />}>
      <EntryListContent entityId={entityId} canCreateEntry={canCreateEntry} />
    </Suspense>
  );
};
