import {
  Box,
  Button,
  Divider,
  Menu,
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
  entryFilter: string;
  anchorElem: HTMLButtonElement | null;
  handleClose: () => void;
  entryFilterDispatcher: any;
  handleSelectFilterConditions: (
    attrfilter:
      | Record<string, { filterKey: SearchResultsFilterKey; keyword: string }>
      | undefined
  ) => void;
}

export const SearchResultControlMenuForEntry: FC<Props> = ({
  entryFilter,
  anchorElem,
  handleClose,
  entryFilterDispatcher,
  handleSelectFilterConditions,
}) => {
  const handleClick = () => {
    handleSelectFilterConditions(undefined);
  };

  const handleKeyPressKeyword = (e: any) => {
    if (e.key === "Enter") {
      handleSelectFilterConditions(undefined);
    }
  };

  return (
    <Menu
      open={Boolean(anchorElem)}
      onClose={() => handleClose()}
      anchorEl={anchorElem}
    >
      <StyledBox>
        <Button variant="outlined" fullWidth onClick={() => handleClick()}>
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
