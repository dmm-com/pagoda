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
  referralFilter: string;
  anchorElem: HTMLButtonElement | null;
  handleClose: () => void;
  referralFilterDispatcher: any;
  handleSelectFilterConditions: (
    attrfilter?:
      | Record<string, { filterKey: SearchResultsFilterKey; keyword: string }>
      | undefined,
    overwriteEntryName?: string | undefined,
    overwriteReferral?: string | undefined
  ) => void;
  handleClear: () => void;
}

export const SearchResultControlMenuForReferral: FC<Props> = ({
  referralFilter,
  anchorElem,
  handleClose,
  referralFilterDispatcher,
  handleSelectFilterConditions,
  handleClear,
}) => {
  const handleKeyPressKeyword = (e: any) => {
    if (e.key === "Enter") {
      setFilterKey(SearchResultsFilterKey.TextContained);
      handleSelectFilterConditions();
    }
  };

  const getDefaultFilterKey = () => {
    const params = new URLSearchParams(location.search);

    switch (params.get("referral_name")) {
      case undefined:
        return SearchResultsFilterKey.Cleared;
      case "\\":
        return SearchResultsFilterKey.Empty;
      case "*":
        return SearchResultsFilterKey.NonEmpty;
      default:
        return SearchResultsFilterKey.TextContained;
    }
  };

  const [filterKey, setFilterKey] = useState<SearchResultsFilterKey>(
    getDefaultFilterKey()
  );
  const handleFilter = (key: SearchResultsFilterKey) => {
    switch (key) {
      case SearchResultsFilterKey.Empty:
        setFilterKey(SearchResultsFilterKey.Empty);
        handleSelectFilterConditions(undefined, undefined, "\\");
        break;

      case SearchResultsFilterKey.NonEmpty:
        setFilterKey(SearchResultsFilterKey.NonEmpty);
        handleSelectFilterConditions(undefined, undefined, "*");
        break;
    }
  };

  const _handleClear = (e: any) => {
    setFilterKey(SearchResultsFilterKey.Cleared);
    handleClear();
  };

  return (
    <Menu
      open={Boolean(anchorElem)}
      onClose={() => handleClose()}
      anchorEl={anchorElem}
    >
      <StyledBox>
        <Button variant="outlined" fullWidth onClick={_handleClear}>
          <Typography>クリア</Typography>
        </Button>
      </StyledBox>
      <Divider />
      <MenuItem onClick={() => handleFilter(SearchResultsFilterKey.Empty)}>
        {filterKey == SearchResultsFilterKey.Empty && (
          <ListItemIcon>
            <Check />
          </ListItemIcon>
        )}
        <Typography>空白</Typography>
      </MenuItem>
      <MenuItem onClick={() => handleFilter(SearchResultsFilterKey.NonEmpty)}>
        {filterKey == SearchResultsFilterKey.NonEmpty && (
          <ListItemIcon>
            <Check />
          </ListItemIcon>
        )}
        <Typography>空白ではない</Typography>
      </MenuItem>
      <StyledTextField
        size="small"
        placeholder="次を含むテキスト"
        value={referralFilter}
        onChange={referralFilterDispatcher}
        onKeyPress={handleKeyPressKeyword}
      />
    </Menu>
  );
};
