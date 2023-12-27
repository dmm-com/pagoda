import { AdvancedSearchResultAttrInfoFilterKeyEnum } from "@dmm-com/airone-apiclient-typescript-fetch";
import Check from "@mui/icons-material/Check";
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
import React, { ChangeEvent, Dispatch, FC, useState } from "react";

import { AttrFilter } from "../../services/entry/AdvancedSearch";

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
  referralFilterDispatcher: Dispatch<
    ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  >;
  handleSelectFilterConditions: (
    attrFilter?: AttrFilter,
    overwriteEntryName?: string | undefined,
    overwriteReferral?: string | undefined,
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
      setFilterKey(AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_CONTAINED);
      handleSelectFilterConditions();
    }
  };

  const getDefaultFilterKey = (): AdvancedSearchResultAttrInfoFilterKeyEnum => {
    const params = new URLSearchParams(location.search);

    switch (params.get("referral_name")) {
      case undefined:
        return AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED;
      case "\\":
        return AdvancedSearchResultAttrInfoFilterKeyEnum.EMPTY;
      case "*":
        return AdvancedSearchResultAttrInfoFilterKeyEnum.NON_EMPTY;
      default:
        return AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_CONTAINED;
    }
  };

  const [filterKey, setFilterKey] =
    useState<AdvancedSearchResultAttrInfoFilterKeyEnum>(getDefaultFilterKey());
  const handleFilter = (key: AdvancedSearchResultAttrInfoFilterKeyEnum) => {
    // If the same filter item is selected, the filter is cleared.
    if (filterKey === key) {
      _handleClear();
      return;
    }

    switch (key) {
      case AdvancedSearchResultAttrInfoFilterKeyEnum.EMPTY:
        setFilterKey(AdvancedSearchResultAttrInfoFilterKeyEnum.EMPTY);
        handleSelectFilterConditions(undefined, undefined, "\\");
        break;

      case AdvancedSearchResultAttrInfoFilterKeyEnum.NON_EMPTY:
        setFilterKey(AdvancedSearchResultAttrInfoFilterKeyEnum.NON_EMPTY);
        handleSelectFilterConditions(undefined, undefined, "*");
        break;
    }
  };

  const _handleClear = () => {
    setFilterKey(AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED);
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
      <MenuItem
        onClick={() =>
          handleFilter(AdvancedSearchResultAttrInfoFilterKeyEnum.EMPTY)
        }
      >
        {filterKey === AdvancedSearchResultAttrInfoFilterKeyEnum.EMPTY && (
          <ListItemIcon>
            <Check />
          </ListItemIcon>
        )}
        <Typography>空白</Typography>
      </MenuItem>
      <MenuItem
        onClick={() =>
          handleFilter(AdvancedSearchResultAttrInfoFilterKeyEnum.NON_EMPTY)
        }
      >
        {filterKey === AdvancedSearchResultAttrInfoFilterKeyEnum.NON_EMPTY && (
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
