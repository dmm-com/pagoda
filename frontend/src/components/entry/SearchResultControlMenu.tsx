import {
  AdvancedSearchResultAttrInfoFilterKeyEnum,
  EntityAttrIDandName,
  EntryAttributeTypeTypeEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import Check from "@mui/icons-material/Check";
import EditNoteIcon from "@mui/icons-material/EditNote";
import LeaderboardIcon from "@mui/icons-material/Leaderboard";
import {
  Box,
  Button,
  Divider,
  FormControlLabel,
  ListItemIcon,
  Menu,
  MenuItem,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { AdapterDateFns } from "@mui/x-date-pickers/AdapterDateFns";
import { DateTimePicker } from "@mui/x-date-pickers/DateTimePicker";
import { DesktopDatePicker } from "@mui/x-date-pickers/DesktopDatePicker";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { ChangeEvent, FC, KeyboardEvent, useEffect, useState } from "react";

import { useTranslation } from "../../hooks/useTranslation";
import { AttrFilter } from "../../services/entry/AdvancedSearch";
import { DateRangePicker } from "../common/DateRangePicker";
import { DateTimeRangePicker } from "../common/DateTimeRangePicker";

import { AttrStatsModal } from "./AttrStatsModal";
import { handleSelectFilterConditionsParams } from "./SearchResultsTableHead";

const StyledTextField = styled(TextField)({
  margin: "8px",
  width: "calc(100% - 16px)",
});

const StyledBox = styled(Box)({
  margin: "8px",
});

const StyledTypography = styled(Typography)(({}) => ({
  color: "rgba(0, 0, 0, 0.6)",
}));

interface Props {
  attrname: string;
  attrFilter: AttrFilter;
  anchorElem: HTMLButtonElement | null;
  handleUpdateAttrFilter: (filter: AttrFilter) => void;
  handleSelectFilterConditions: (
    params: handleSelectFilterConditionsParams,
  ) => void;
  handleClose: () => void;
  attrType?: number;
  setOpenEditModal: (willOpen: boolean) => void;
  isDisabledEditModal: boolean;
  entityAttrs: EntityAttrIDandName[];
  setEditTargetAttrID?: (attrID: number) => void;
  setEditTargetAttrname?: (attrname: string) => void;
  setEditTargetAttrtype?: (attrtype: number) => void;
  totalCount: number;
}

export const SearchResultControlMenu: FC<Props> = ({
  attrname,
  attrFilter,
  anchorElem,
  handleUpdateAttrFilter,
  handleSelectFilterConditions,
  handleClose,
  attrType,
  setOpenEditModal,
  isDisabledEditModal,
  entityAttrs,
  setEditTargetAttrID,
  setEditTargetAttrname,
  setEditTargetAttrtype,
  totalCount,
}) => {
  const { t } = useTranslation();
  const [openStatsModal, setOpenStatsModal] = useState(false);
  const handleClick = (key: AdvancedSearchResultAttrInfoFilterKeyEnum) => {
    // If the selected filter is the same, remove the filter.
    if (attrFilter.filterKey === key) {
      handleSelectFilterConditions({
        attrFilter: {
          ...attrFilter,
          filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED,
        },
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
          attrFilter: {
            ...attrFilter,
            filterKey: key,
          },
        });
        break;
      case AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED:
        handleSelectFilterConditions({
          attrFilter: {
            ...attrFilter,
            filterKey: key,
            keyword: "",
          },
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
    (e: KeyboardEvent<HTMLDivElement>) => {
      if (e.key === "Enter") {
        handleSelectFilterConditions({
          attrFilter: {
            ...attrFilter,
            filterKey,
          },
        });
      }
    };

  const filterKey =
    attrFilter?.filterKey ?? AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED;
  const keyword = attrFilter?.keyword ?? "";

  // State management for the date range selection
  const [isRange, setIsRange] = useState(false);

  // Set the initial state
  useEffect(() => {
    if (keyword && keyword.includes("~")) {
      setIsRange(true);
    } else {
      setIsRange(false);
    }
  }, [keyword]);

  return (
    <>
      <Menu
        open={Boolean(anchorElem)}
        onClose={handleClose}
        anchorEl={anchorElem}
      >
        <Box pl="16px" py="8px">
          <Typography>
            {t("advancedSearch.controlMenu.filterConditions")}
          </Typography>
        </Box>
        <StyledBox>
          <Button
            variant="outlined"
            fullWidth
            onClick={() =>
              handleClick(AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED)
            }
          >
            <Typography>{t("advancedSearch.controlMenu.clear")}</Typography>
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
          <Typography>{t("advancedSearch.controlMenu.empty")}</Typography>
        </MenuItem>
        <MenuItem
          onClick={() =>
            handleClick(AdvancedSearchResultAttrInfoFilterKeyEnum.NON_EMPTY)
          }
        >
          {filterKey ===
            AdvancedSearchResultAttrInfoFilterKeyEnum.NON_EMPTY && (
            <ListItemIcon>
              <Check />
            </ListItemIcon>
          )}
          <Typography>{t("advancedSearch.controlMenu.nonEmpty")}</Typography>
        </MenuItem>
        <MenuItem
          onClick={() =>
            handleClick(AdvancedSearchResultAttrInfoFilterKeyEnum.DUPLICATED)
          }
        >
          {filterKey ==
            AdvancedSearchResultAttrInfoFilterKeyEnum.DUPLICATED && (
            <ListItemIcon>
              <Check />
            </ListItemIcon>
          )}
          <Typography>{t("advancedSearch.controlMenu.duplicated")}</Typography>
        </MenuItem>

        {attrType === EntryAttributeTypeTypeEnum.DATE && (
          <Box>
            <StyledBox display="flex" flexDirection="column">
              <FormControlLabel
                control={
                  <Switch
                    checked={isRange}
                    onChange={() => {
                      setIsRange(!isRange);
                    }}
                    size="small"
                  />
                }
                label={t("advancedSearch.controlMenu.rangeSpecifyDate")}
              />

              <StyledTypography variant="caption">
                {t("advancedSearch.controlMenu.containsDate")}
              </StyledTypography>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                {isRange ? (
                  <DateRangePicker
                    initialStart={
                      keyword.includes("~") ? keyword.split("~")[0] : undefined
                    }
                    initialEnd={
                      keyword.includes("~") ? keyword.split("~")[1] : undefined
                    }
                    onApply={(start, end) => {
                      handleSelectFilterConditions({
                        attrFilter: {
                          ...attrFilter,
                          filterKey:
                            AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_CONTAINED,
                          keyword: `${start}~${end}`,
                        },
                      });
                    }}
                    onCancel={() => {}}
                  />
                ) : (
                  <DesktopDatePicker
                    format="yyyy/MM/dd"
                    value={
                      filterKey ===
                      AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_CONTAINED
                        ? keyword
                          ? new Date(keyword)
                          : null
                        : null
                    }
                    onChange={(date: Date | null) => {
                      const settingDateValue = date
                        ? new Date(
                            date.getTime() - date.getTimezoneOffset() * 60000,
                          )
                            .toISOString()
                            .split("T")[0]
                        : "";
                      handleSelectFilterConditions({
                        attrFilter: {
                          ...attrFilter,
                          filterKey:
                            AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_CONTAINED,
                          keyword: settingDateValue,
                        },
                      });
                    }}
                    slotProps={{
                      textField: {
                        size: "small",
                      },
                    }}
                  />
                )}
              </LocalizationProvider>
            </StyledBox>
            <StyledBox display="flex" flexDirection="column">
              <StyledTypography variant="caption">
                {t("advancedSearch.controlMenu.notContainsDate")}
              </StyledTypography>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                {isRange ? (
                  <DateRangePicker
                    initialStart={
                      keyword.includes("~") ? keyword.split("~")[0] : undefined
                    }
                    initialEnd={
                      keyword.includes("~") ? keyword.split("~")[1] : undefined
                    }
                    onApply={(start, end) => {
                      handleSelectFilterConditions({
                        attrFilter: {
                          ...attrFilter,
                          filterKey:
                            AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_NOT_CONTAINED,
                          keyword: `${start}~${end}`,
                        },
                      });
                    }}
                    onCancel={() => {}}
                  />
                ) : (
                  <DesktopDatePicker
                    format="yyyy/MM/dd"
                    value={
                      filterKey ===
                      AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_NOT_CONTAINED
                        ? keyword
                          ? new Date(keyword)
                          : null
                        : null
                    }
                    onChange={(date: Date | null) => {
                      const settingDateValue = date
                        ? new Date(
                            date.getTime() - date.getTimezoneOffset() * 60000,
                          )
                            .toISOString()
                            .split("T")[0]
                        : "";
                      handleSelectFilterConditions({
                        attrFilter: {
                          ...attrFilter,
                          filterKey:
                            AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_NOT_CONTAINED,
                          keyword: settingDateValue,
                        },
                      });
                    }}
                    slotProps={{
                      textField: {
                        size: "small",
                      },
                    }}
                  />
                )}
              </LocalizationProvider>
            </StyledBox>
          </Box>
        )}

        {attrType === EntryAttributeTypeTypeEnum.DATETIME && (
          <Box>
            <StyledBox display="flex" flexDirection="column">
              <FormControlLabel
                control={
                  <Switch
                    checked={isRange}
                    onChange={() => {
                      setIsRange(!isRange);
                    }}
                    size="small"
                  />
                }
                label={t("advancedSearch.controlMenu.rangeSpecify")}
              />

              <StyledTypography variant="caption">
                {t("advancedSearch.controlMenu.containsDateTime")}
              </StyledTypography>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                {isRange ? (
                  <DateTimeRangePicker
                    ampm={false}
                    initialStart={
                      keyword.includes("~") ? keyword.split("~")[0] : undefined
                    }
                    initialEnd={
                      keyword.includes("~") ? keyword.split("~")[1] : undefined
                    }
                    onApply={(start, end) => {
                      handleSelectFilterConditions({
                        attrFilter: {
                          ...attrFilter,
                          filterKey:
                            AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_CONTAINED,
                          keyword: `${start}~${end}`,
                        },
                      });
                    }}
                    onCancel={() => {}}
                  />
                ) : (
                  <DateTimePicker
                    format="yyyy/MM/dd HH:mm"
                    ampm={false}
                    value={
                      filterKey ===
                      AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_CONTAINED
                        ? keyword
                          ? new Date(keyword)
                          : null
                        : null
                    }
                    onAccept={(date: Date | null) => {
                      const settingDateValue = date
                        ? new Date(
                            date.getTime() - date.getTimezoneOffset() * 60000,
                          ).toISOString()
                        : "";
                      handleSelectFilterConditions({
                        attrFilter: {
                          ...attrFilter,
                          filterKey:
                            AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_CONTAINED,
                          keyword: settingDateValue,
                        },
                      });
                    }}
                    slotProps={{
                      textField: {
                        size: "small",
                      },
                    }}
                  />
                )}
              </LocalizationProvider>
            </StyledBox>
            <StyledBox display="flex" flexDirection="column">
              <StyledTypography variant="caption">
                {t("advancedSearch.controlMenu.notContainsDateTime")}
              </StyledTypography>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                {isRange ? (
                  <DateTimeRangePicker
                    ampm={false}
                    initialStart={
                      keyword.includes("~") ? keyword.split("~")[0] : undefined
                    }
                    initialEnd={
                      keyword.includes("~") ? keyword.split("~")[1] : undefined
                    }
                    onApply={(start, end) => {
                      handleSelectFilterConditions({
                        attrFilter: {
                          ...attrFilter,
                          filterKey:
                            AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_NOT_CONTAINED,
                          keyword: `${start}~${end}`,
                        },
                      });
                    }}
                    onCancel={() => {}}
                  />
                ) : (
                  <DateTimePicker
                    format="yyyy/MM/dd HH:mm"
                    ampm={false}
                    value={
                      filterKey ===
                      AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_NOT_CONTAINED
                        ? keyword
                          ? new Date(keyword)
                          : null
                        : null
                    }
                    onAccept={(date: Date | null) => {
                      const settingDateValue = date
                        ? new Date(
                            date.getTime() - date.getTimezoneOffset() * 60000,
                          ).toISOString()
                        : "";
                      handleSelectFilterConditions({
                        attrFilter: {
                          ...attrFilter,
                          filterKey:
                            AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_NOT_CONTAINED,
                          keyword: settingDateValue,
                        },
                      });
                    }}
                    slotProps={{
                      textField: {
                        size: "small",
                      },
                    }}
                  />
                )}
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
                  attrFilter: {
                    ...attrFilter,
                    filterKey:
                      AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_CONTAINED,
                    keyword: "true",
                  },
                })
              }
            >
              {filterKey ===
                AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_CONTAINED && (
                <ListItemIcon>
                  <Check />
                </ListItemIcon>
              )}
              <Typography>
                {t("advancedSearch.controlMenu.trueOnly")}
              </Typography>
            </MenuItem>
            <MenuItem
              onClick={() =>
                handleSelectFilterConditions({
                  attrFilter: {
                    ...attrFilter,
                    filterKey:
                      AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_NOT_CONTAINED,
                    keyword: "true",
                  },
                })
              }
            >
              {filterKey ===
                AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_NOT_CONTAINED && (
                <ListItemIcon>
                  <Check />
                </ListItemIcon>
              )}
              <Typography>
                {t("advancedSearch.controlMenu.falseOnly")}
              </Typography>
            </MenuItem>
          </Box>
        )}

        {/* default text selector */}
        {attrType !== EntryAttributeTypeTypeEnum.DATE &&
          attrType !== EntryAttributeTypeTypeEnum.BOOLEAN &&
          attrType !== EntryAttributeTypeTypeEnum.DATETIME && (
            <Box>
              <Box>
                <StyledTextField
                  size="small"
                  placeholder={t("advancedSearch.controlMenu.containsText")}
                  value={
                    filterKey ===
                    AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_CONTAINED
                      ? keyword
                      : ""
                  }
                  onChange={handleChangeKeyword(
                    AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_CONTAINED,
                  )}
                  onKeyPress={handleKeyPressKeyword(
                    AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_CONTAINED,
                  )}
                />
              </Box>
              <Box>
                <StyledTextField
                  size="small"
                  placeholder={t("advancedSearch.controlMenu.notContainsText")}
                  value={
                    filterKey ===
                    AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_NOT_CONTAINED
                      ? keyword
                      : ""
                  }
                  onChange={handleChangeKeyword(
                    AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_NOT_CONTAINED,
                  )}
                  onKeyPress={handleKeyPressKeyword(
                    AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_NOT_CONTAINED,
                  )}
                />
              </Box>
            </Box>
          )}
        <Divider />
        <Box pl="16px" py="8px">
          <Typography>
            {t("advancedSearch.controlMenu.otherFunctions")}
          </Typography>
        </Box>
        <StyledBox>
          <Button
            variant="outlined"
            fullWidth
            startIcon={<EditNoteIcon />}
            // Defense-in-depth for #3449: refuse to open the modal when the
            // attribute type is unknown (would cause AttributeValueField to
            // throw "Unknown attribute type: 0").
            disabled={isDisabledEditModal || (attrType ?? 0) === 0}
            onClick={() => {
              setEditTargetAttrID &&
                setEditTargetAttrID(
                  entityAttrs.find((attr) => attr.name === attrname)?.id ?? 0,
                );
              setEditTargetAttrname && setEditTargetAttrname(attrname);
              setEditTargetAttrtype && setEditTargetAttrtype(attrType ?? 0);
              setOpenEditModal(true);
            }}
          >
            <Typography>
              {t("advancedSearch.controlMenu.bulkUpdate")}
            </Typography>
          </Button>
        </StyledBox>
        <StyledBox>
          <Button
            variant="outlined"
            fullWidth
            startIcon={<LeaderboardIcon />}
            onClick={() => {
              handleClose();
              setOpenStatsModal(true);
            }}
          >
            <Typography>{t("advancedSearch.controlMenu.showStats")}</Typography>
          </Button>
        </StyledBox>
      </Menu>
      <AttrStatsModal
        open={openStatsModal}
        onClose={() => setOpenStatsModal(false)}
        attrname={attrname}
        attrType={attrType ?? 0}
        totalCount={totalCount}
      />
    </>
  );
};
