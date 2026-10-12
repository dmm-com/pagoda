import {
  EntryHint,
  EntryHintFilterKeyEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  Box,
  Button,
  Divider,
  Menu,
  TextField,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { FC, KeyboardEvent } from "react";

import { handleSelectFilterConditionsParams } from "./SearchResultsTableHead";

import { useTranslation } from "hooks/useTranslation";

const StyledBox = styled(Box)({
  margin: "8px",
});

interface Props {
  hintEntry?: EntryHint;
  anchorElem: HTMLButtonElement | null;
  handleClose: () => void;
  hintEntryDispatcher: (entry: Partial<EntryHint>) => void;
  handleSelectFilterConditions: (
    param: handleSelectFilterConditionsParams,
  ) => void;
}

export const SearchResultControlMenuForEntry: FC<Props> = ({
  hintEntry,
  anchorElem,
  handleClose,
  hintEntryDispatcher,
  handleSelectFilterConditions,
}) => {
  const { t } = useTranslation();
  const handleKeyPressKeyword = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Enter") {
      handleSelectFilterConditions({});
    }
  };

  return (
    <Menu
      open={Boolean(anchorElem)}
      onClose={() => handleClose()}
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
          onClick={() => {
            const clearedHintEntry = {
              filterKey: EntryHintFilterKeyEnum.CLEARED,
              keyword: "",
            };
            hintEntryDispatcher(clearedHintEntry);
            handleSelectFilterConditions({
              overwriteHintEntry: clearedHintEntry,
            });
          }}
        >
          <Typography>{t("advancedSearch.controlMenu.clear")}</Typography>
        </Button>
      </StyledBox>
      <Divider />
      <StyledBox>
        <TextField
          size="small"
          placeholder={t("advancedSearch.controlMenu.containsText")}
          value={
            hintEntry?.filterKey === EntryHintFilterKeyEnum.TEXT_CONTAINED
              ? (hintEntry?.keyword ?? "")
              : ""
          }
          onChange={(e) =>
            hintEntryDispatcher({
              filterKey: EntryHintFilterKeyEnum.TEXT_CONTAINED,
              keyword: e.target.value,
            })
          }
          onKeyPress={handleKeyPressKeyword}
        />
      </StyledBox>
      <StyledBox>
        <TextField
          size="small"
          placeholder={t("advancedSearch.controlMenu.notContainsText")}
          value={
            hintEntry?.filterKey === EntryHintFilterKeyEnum.TEXT_NOT_CONTAINED
              ? (hintEntry?.keyword ?? "")
              : ""
          }
          onChange={(e) =>
            hintEntryDispatcher({
              filterKey: EntryHintFilterKeyEnum.TEXT_NOT_CONTAINED,
              keyword: e.target.value,
            })
          }
          onKeyPress={handleKeyPressKeyword}
        />
      </StyledBox>
    </Menu>
  );
};
