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

import { AttrsFilter } from "../../services/entry/AdvancedSearch";

import { AdvancedSearchResultAttrInfoFilterKeyEnum } from "@dmm-com/airone-apiclient-typescript-fetch";

const StyledTextField = styled(TextField)({
  margin: "8px",
});

const StyledBox = styled(Box)({
  margin: "8px",
});

interface Props {
  attrName: string;
  attrsFilter: AttrsFilter;
  anchorElem: HTMLButtonElement | null;
  handleClose: (name: string) => void;
  setAttrsFilter: (filter: AttrsFilter) => void;
  handleSelectFilterConditions: (
    attrfilter?: AttrsFilter,
    overwriteEntryName?: string | undefined,
    overwriteReferral?: string | undefined
  ) => void;
}

export const SearchResultControlMenu: FC<Props> = ({
  attrName,
  attrsFilter,
  anchorElem,
  handleClose,
  setAttrsFilter,
  handleSelectFilterConditions,
}) => {
  const handleClick = (key: AdvancedSearchResultAttrInfoFilterKeyEnum) => {
    // If the selected filter is the same, remove the filter.
    if (attrsFilter[attrName].filterKey === key) {
      handleSelectFilterConditions({
        ...attrsFilter,
        [attrName]: {
          ...attrsFilter[attrName],
          filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED,
        },
      });
      return;
    }

    setAttrsFilter({
      ...attrsFilter,
      [attrName]: { ...attrsFilter[attrName], filterKey: key },
    });

    switch (key) {
      case AdvancedSearchResultAttrInfoFilterKeyEnum.DUPLICATED:
      case AdvancedSearchResultAttrInfoFilterKeyEnum.EMPTY:
      case AdvancedSearchResultAttrInfoFilterKeyEnum.NON_EMPTY:
        handleSelectFilterConditions({
          ...attrsFilter,
          [attrName]: { ...attrsFilter[attrName], filterKey: key },
        });

      case AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED:
        handleSelectFilterConditions({
          ...attrsFilter,
          [attrName]: {
            ...attrsFilter[attrName],
            filterKey: key,
            keyword: "",
          },
        });
    }
  };

  const handleChangeKeyword =
    (filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum) =>
    (e: ChangeEvent<HTMLInputElement>) => {
      setAttrsFilter({
        ...attrsFilter,
        [attrName]: {
          ...attrsFilter[attrName],
          keyword: e.target.value,
          filterKey,
        },
      });
    };

  const handleKeyPressKeyword =
    (filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum) =>
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (e.key === "Enter") {
        handleSelectFilterConditions({
          ...attrsFilter,
          [attrName]: {
            ...attrsFilter[attrName],
            filterKey,
          },
        });
      }
    };

  const filterKey =
    attrsFilter[attrName].filterKey ??
    AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED;
  const keyword = attrsFilter[attrName].keyword ?? "";

  return (
    <Menu
      id={attrName}
      open={Boolean(anchorElem)}
      onClose={() => handleClose(attrName)}
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
