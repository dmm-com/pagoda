import { Check } from "@mui/icons-material";
import {
  ListItemIcon,
  Menu,
  MenuItem,
  TextField,
  Typography,
} from "@mui/material";
import React, { FC, useState } from "react";

import { SearchResultsFilterKey } from "./SearchResults";

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

    if (
      key === SearchResultsFilterKey.Empty ||
      key === SearchResultsFilterKey.NonEmpty
    ) {
      handleSelectFilterConditions({
        ...newAttrsFilter,
        [attrName]: { ...newAttrsFilter[attrName], filterKey: key },
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
    newAttrsFilter[attrName].filterKey ?? SearchResultsFilterKey.TextContained;
  const keyword = newAttrsFilter[attrName].keyword ?? "";

  return (
    <Menu
      id={attrName}
      open={Boolean(anchorElem)}
      onClose={() => handleClose(attrName)}
      anchorEl={anchorElem}
    >
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
      {keywordRequired && (
        <TextField
          placeholder="絞り込みキーワード"
          value={keyword}
          onChange={handleChangeKeyword}
          onKeyPress={handleKeyPressKeyword}
        />
      )}
    </Menu>
  );
};
