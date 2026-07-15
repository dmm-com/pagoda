import { GetEntryAttrReferral } from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  Autocomplete,
  AutocompleteChangeReason,
  AutocompleteInputChangeReason,
  TextField,
} from "@mui/material";
import { FC, useState, useCallback } from "react";

import { aironeApiClient } from "../../../repository/AironeApiClient";

// Accept any object that carries at least id / name — display_label is optional
// and callers may not always provide it (e.g. Trigger/Isolation flows build
// their own picker payload).
type ReferralOption = {
  id: number;
  name: string;
  displayLabel?: string | null;
};

interface Props {
  attrId: number;
  value: ReferralOption | ReferralOption[] | null;
  handleChange: (
    value: GetEntryAttrReferral | GetEntryAttrReferral[] | null,
  ) => void;
  multiple?: boolean;
  error?: { message?: string };
  isDisabled?: boolean;
}

// Returns undefined only when the option itself is nullish, so the caller can
// distinguish "no option selected" from "option with an empty label" via ??.
const labelOf = (o: ReferralOption | null | undefined): string | undefined =>
  o == null ? undefined : (o.displayLabel ?? o.name);

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
    !multiple ? (labelOf(value as ReferralOption | null) ?? "") : "",
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
      setInputValue(labelOf(value) ?? "");
    } else if (multiple) {
      setInputValue("");
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
      setInputValue(labelOf(value) ?? "");
    }
  };

  return (
    <Autocomplete
      fullWidth
      multiple={multiple}
      loading={loading}
      options={options}
      // MUI Autocomplete's value must be structurally compatible with the
      // options type; ReferralOption is a subset of GetEntryAttrReferral
      // (displayLabel is optional here but nullable-required on the API).
      value={
        (value as GetEntryAttrReferral | GetEntryAttrReferral[] | null) ??
        (multiple ? [] : null)
      }
      inputValue={inputValue}
      getOptionLabel={(option) => labelOf(option) ?? "-NOT SET-"}
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
