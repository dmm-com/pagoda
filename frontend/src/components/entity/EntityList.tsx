import { EntityList as EntityListInterface } from "@dmm-com/airone-apiclient-typescript-fetch";
import AddIcon from "@mui/icons-material/Add";
import { Box, Button, Grid } from "@mui/material";
import React, { FC, useState } from "react";
import { Link } from "react-router-dom";

import { EntityListCard } from "./EntityListCard";

import { newEntityPath } from "Routes";
import { PaginationFooter } from "components/common/PaginationFooter";
import { SearchBox } from "components/common/SearchBox";
import { normalizeToMatch } from "services/StringUtil";

interface Props {
  entities: EntityListInterface[];
  totalPageCount: number;
  maxRowCount: number;
  page: number;
  changePage: (page: number) => void;
  query?: string;
  handleChangeQuery: (query: string) => void;
  setToggle?: () => void;
}

export const EntityList: FC<Props> = ({
  entities,
  totalPageCount,
  maxRowCount,
  page,
  query,
  changePage,
  handleChangeQuery,
  setToggle,
}) => {
  const [keyword, setKeyword] = useState(query ?? "");

  return (
    <Box>
      {/* This box shows search box and create button */}
      <Box display="flex" justifyContent="space-between" mb="16px">
        <Box width="600px">
          <SearchBox
            placeholder="エンティティを絞り込む"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onKeyPress={(e) => {
              e.key === "Enter" &&
                handleChangeQuery(
                  keyword.length > 0 ? normalizeToMatch(keyword) : ""
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
          <AddIcon /> 新規エンティティを作成
        </Button>
      </Box>

      {/* This box shows each entity Cards */}
      <Grid container spacing={2} id="entity_list">
        {entities.map((entity) => (
          <Grid item xs={4} key={entity.id}>
            <EntityListCard entity={entity} setToggle={setToggle} />
          </Grid>
        ))}
      </Grid>
      <PaginationFooter
        count={entities.length}
        totalPageCount={totalPageCount}
        maxRowCount={maxRowCount}
        page={page}
        changePage={changePage}
      />
    </Box>
  );
};
