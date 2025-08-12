import { Box, Button, Typography } from "@mui/material";
import { DesktopDatePicker } from "@mui/x-date-pickers";
import React, { FC, useEffect, useState } from "react";

interface DateRangePickerProps {
  initialStart?: string;
  initialEnd?: string;
  onApply: (start: string, end: string) => void;
  onCancel: () => void;
  disabled?: boolean;
}

export const DateRangePicker: FC<DateRangePickerProps> = ({
  initialStart,
  initialEnd,
  onApply,
  onCancel,
  disabled = false,
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
        setValidationError("終了日は開始日以降を指定してください");
        return false;
      }
    }
    setValidationError(null);
    return true;
  };

  const formatDate = (date: Date | null): string => {
    if (!date) return "";
    return new Date(date.getTime() - date.getTimezoneOffset() * 60000)
      .toISOString()
      .split("T")[0];
  };

  const handleApply = () => {
    if (!validateDates()) return;
    onApply(formatDate(draftDates.start), formatDate(draftDates.end));
    setIsEditing(false);
  };

  return (
    <Box>
      <Box display="flex" gap={2} mb={1}>
        <DesktopDatePicker
          format="yyyy/MM/dd"
          label="開始日"
          value={draftDates.start}
          onChange={(date) => handleDateChange("start", date)}
          disabled={disabled}
          slotProps={{
            textField: {
              size: "small",
              fullWidth: true,
            },
          }}
        />
        <DesktopDatePicker
          format="yyyy/MM/dd"
          label="終了日"
          value={draftDates.end}
          onChange={(date) => handleDateChange("end", date)}
          disabled={disabled}
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
