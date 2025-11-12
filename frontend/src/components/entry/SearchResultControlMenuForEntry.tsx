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

import { AttrFilter } from "../../services/entry/AdvancedSearch";

const StyledBox = styled(Box)({
  margin: "8px",
});

interface Props {
  hintEntry?: EntryHint;
  anchorElem: HTMLButtonElement | null;
  handleClose: () => void;
  hintEntryDispatcher: (entry: Partial<EntryHint>) => void;
  handleSelectFilterConditions: (
    attrFilter?: AttrFilter,
    overwriteReferral?: string,
    overwriteHintEntry?: EntryHint,
  ) => void;
}

export const SearchResultControlMenuForEntry: FC<Props> = ({
  hintEntry,
  anchorElem,
  handleClose,
  hintEntryDispatcher,
  handleSelectFilterConditions,
}) => {
  const handleKeyPressKeyword = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Enter") {
      handleSelectFilterConditions();
    }
  };

  return (
    <Menu
      open={Boolean(anchorElem)}
      onClose={() => handleClose()}
      anchorEl={anchorElem}
    >
      <Box pl="16px" py="8px">
        <Typography>絞り込み条件</Typography>
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
            handleSelectFilterConditions(
              undefined,
              undefined,
              clearedHintEntry,
            );
          }}
        >
          <Typography>クリア</Typography>
        </Button>
      </StyledBox>
      <Divider />
      <StyledBox>
        <TextField
          size="small"
          placeholder="次を含むテキスト"
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
          placeholder="次を含まないテキスト"
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
