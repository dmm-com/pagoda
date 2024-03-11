import {
  AdvancedSearchResultAttrInfoFilterKeyEnum,
  EntryAttributeTypeTypeEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
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
import { AdapterDateFns } from "@mui/x-date-pickers/AdapterDateFns";
import { DesktopDatePicker } from "@mui/x-date-pickers/DesktopDatePicker";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import React, { ChangeEvent, FC } from "react";

import { AttrFilter } from "../../services/entry/AdvancedSearch";

const StyledTextField = styled(TextField)({
  margin: "8px",
});

const StyledBox = styled(Box)({
  margin: "8px",
});

const StyledTypography = styled(Typography)(({}) => ({
  color: "rgba(0, 0, 0, 0.6)",
}));

interface Props {
  attrFilter: AttrFilter;
  anchorElem: HTMLButtonElement | null;
  handleUpdateAttrFilter: (filter: AttrFilter) => void;
  handleSelectFilterConditions: (attrFilter: AttrFilter) => void;
  handleClose: () => void;
  attrType?: number;
}

export const SearchResultControlMenu: FC<Props> = ({
  attrFilter,
  anchorElem,
  handleUpdateAttrFilter,
  handleSelectFilterConditions,
  handleClose,
  attrType,
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

      {/* date-type specific text selector */}
      {attrType === EntryAttributeTypeTypeEnum.DATE && (
        <Box>
          <StyledBox display="flex" flexDirection="column">
            <StyledTypography variant="caption">次を含む日付</StyledTypography>
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <DesktopDatePicker
                inputFormat="yyyy/MM/dd"
                value={
                  filterKey ===
                  AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_CONTAINED
                    ? keyword
                    : null
                }
                onChange={(date: Date | null) => {
                  let settingDateValue = "";
                  if (date !== null) {
                    settingDateValue = `${date.getFullYear()}-${
                      date.getMonth() + 1
                    }-${date.getDate()}`;
                  }
                  handleSelectFilterConditions({
                    ...attrFilter,
                    filterKey:
                      AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_CONTAINED,
                    keyword: settingDateValue,
                  });
                }}
                renderInput={(params) => (
                  <StyledTextField size="small" {...params} />
                )}
              />
            </LocalizationProvider>
          </StyledBox>
          <StyledBox display="flex" flexDirection="column">
            <StyledTypography variant="caption">
              次を含まない日付
            </StyledTypography>
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <DesktopDatePicker
                inputFormat="yyyy/MM/dd"
                value={
                  filterKey ===
                  AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_NOT_CONTAINED
                    ? keyword
                    : null
                }
                onChange={(date: Date | null) => {
                  let settingDateValue = "";
                  if (date !== null) {
                    settingDateValue = `${date.getFullYear()}-${
                      date.getMonth() + 1
                    }-${date.getDate()}`;
                  }
                  handleSelectFilterConditions({
                    ...attrFilter,
                    filterKey:
                      AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_NOT_CONTAINED,
                    keyword: settingDateValue,
                  });
                }}
                renderInput={(params) => (
                  <StyledTextField size="small" {...params} />
                )}
              />
            </LocalizationProvider>
          </StyledBox>
        </Box>
      )}

      {/* date-type specific text selector */}
      {attrType === EntryAttributeTypeTypeEnum.BOOLEAN && (
        <Box>
          <MenuItem
            onClick={() =>
              handleSelectFilterConditions({
                ...attrFilter,
                filterKey:
                  AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_CONTAINED,
                keyword: "true",
              })
            }
          >
            {filterKey ===
              AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_CONTAINED && (
              <ListItemIcon>
                <Check />
              </ListItemIcon>
            )}
            <Typography>true のみ</Typography>
          </MenuItem>
          <MenuItem
            onClick={() =>
              handleSelectFilterConditions({
                ...attrFilter,
                filterKey:
                  AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_NOT_CONTAINED,
                keyword: "true",
              })
            }
          >
            {filterKey ===
              AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_NOT_CONTAINED && (
              <ListItemIcon>
                <Check />
              </ListItemIcon>
            )}
            <Typography>false のみ</Typography>
          </MenuItem>
        </Box>
      )}

      {/* default text selector */}
      {attrType !== EntryAttributeTypeTypeEnum.DATE &&
        attrType !== EntryAttributeTypeTypeEnum.BOOLEAN && (
          <Box>
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
          </Box>
        )}
    </Menu>
  );
};
