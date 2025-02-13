import {
  Box,
  Container,
  Grid,
  List,
  ListItem,
  ListItemText,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router";

import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";

import { SearchBox } from "components";
import { CategoryListHeader } from "components/category/CategoryListHeader";
import { aironeApiClient } from "repository/AironeApiClient";
import { entityEntriesPath } from "routes/Routes";
import { normalizeToMatch } from "services";

const StyledContainer = styled(Container)({
  marginTop: "16px",
});

export const DashboardPage: FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // variable to store search query for Category
  const params = new URLSearchParams(location.search);
  const [query, setQuery] = useState<string>(params.get("query") ?? "");

  const [toggle, setToggle] = useState(false);

  const handleChangeQuery = (newQuery?: string) => {
    setQuery(newQuery ?? "");

    navigate({
      pathname: location.pathname,
      search: newQuery ? `?query=${newQuery}` : "",
    });
  };

  const categories = useAsyncWithThrow(async () => {
    return await aironeApiClient.getCategories(1, query);
  }, [query, toggle]);

  return (
    <StyledContainer>
      {/* Context of Category */}
      <Box m="16px">
        <SearchBox
          placeholder="カテゴリを絞り込む"
          defaultValue={query}
          onKeyPress={(e) => {
            e.key === "Enter" &&
              handleChangeQuery(
                normalizeToMatch((e.target as HTMLInputElement).value ?? "")
              );
          }}
        />
      </Box>
      <Grid container spacing={3}>
        {categories.value?.results.map((category) => (
          <Grid item md={4} key={category.id}>
            <List
              subheader={
                <CategoryListHeader
                  category={category}
                  setToggle={() => setToggle(!toggle)}
                />
              }
            >
              <Box sx={{ overflowY: "scroll", maxHeight: 300 }}>
                {category.models.map((models) => (
                  <ListItem
                    button
                    key={models.id}
                    component={Link}
                    to={entityEntriesPath(models.id)}
                  >
                    <ListItemText primary={models.name} />
                  </ListItem>
                ))}
              </Box>
            </List>
          </Grid>
        ))}
      </Grid>
    </StyledContainer>
  );
};
