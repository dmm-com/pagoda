import {
  Box,
  Button,
  Divider,
  Menu,
  TextField,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { ChangeEvent, Dispatch, FC, KeyboardEvent } from "react";

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
  entryFilterDispatcher: Dispatch<
    ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  >;
  handleSelectFilterConditions: () => void;
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
