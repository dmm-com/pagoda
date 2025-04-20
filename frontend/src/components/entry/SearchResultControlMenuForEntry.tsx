import {
  Box,
  Button,
  Divider,
  Menu,
  TextField,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, KeyboardEvent } from "react";
import type { HintEntryParam as HintEntry } from "../../services/entry/AdvancedSearch";

const StyledBox = styled(Box)({
  margin: "8px",
});

interface Props {
  hintEntry?: HintEntry;
  anchorElem: HTMLButtonElement | null;
  handleClose: () => void;
  hintEntryDispatcher: (entry: Partial<HintEntry>) => void;
  handleSelectFilterConditions: () => void;
  handleClear: () => void;
}

export const SearchResultControlMenuForEntry: FC<Props> = ({
  hintEntry,
  anchorElem,
  handleClose,
  hintEntryDispatcher,
  handleSelectFilterConditions,
  handleClear,
}) => {
  hintEntry = hintEntry ?? { filter_key: 3, keyword: "" };

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
      <StyledBox>
        <Button variant="outlined" fullWidth onClick={() => handleClear()}>
          <Typography>クリア</Typography>
        </Button>
      </StyledBox>
      <Divider />
      <StyledBox>
        <TextField
          size="small"
          placeholder="次を含むテキスト"
          value={hintEntry?.filter_key === 3 ? (hintEntry?.keyword ?? "") : ""}
          onChange={(e) =>
            hintEntryDispatcher({ filter_key: 3, keyword: e.target.value })
          }
          onKeyPress={handleKeyPressKeyword}
        />
      </StyledBox>
      <StyledBox>
        <TextField
          size="small"
          placeholder="次を含まないテキスト"
          value={hintEntry?.filter_key === 4 ? (hintEntry?.keyword ?? "") : ""}
          onChange={(e) =>
            hintEntryDispatcher({ filter_key: 4, keyword: e.target.value })
          }
          onKeyPress={handleKeyPressKeyword}
        />
      </StyledBox>
    </Menu>
  );
};
