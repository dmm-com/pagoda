import { Button, CircularProgress } from "@mui/material";
import { styled } from "@mui/material/styles";
import { FC, MouseEventHandler } from "react";

import { CenterAlignedBox } from "components/common/FlexBox";
import { useTranslation } from "hooks/useTranslation";

const StyledButton = styled(Button)({
  margin: "0 4px",
});

interface Props {
  name: string;
  disabled: boolean;
  isSubmitting: boolean;
  handleSubmit: MouseEventHandler<HTMLButtonElement>;
  handleCancel?: MouseEventHandler<HTMLButtonElement>;
}

export const SubmitButton: FC<Props> = ({
  name,
  disabled,
  isSubmitting,
  handleSubmit,
  handleCancel,
}) => {
  const { t } = useTranslation();
  return (
    <CenterAlignedBox>
      <StyledButton
        variant="contained"
        color="secondary"
        disabled={disabled}
        onClick={handleSubmit}
      >
        {name}
        {isSubmitting && <CircularProgress size="20px" />}
      </StyledButton>
      {handleCancel && (
        <StyledButton variant="contained" color="info" onClick={handleCancel}>
          {t("common.cancel")}
        </StyledButton>
      )}
    </CenterAlignedBox>
  );
};
