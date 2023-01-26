import { Box, Button } from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";

const StyledBox = styled(Box)({
  display: "flex",
  justifyContent: "center",
});

const StyledButton = styled(Button)({
  margin: "0 4px",
});

interface Props {
  name: string;
  disabled: boolean;
  handleSubmit: React.MouseEventHandler<HTMLButtonElement>;
  handleCancel: React.MouseEventHandler<HTMLButtonElement>;
}

export const SubmitButton: FC<Props> = ({
  name,
  disabled,
  handleSubmit,
  handleCancel,
}) => {
  return (
    <StyledBox>
      <StyledButton
        variant="contained"
        color="secondary"
        disabled={disabled}
        onClick={handleSubmit}
      >
        {name}
      </StyledButton>
      <StyledButton variant="contained" color="info" onClick={handleCancel}>
        キャンセル
      </StyledButton>
    </StyledBox>
  );
};
