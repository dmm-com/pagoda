import { GetEntryAttrReferral } from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  Autocomplete,
  AutocompleteChangeReason,
  AutocompleteInputChangeReason,
  TextField,
} from "@mui/material";
import { FC, useCallback, useEffect, useRef, useState } from "react";

import { aironeApiClient } from "../../../repository/AironeApiClient";

import { fuzzyMatch } from "services/StringUtil";

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
  onRestrictedItemsChange?: (restricted: boolean) => void;
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
  onRestrictedItemsChange,
}) => {
  const [options, setOptions] = useState<GetEntryAttrReferral[]>([]);
  const [inputValue, setInputValue] = useState<string>(
    !multiple ? (labelOf(value as ReferralOption | null) ?? "") : "",
  );
  const [loading, setLoading] = useState(false);
  const initialRequestInFlight = useRef(false);
  const referralRequestId = useRef(0);
  const [hasFetchedInitial, setHasFetchedInitial] = useState(false);
  const [resolvedLabels, setResolvedLabels] = useState<Record<number, string>>(
    {},
  );

  useEffect(() => {
    const selectedValues = Array.isArray(value) ? value : value ? [value] : [];
    // ID-only defaults need an API label before the controlled input can render them.
    // eslint-disable-next-line react-you-might-not-need-an-effect/no-pass-live-state-to-parent
    const unresolved = selectedValues.filter(
      (entry) => !labelOf(entry) && resolvedLabels[entry.id] == null,
    );
    if (unresolved.length === 0) return;

    let active = true;
    void Promise.all(
      unresolved.map(async (entry) => {
        try {
          const resolved = await aironeApiClient.getEntry(entry.id);
          return { id: entry.id, name: resolved.name };
        } catch {
          return { id: entry.id, name: `#${entry.id}` };
        }
      }),
    ).then((entries) => {
      if (!active) return;
      setResolvedLabels((current) => ({
        ...current,
        ...Object.fromEntries(entries.map((entry) => [entry.id, entry.name])),
      }));
      if (!multiple && entries[0]) {
        setInputValue(entries[0].name);
      }
    });

    return () => {
      active = false;
    };
  }, [multiple, resolvedLabels, value]);

  const fetchInitialOptions = useCallback(async () => {
    if (hasFetchedInitial || initialRequestInFlight.current) return;
    initialRequestInFlight.current = true;
    const requestId = ++referralRequestId.current;
    setLoading(true);
    try {
      const result = await aironeApiClient.getEntryAttrReferrals(attrId);
      if (requestId !== referralRequestId.current) return;
      setOptions(result.results);
      onRestrictedItemsChange?.(result.hasRestrictedItems);
      setHasFetchedInitial(true);
    } catch {
      setOptions([]);
    } finally {
      initialRequestInFlight.current = false;
      setLoading(false);
    }
  }, [attrId, hasFetchedInitial]);

  useEffect(() => {
    setHasFetchedInitial(false);
    setOptions([]);
    onRestrictedItemsChange?.(false);
  }, [attrId]);

  const fetchFilteredOptions = useCallback(
    async (keyword: string) => {
      setLoading(true);
      const requestId = ++referralRequestId.current;
      try {
        const result = await aironeApiClient.getEntryAttrReferrals(
          attrId,
          keyword,
        );
        if (requestId !== referralRequestId.current) return;
        setOptions(result.results);
        onRestrictedItemsChange?.(result.hasRestrictedItems);
      } catch {
        setOptions([]);
      } finally {
        setLoading(false);
      }
    },
    [attrId],
  );

  useEffect(() => {
    void fetchInitialOptions();
  }, [fetchInitialOptions]);

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
    <>
      <Autocomplete
        fullWidth
        multiple={multiple}
        disabled={isDisabled}
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
        getOptionLabel={(option) =>
          resolvedLabels[option.id] ?? labelOf(option) ?? "-NOT SET-"
        }
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
    </>
  );
};
