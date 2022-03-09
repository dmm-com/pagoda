import SearchIcon from "@mui/icons-material/Search";
import { InputAdornment, TextField } from "@mui/material";
import React, { FC } from "react";

interface Props {
  placeholder: string;
  onChange: React.ChangeEventHandler<HTMLTextAreaElement | HTMLInputElement>;
  value: string;
}

export const SearchBox: FC<Props> = ({ placeholder, onChange, value }) => {
  return (
    <TextField
      InputProps={{
        startAdornment: (
          <InputAdornment position="start">
            <SearchIcon />
          </InputAdornment>
        ),
      }}
      placeholder={placeholder}
      sx={{
        background: "#0000000B",
        "& fieldset": {
          borderColor: "white",
        },
      }}
      fullWidth={true}
      value={value}
      onChange={onChange}
    />
  );
};
