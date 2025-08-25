import { Box, Button, Typography } from "@mui/material";
import { DateTimePicker, DesktopDatePicker } from "@mui/x-date-pickers";
import { FC, useEffect, useState } from "react";

interface BaseDateRangePickerProps {
  initialStart?: string;
  initialEnd?: string;
  onApply: (start: string, end: string) => void;
  onCancel: () => void;
  disabled?: boolean;
  format?: string;
  ampm?: boolean;
  isDateTime?: boolean;
}

export const BaseDateRangePicker: FC<BaseDateRangePickerProps> = ({
  initialStart,
  initialEnd,
  onApply,
  onCancel,
  disabled = false,
  format = "yyyy/MM/dd",
  ampm = false,
  isDateTime = false,
}) => {
  const [draftDates, setDraftDates] = useState<{
    start: Date | null;
    end: Date | null;
  }>({
    start: initialStart ? new Date(initialStart) : null,
    end: initialEnd ? new Date(initialEnd) : null,
  });
  const [isEditing, setIsEditing] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  useEffect(() => {
    setDraftDates({
      start: initialStart ? new Date(initialStart) : null,
      end: initialEnd ? new Date(initialEnd) : null,
    });
    setIsEditing(false);
    setValidationError(null);
  }, [initialStart, initialEnd]);

  useEffect(() => {
    validateDates();
  }, [draftDates]);

  const handleDateChange = (type: "start" | "end", date: Date | null) => {
    setDraftDates((prev) => ({
      ...prev,
      [type]: date,
    }));
    setIsEditing(true);
  };

  const validateDates = () => {
    if (draftDates.start && draftDates.end) {
      if (draftDates.start > draftDates.end) {
        const errorMessage = isDateTime
          ? "終了日時は開始日時以降を指定してください"
          : "終了日は開始日以降を指定してください";
        setValidationError(errorMessage);
        return false;
      }
    }
    setValidationError(null);
    return true;
  };

  const formatDate = (date: Date | null): string => {
    if (!date) return "";
    if (isDateTime) {
      return new Date(
        date.getTime() - date.getTimezoneOffset() * 60000,
      ).toISOString();
    } else {
      return new Date(date.getTime() - date.getTimezoneOffset() * 60000)
        .toISOString()
        .split("T")[0];
    }
  };

  const handleApply = () => {
    if (!validateDates()) return;
    onApply(formatDate(draftDates.start), formatDate(draftDates.end));
    setIsEditing(false);
  };

  const startLabel = isDateTime ? "開始日時" : "開始日";
  const endLabel = isDateTime ? "終了日時" : "終了日";

  const DatePickerComponent = isDateTime ? DateTimePicker : DesktopDatePicker;

  return (
    <Box>
      <Box display="flex" gap={2} mb={1}>
        <DatePickerComponent
          format={format}
          label={startLabel}
          value={draftDates.start}
          onChange={(date) => handleDateChange("start", date)}
          disabled={disabled}
          {...(isDateTime && { ampm })}
          slotProps={{
            textField: {
              size: "small",
              fullWidth: true,
            },
          }}
        />
        <DatePickerComponent
          format={format}
          label={endLabel}
          value={draftDates.end}
          onChange={(date) => handleDateChange("end", date)}
          disabled={disabled}
          {...(isDateTime && { ampm })}
          slotProps={{
            textField: {
              size: "small",
              fullWidth: true,
            },
          }}
        />
      </Box>
      {validationError && (
        <Typography color="error" variant="body2">
          {validationError}
        </Typography>
      )}
      {isEditing && (
        <Box display="flex" gap={1}>
          <Button variant="outlined" size="small" onClick={onCancel}>
            キャンセル
          </Button>
          <Button
            variant="contained"
            size="small"
            onClick={handleApply}
            disabled={
              !draftDates.start ||
              !draftDates.end ||
              !!validationError ||
              disabled
            }
          >
            適用
          </Button>
        </Box>
      )}
    </Box>
  );
};
