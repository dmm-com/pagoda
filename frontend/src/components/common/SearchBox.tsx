import SearchIcon from "@mui/icons-material/Search";
import { InputAdornment, SxProps, TextField, Theme } from "@mui/material";
import React, { FC } from "react";

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
    <TextField
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
      sx={{
        background: "#F4F4F4",
        "& fieldset": {
          borderColor: "white",
        },
      }}
      fullWidth={true}
      defaultValue={defaultValue}
      value={value}
      onChange={onChange}
      onKeyPress={onKeyPress}
      autoFocus={autoFocus}
    />
  );
};
