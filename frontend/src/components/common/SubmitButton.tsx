import { Box, Button, CircularProgress } from "@mui/material";
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
  isSubmitting: boolean;
  handleSubmit: React.MouseEventHandler<HTMLButtonElement>;
  handleCancel: React.MouseEventHandler<HTMLButtonElement>;
}

export const SubmitButton: FC<Props> = ({
  name,
  disabled,
  isSubmitting,
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
        {isSubmitting && <CircularProgress size="20px" />}
      </StyledButton>
      <StyledButton variant="contained" color="info" onClick={handleCancel}>
        キャンセル
      </StyledButton>
    </StyledBox>
  );
};
