export const getStagedErrorStyle = (hasError: boolean, isDirty: boolean) => ({
  "& .MuiInput-underline": {
    "&:before": {
      borderBottomColor:
        hasError && !isDirty ? "rgba(211, 47, 47, 0.3)" : undefined,
    },
  },
  "& .MuiFormHelperText-root": {
    color: hasError && !isDirty ? "rgba(211, 47, 47, 0.7)" : undefined,
  },
});

export const getStagedHelperTextStyle = (
  hasError: boolean,
  isDirty: boolean,
) => ({
  color: hasError && !isDirty ? "rgba(211, 47, 47, 0.7)" : undefined,
});
