import SearchIcon from "@mui/icons-material/Search";
import { InputAdornment, SxProps, TextField, Theme } from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";

const StyledTextField = styled(TextField)({
  background: "#F4F4F4",
  "& fieldset": {
    borderColor: "white",
  },
});

interface Props {
  placeholder: string;
  onChange?: React.ChangeEventHandler<HTMLTextAreaElement | HTMLInputElement>;
  onKeyPress?: (e: any) => void;
  value?: string;
  defaultValue?: string;
  inputSx?: SxProps<Theme>;
  autoFocus?: boolean;
}

export const SearchBox: FC<Props> = ({
  placeholder,
  onChange,
  onKeyPress,
  value,
  defaultValue,
  inputSx,
  autoFocus,
}) => {
  return (
    <StyledTextField
      InputProps={{
        startAdornment: (
          <InputAdornment position="start">
            <SearchIcon />
          </InputAdornment>
        ),
        sx: {
          borderRadius: "0px",
          ...inputSx,
        },
      }}
      placeholder={placeholder}
      fullWidth={true}
      defaultValue={defaultValue}
      value={value}
      onChange={onChange}
      onKeyPress={onKeyPress}
      autoFocus={autoFocus}
    />
  );
};
