import { GetEntryAttrReferral } from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  Autocomplete,
  AutocompleteChangeReason,
  AutocompleteInputChangeReason,
  TextField,
} from "@mui/material";
import React, { FC, useState } from "react";
import { useAsync } from "react-use";

import { aironeApiClientV2 } from "../../../apiclient/AironeApiClientV2";

interface Props {
  attrId: number;
  value: GetEntryAttrReferral | GetEntryAttrReferral[] | null;
  handleChange: (
    value: GetEntryAttrReferral | GetEntryAttrReferral[] | null
  ) => void;
  multiple?: boolean;
  disabled?: boolean;
  error?: { message?: string };
}

export const ReferralsAutocomplete: FC<Props> = ({
  attrId,
  value,
  handleChange,
  multiple,
  disabled,
  error,
}) => {
  const [inputValue, setInputValue] = useState<string>(
    !multiple ? (value as GetEntryAttrReferral | null)?.name ?? "" : ""
  );

  const referrals = useAsync(async () => {
    return await aironeApiClientV2.getEntryAttrReferrals(attrId, inputValue);
  }, [attrId, inputValue]);

  const _handleChange = (
    value: GetEntryAttrReferral | GetEntryAttrReferral[] | null,
    reason: AutocompleteChangeReason
  ) => {
    if (!multiple && value != null && !Array.isArray(value)) {
      setInputValue(value.name);
    }

    if (reason === "clear") {
      if (multiple) {
        handleChange([]);
      } else {
        handleChange(null);
      }
    } else {
      handleChange(value);
    }
  };

  const handleInputChange = (
    _value: string,
    reason: AutocompleteInputChangeReason
  ) => {
    switch (reason) {
      case "input":
        setInputValue(_value);
        break;
      case "clear":
        setInputValue("");
        break;
    }
  };

  const handleBlur = () => {
    if (!multiple && value != null && !Array.isArray(value)) {
      setInputValue(value.name);
    }
  };

  return (
    <Autocomplete
      sx={{ width: "280px" }}
      multiple={multiple}
      disabled={disabled}
      loading={referrals.loading}
      options={referrals.value ?? []}
      value={value}
      inputValue={inputValue}
      getOptionLabel={(option) => option?.name ?? "-NOT SET-"}
      isOptionEqualToValue={(option, value) => option.id === value.id}
      onChange={(_e, value, reason) => _handleChange(value, reason)}
      onInputChange={(e, value, reason) => handleInputChange(value, reason)}
      onBlur={handleBlur}
      renderInput={(params) => (
        <TextField
          {...params}
          error={error != null}
          helperText={error?.message}
          size="small"
          placeholder={multiple ? "" : "-NOT SET-"}
        />
      )}
    />
  );
};
