import { PaginatedEntityListList } from "@dmm-com/airone-apiclient-typescript-fetch";
import AddIcon from "@mui/icons-material/Add";
import { Box, Button, Grid } from "@mui/material";
import React, { FC } from "react";
import { Link } from "react-router";

import { EntityListCard } from "./EntityListCard";

import { PaginationFooter } from "components/common/PaginationFooter";
import { SearchBox } from "components/common/SearchBox";
import { newEntityPath } from "routes/Routes";
import { EntityListParam } from "services/Constants";
import { normalizeToMatch } from "services/StringUtil";

interface Props {
  entities: PaginatedEntityListList;
  page: number;
  changePage: (page: number) => void;
  query?: string;
  handleChangeQuery: (query: string) => void;
  setToggle?: () => void;
}

export const EntityList: FC<Props> = ({
  entities,
  page,
  query,
  changePage,
  handleChangeQuery,
  setToggle,
}) => {
  return (
    <Box>
      {/* This box shows search box and create button */}
      <Box display="flex" justifyContent="space-between" mb="16px">
        <Box width="600px">
          <SearchBox
            placeholder="モデルを絞り込む"
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
          variant="contained"
          color="secondary"
          component={Link}
          to={newEntityPath()}
          sx={{ height: "48px", borderRadius: "24px" }}
        >
          <AddIcon /> 新規モデルを作成
        </Button>
      </Box>

      {/* This box shows each entity Cards */}
      <Grid container spacing={2} id="entity_list">
        {entities.results?.map((entity) => (
          <Grid item xs={4} key={entity.id}>
            <EntityListCard entity={entity} setToggle={setToggle} />
          </Grid>
        ))}
      </Grid>
      <PaginationFooter
        count={entities.count ?? 0}
        maxRowCount={EntityListParam.MAX_ROW_COUNT}
        page={page}
        changePage={changePage}
      />
    </Box>
  );
};
