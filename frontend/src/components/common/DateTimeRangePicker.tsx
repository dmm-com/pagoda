import { Box, Button, Typography } from "@mui/material";
import { DateTimePicker } from "@mui/x-date-pickers";
import React, { FC, useEffect, useState } from "react";

interface DateTimeRangePickerProps {
  initialStart?: string;
  initialEnd?: string;
  onApply: (start: string, end: string) => void;
  onCancel: () => void;
  disabled?: boolean;
  format?: string;
  ampm?: boolean;
}

export const DateTimeRangePicker: FC<DateTimeRangePickerProps> = ({
  initialStart,
  initialEnd,
  onApply,
  onCancel,
  disabled = false,
  format = "yyyy/MM/dd HH:mm",
  ampm = false,
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
        setValidationError("終了日時は開始日時以降を指定してください");
        return false;
      }
    }
    setValidationError(null);
    return true;
  };

  const formatDateTime = (date: Date | null): string => {
    if (!date) return "";
    return new Date(date.getTime() - date.getTimezoneOffset() * 60000)
      .toISOString()
      .slice(0, 16)
      .replace("T", " ");
  };

  const handleApply = () => {
    if (!validateDates()) return;
    onApply(formatDateTime(draftDates.start), formatDateTime(draftDates.end));
    setIsEditing(false);
  };

  return (
    <Box>
      <Box display="flex" gap={2} mb={1}>
        <DateTimePicker
          format={format}
          label="開始日時"
          value={draftDates.start}
          onChange={(date) => handleDateChange("start", date)}
          disabled={disabled}
          ampm={ampm}
          slotProps={{
            textField: {
              size: "small",
              fullWidth: true,
            },
          }}
        />
        <DateTimePicker
          format={format}
          label="終了日時"
          value={draftDates.end}
          onChange={(date) => handleDateChange("end", date)}
          disabled={disabled}
          ampm={ampm}
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
