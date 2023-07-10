import {
  Box,
  Button,
  Divider,
  Menu,
  TextField,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";

import { AttrsFilter } from "./SearchResults";

const StyledTextField = styled(TextField)({
  margin: "8px",
});

const StyledBox = styled(Box)({
  margin: "8px",
});

interface Props {
  entryFilter: string;
  anchorElem: HTMLButtonElement | null;
  handleClose: () => void;
  entryFilterDispatcher: any;
  handleSelectFilterConditions: (
    attrfilter?: AttrsFilter,
    overwriteEntryName?: string | undefined,
    overwriteReferral?: string | undefined
  ) => void;
  handleClear: () => void;
}

export const SearchResultControlMenuForEntry: FC<Props> = ({
  entryFilter,
  anchorElem,
  handleClose,
  entryFilterDispatcher,
  handleSelectFilterConditions,
  handleClear,
}) => {
  const handleKeyPressKeyword = (e: any) => {
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
      <StyledTextField
        size="small"
        placeholder="次を含むテキスト"
        value={entryFilter}
        onChange={entryFilterDispatcher}
        onKeyPress={handleKeyPressKeyword}
      />
    </Menu>
  );
};
