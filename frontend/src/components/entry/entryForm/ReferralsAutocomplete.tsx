import { GetEntryAttrReferral } from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  Autocomplete,
  AutocompleteChangeReason,
  AutocompleteInputChangeReason,
  TextField,
} from "@mui/material";
import { FC, useState, useCallback } from "react";

import { aironeApiClient } from "../../../repository/AironeApiClient";

interface Props {
  attrId: number;
  value: GetEntryAttrReferral | GetEntryAttrReferral[] | null;
  handleChange: (
    value: GetEntryAttrReferral | GetEntryAttrReferral[] | null,
  ) => void;
  multiple?: boolean;
  error?: { message?: string };
  isDisabled?: boolean;
}

export const ReferralsAutocomplete: FC<Props> = ({
  attrId,
  value,
  handleChange,
  multiple,
  error,
  isDisabled = false,
}) => {
  const [options, setOptions] = useState<GetEntryAttrReferral[]>([]);
  const [inputValue, setInputValue] = useState<string>(
    !multiple ? ((value as GetEntryAttrReferral | null)?.name ?? "") : "",
  );
  const [loading, setLoading] = useState(false);
  const [hasFetchedInitial, setHasFetchedInitial] = useState(false);

  const fetchInitialOptions = useCallback(async () => {
    if (hasFetchedInitial) return;
    setLoading(true);
    try {
      const result = await aironeApiClient.getEntryAttrReferrals(attrId);
      setOptions(result);
      setHasFetchedInitial(true);
    } finally {
      setLoading(false);
    }
  }, [attrId, hasFetchedInitial]);

  const fetchFilteredOptions = useCallback(
    async (keyword: string) => {
      setLoading(true);
      try {
        const result = await aironeApiClient.getEntryAttrReferrals(
          attrId,
          keyword,
        );
        setOptions(result);
      } finally {
        setLoading(false);
      }
    },
    [attrId],
  );

  const _handleChange = (
    value: GetEntryAttrReferral | GetEntryAttrReferral[] | null,
    reason: AutocompleteChangeReason,
  ) => {
    if (!multiple && value != null && !Array.isArray(value)) {
      setInputValue(value.name);
    }

    if (reason === "clear") {
      handleChange(multiple ? [] : null);
    } else {
      handleChange(value);
    }
  };

  const handleInputChange = (
    _value: string,
    reason: AutocompleteInputChangeReason,
  ) => {
    switch (reason) {
      case "input":
        setInputValue(_value);
        fetchFilteredOptions(_value);
        break;
      case "clear":
        setInputValue("");
        fetchFilteredOptions("");
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
      fullWidth
      multiple={multiple}
      loading={loading}
      options={options}
      value={value ?? (multiple ? [] : null)}
      inputValue={inputValue}
      getOptionLabel={(option) => option?.name ?? "-NOT SET-"}
      isOptionEqualToValue={(option, value) => option.id === value.id}
      onChange={(_e, value, reason) => _handleChange(value, reason)}
      onInputChange={(e, value, reason) => handleInputChange(value, reason)}
      onBlur={handleBlur}
      onOpen={fetchInitialOptions}
      renderInput={(params) => (
        <TextField
          {...params}
          error={error != null}
          helperText={error?.message}
          size="small"
          placeholder={multiple ? "" : "-NOT SET-"}
          disabled={isDisabled}
        />
      )}
    />
  );
};
