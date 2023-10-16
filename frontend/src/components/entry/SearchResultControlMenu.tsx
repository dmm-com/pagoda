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
import React, { ChangeEvent, FC } from "react";

import { AttrFilter } from "../../services/entry/AdvancedSearch";

const StyledTextField = styled(TextField)({
  margin: "8px",
});

const StyledBox = styled(Box)({
  margin: "8px",
});

interface Props {
  attrFilter: AttrFilter;
  anchorElem: HTMLButtonElement | null;
  handleUpdateAttrFilter: (filter: AttrFilter) => void;
  handleSelectFilterConditions: (attrFilter: AttrFilter) => void;
  handleClose: () => void;
}

export const SearchResultControlMenu: FC<Props> = ({
  attrFilter,
  anchorElem,
  handleUpdateAttrFilter,
  handleSelectFilterConditions,
  handleClose,
}) => {
  const handleClick = (key: AdvancedSearchResultAttrInfoFilterKeyEnum) => {
    // If the selected filter is the same, remove the filter.
    if (attrFilter.filterKey === key) {
      handleSelectFilterConditions({
        ...attrFilter,
        filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED,
      });
      return;
    }

    handleUpdateAttrFilter({
      ...attrFilter,
      filterKey: key,
    });

    switch (key) {
      case AdvancedSearchResultAttrInfoFilterKeyEnum.DUPLICATED:
      case AdvancedSearchResultAttrInfoFilterKeyEnum.EMPTY:
      case AdvancedSearchResultAttrInfoFilterKeyEnum.NON_EMPTY:
        handleSelectFilterConditions({
          ...attrFilter,
          filterKey: key,
        });
        break;
      case AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED:
        handleSelectFilterConditions({
          ...attrFilter,
          filterKey: key,
          keyword: "",
        });
        break;
    }
  };

  const handleChangeKeyword =
    (filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum) =>
    (e: ChangeEvent<HTMLInputElement>) => {
      handleUpdateAttrFilter({
        ...attrFilter,
        keyword: e.target.value,
        filterKey,
      });
    };

  const handleKeyPressKeyword =
    (filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum) =>
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (e.key === "Enter") {
        handleSelectFilterConditions({
          ...attrFilter,
          filterKey,
        });
      }
    };

  const filterKey =
    attrFilter.filterKey ?? AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED;
  const keyword = attrFilter.keyword ?? "";

  return (
    <Menu
      open={Boolean(anchorElem)}
      onClose={handleClose}
      anchorEl={anchorElem}
    >
      <Box pl="16px" py="8px">
        <Typography>絞り込み条件</Typography>
      </Box>
      <StyledBox>
        <Button
          variant="outlined"
          fullWidth
          onClick={() =>
            handleClick(AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED)
          }
        >
          <Typography>クリア</Typography>
        </Button>
      </StyledBox>
      <Divider />
      <MenuItem
        onClick={() =>
          handleClick(AdvancedSearchResultAttrInfoFilterKeyEnum.EMPTY)
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
          handleClick(AdvancedSearchResultAttrInfoFilterKeyEnum.NON_EMPTY)
        }
      >
        {filterKey === AdvancedSearchResultAttrInfoFilterKeyEnum.NON_EMPTY && (
          <ListItemIcon>
            <Check />
          </ListItemIcon>
        )}
        <Typography>空白ではない</Typography>
      </MenuItem>
      <MenuItem
        onClick={() =>
          handleClick(AdvancedSearchResultAttrInfoFilterKeyEnum.DUPLICATED)
        }
      >
        {filterKey == AdvancedSearchResultAttrInfoFilterKeyEnum.DUPLICATED && (
          <ListItemIcon>
            <Check />
          </ListItemIcon>
        )}
        <Typography>重複</Typography>
      </MenuItem>
      <Box>
        <StyledTextField
          size="small"
          placeholder="次を含むテキスト"
          value={
            filterKey ===
            AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_CONTAINED
              ? keyword
              : ""
          }
          onChange={handleChangeKeyword(
            AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_CONTAINED
          )}
          onKeyPress={handleKeyPressKeyword(
            AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_CONTAINED
          )}
        />
      </Box>
      <Box>
        <StyledTextField
          size="small"
          placeholder="次を含まないテキスト"
          value={
            filterKey ===
            AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_NOT_CONTAINED
              ? keyword
              : ""
          }
          onChange={handleChangeKeyword(
            AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_NOT_CONTAINED
          )}
          onKeyPress={handleKeyPressKeyword(
            AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_NOT_CONTAINED
          )}
        />
      </Box>
    </Menu>
  );
};
