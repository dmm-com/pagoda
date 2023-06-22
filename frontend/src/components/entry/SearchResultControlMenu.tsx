import { Check } from "@mui/icons-material";
import {
  Box,
  Button,
  Divider,
  ListItemIcon,
  Menu,
  MenuItem,
  TextField,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useState } from "react";

import { SearchResultsFilterKey } from "./SearchResults";

const StyledTextField = styled(TextField)({
  margin: "8px",
});

const StyledBox = styled(Box)({
  margin: "8px",
});

interface Props {
  attrName: string;
  newAttrsFilter: Record<
    string,
    { filterKey: SearchResultsFilterKey; keyword: string }
  >;
  anchorElem: HTMLButtonElement | null;
  handleClose: (name: string) => void;
  setNewAttrsFilter: (
    filter: Record<
      string,
      { filterKey: SearchResultsFilterKey; keyword: string }
    >
  ) => void;
  handleSelectFilterConditions: (
    attrfilter: Record<
      string,
      { filterKey: SearchResultsFilterKey; keyword: string }
    >
  ) => void;
}

export const SearchResultControlMenu: FC<Props> = ({
  attrName,
  newAttrsFilter,
  anchorElem,
  handleClose,
  setNewAttrsFilter,
  handleSelectFilterConditions,
}) => {
  // const [filterKey, setFilterKey] = useState<SearchResultsFilterKey>(SearchResultsFilterKey.TextContained);
  // const [keyword, setKeyword] = useState("");
  const [keywordRequired, setKeywordRequired] = useState(true);

  console.log(
    "[onix/SearchResultControlMenu(00)] newAttrsFilter: ",
    newAttrsFilter
  );

  const handleClick = (key: SearchResultsFilterKey) => {
    console.log("key", key);
    console.log("setNewAttrsFilter2", {
      ...newAttrsFilter,
      [attrName]: { ...newAttrsFilter[attrName], filterKey: key },
    });
    setKeywordRequired(key === SearchResultsFilterKey.TextContained);
    setNewAttrsFilter({
      ...newAttrsFilter,
      [attrName]: { ...newAttrsFilter[attrName], filterKey: key },
    });

    switch (key) {
      case SearchResultsFilterKey.Empty:
      case SearchResultsFilterKey.NonEmpty:
        handleSelectFilterConditions({
          ...newAttrsFilter,
          [attrName]: { ...newAttrsFilter[attrName], filterKey: key },
        });

      case SearchResultsFilterKey.Cleared:
        handleSelectFilterConditions({
          ...newAttrsFilter,
          [attrName]: {
            ...newAttrsFilter[attrName],
            filterKey: key,
            keyword: "",
          },
        });
    }
  };

  const handleChangeKeyword = (e: any) => {
    setNewAttrsFilter({
      ...newAttrsFilter,
      [attrName]: { ...newAttrsFilter[attrName], keyword: e.target.value },
    });
  };

  const handleKeyPressKeyword = (e: any) => {
    if (e.key === "Enter") {
      handleSelectFilterConditions({
        ...newAttrsFilter,
        [attrName]: { ...newAttrsFilter[attrName], keyword: e.target.value },
      });
    }
  };

  const filterKey =
    newAttrsFilter[attrName].filterKey ?? SearchResultsFilterKey.Cleared;
  const keyword = newAttrsFilter[attrName].keyword ?? "";

  return (
    <Menu
      id={attrName}
      open={Boolean(anchorElem)}
      onClose={() => handleClose(attrName)}
      anchorEl={anchorElem}
    >
      <StyledBox>
        <Button
          variant="outlined"
          fullWidth
          onClick={() => handleClick(SearchResultsFilterKey.Cleared)}
        >
          <Typography>クリア</Typography>
        </Button>
      </StyledBox>
      <Divider />
      <MenuItem onClick={() => handleClick(SearchResultsFilterKey.Empty)}>
        {filterKey == SearchResultsFilterKey.Empty && (
          <ListItemIcon>
            <Check />
          </ListItemIcon>
        )}
        <Typography>空白</Typography>
      </MenuItem>
      <MenuItem onClick={() => handleClick(SearchResultsFilterKey.NonEmpty)}>
        {filterKey == SearchResultsFilterKey.NonEmpty && (
          <ListItemIcon>
            <Check />
          </ListItemIcon>
        )}
        <Typography>空白ではない</Typography>
      </MenuItem>
      <MenuItem
        onClick={() => handleClick(SearchResultsFilterKey.TextContained)}
      >
        {filterKey == SearchResultsFilterKey.TextContained && (
          <ListItemIcon>
            <Check />
          </ListItemIcon>
        )}
        <Typography>次を含むテキスト</Typography>
      </MenuItem>
      <StyledTextField
        size="small"
        placeholder="絞り込みキーワード"
        value={keyword}
        onChange={handleChangeKeyword}
        onKeyPress={handleKeyPressKeyword}
      />
    </Menu>
  );
};
