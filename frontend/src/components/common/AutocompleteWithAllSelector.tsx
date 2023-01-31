import {
  AutocompleteChangeReason,
  AutocompleteFreeSoloValueMapping,
} from "@mui/base/AutocompleteUnstyled/useAutocomplete";
import {
  Autocomplete,
  Box,
  Checkbox,
  createFilterOptions,
  FilterOptionsState,
} from "@mui/material";
import { AutocompleteProps } from "@mui/material/Autocomplete/Autocomplete";
import React, { HTMLAttributes, SyntheticEvent, useMemo, useRef } from "react";

type SelectorOption = "select-all" | "remove-all";

interface Props<
  T,
  DisableClearable extends boolean | undefined = undefined,
  FreeSolo extends boolean | undefined = undefined
> extends AutocompleteProps<
    T | SelectorOption,
    true,
    DisableClearable,
    FreeSolo
  > {
  selectAllLabel: string;
}

/**
 * An Autocomplete wrapper to inject special option "select-all", "remove-all" to select many options easily
 *
 * @param selectAllLabel
 * @param autocompleteProps
 * @constructor
 */
export const AutocompleteWithAllSelector = <
  T,
  DisableClearable extends boolean | undefined = undefined,
  FreeSolo extends boolean | undefined = undefined
>({
  selectAllLabel,
  ...autocompleteProps
}: Props<T | SelectorOption, DisableClearable, FreeSolo>) => {
  if (!autocompleteProps.multiple) {
    throw new Error(
      "AutocompleteWithAllSelector supports only multiple options"
    );
  }

  const {
    options,
    value,
    onChange,
  }: AutocompleteProps<T | SelectorOption, true, DisableClearable, FreeSolo> =
    autocompleteProps;

  const filterOptionResult = useRef<{
    query: string;
    results: Array<T | SelectorOption>;
  }>({ query: "", results: options as Array<T | SelectorOption> });

  const allSelected = useMemo(() => {
    return options.length === value?.length;
  }, [options, value]);

  const filter = useMemo(() => {
    return createFilterOptions<T | SelectorOption>();
  }, []);

  const handleChange = (
    event: SyntheticEvent,
    value: Array<
      T | AutocompleteFreeSoloValueMapping<FreeSolo> | SelectorOption
    >,
    reason: AutocompleteChangeReason
  ): void => {
    if (onChange == null) return;

    if (value.find((v) => v === "select-all") != null) {
      const newValueBase = value.filter((v) => v !== "select-all");
      const newElements = filterOptionResult.current.results.filter(
        (v) => !newValueBase.includes(v)
      );
      return onChange(event, newValueBase.concat(newElements), reason);
    } else if (value.find((v) => v === "remove-all") != null) {
      return onChange(event, [], reason);
    } else {
      return onChange(event, value, reason);
    }
  };

  const optionRenderer = (
    props: HTMLAttributes<HTMLLIElement>,
    option: T | SelectorOption
  ) => {
    switch (option) {
      case "select-all":
      case "remove-all":
        return (
          <li {...props}>
            <Checkbox checked={allSelected} />
            <Box>{selectAllLabel}</Box>
          </li>
        );
      default:
        return <li {...props}>{option}</li>;
    }
  };

  const filterOptions = (
    options: Array<T | SelectorOption>,
    params: FilterOptionsState<T | SelectorOption>
  ): (T | SelectorOption)[] => {
    const filtered = filter(options, params);

    if (filterOptionResult.current.query !== params.inputValue) {
      filterOptionResult.current = {
        query: params.inputValue,
        results: filtered,
      };
    }

    const allSelector: SelectorOption[] = (() => {
      if (options.length > 0) {
        return (
          allSelected ? ["remove-all"] : ["select-all"]
        ) as SelectorOption[];
      } else {
        return [];
      }
    })();

    return [...allSelector, ...filtered];
  };

  return (
    <Autocomplete
      {...autocompleteProps}
      filterOptions={filterOptions}
      onChange={handleChange}
      renderOption={optionRenderer}
    />
  );
};
