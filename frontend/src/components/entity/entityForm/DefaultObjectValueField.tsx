import { Autocomplete, CircularProgress, TextField } from "@mui/material";
import { FC, useCallback, useEffect, useMemo, useState } from "react";

import { aironeApiClient } from "repository/AironeApiClient";

type EntryOption = { id: number; name: string };

interface Props {
  value: number | number[] | null | undefined;
  referralEntityIds: number[];
  multiple: boolean;
  disabled: boolean;
  ariaLabel: string;
  onChange: (value: number | number[] | null) => void;
}

export const DefaultObjectValueField: FC<Props> = ({
  value,
  referralEntityIds,
  multiple,
  disabled,
  ariaLabel,
  onChange,
}) => {
  const [options, setOptions] = useState<EntryOption[]>([]);
  const [selected, setSelected] = useState<EntryOption[]>([]);
  const [loading, setLoading] = useState(false);

  const selectedIds = useMemo(
    () => (Array.isArray(value) ? value : value == null ? [] : [value]),
    [value],
  );

  useEffect(() => {
    let active = true;
    const loadSelected = async () => {
      const entries = await Promise.all(
        selectedIds.map(async (id) => {
          try {
            const entry = await aironeApiClient.getEntry(id);
            return { id: entry.id, name: entry.name };
          } catch {
            return { id, name: `#${id}` };
          }
        }),
      );
      if (active) {
        setSelected(entries);
      }
    };
    void loadSelected();
    return () => {
      active = false;
    };
  }, [selectedIds]);

  const fetchOptions = useCallback(
    async (keyword = "") => {
      if (referralEntityIds.length === 0) {
        setOptions([]);
        return;
      }
      setLoading(true);
      try {
        const responses = await Promise.all(
          referralEntityIds.map((entityId) =>
            aironeApiClient.getEntries(entityId, true, 1, keyword),
          ),
        );
        const unique = new Map<number, EntryOption>();
        responses.forEach((response) => {
          response.results.forEach((entry) => {
            unique.set(entry.id, { id: entry.id, name: entry.name });
          });
        });
        setOptions(Array.from(unique.values()));
      } catch {
        setOptions([]);
      } finally {
        setLoading(false);
      }
    },
    [referralEntityIds],
  );

  const commonProps = {
    disabled,
    loading,
    options,
    getOptionLabel: (option: EntryOption) => option.name,
    isOptionEqualToValue: (option: EntryOption, selectedValue: EntryOption) =>
      option.id === selectedValue.id,
    onOpen: () => void fetchOptions(),
    onInputChange: (_event: unknown, inputValue: string, reason: string) => {
      if (reason === "input") {
        void fetchOptions(inputValue);
      }
    },
    renderInput: (params: Parameters<typeof TextField>[0]) => (
      <TextField
        {...params}
        placeholder="デフォルトのアイテム"
        size="small"
        inputProps={{ ...params.inputProps, "aria-label": ariaLabel }}
        InputProps={{
          ...params.InputProps,
          endAdornment: (
            <>
              {loading ? <CircularProgress color="inherit" size={18} /> : null}
              {params.InputProps?.endAdornment}
            </>
          ),
        }}
      />
    ),
  };

  if (multiple) {
    return (
      <Autocomplete
        {...commonProps}
        multiple
        value={selected}
        onChange={(_event, entries) => {
          setSelected(entries);
          onChange(entries.map((entry) => entry.id));
        }}
      />
    );
  }

  return (
    <Autocomplete
      {...commonProps}
      value={selected[0] ?? null}
      onChange={(_event, entry) => {
        setSelected(entry ? [entry] : []);
        onChange(entry?.id ?? null);
      }}
    />
  );
};
