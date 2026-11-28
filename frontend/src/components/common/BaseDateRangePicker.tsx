import { Box, Button, Typography } from "@mui/material";
import { DateTimePicker, DesktopDatePicker } from "@mui/x-date-pickers";
import { getUnixTime, isValid } from "date-fns";
import { FC, useState } from "react";

import { useTranslation } from "../../hooks/useTranslation";

import {
  parseCalendarDate,
  serializeCalendarDate,
  serializeDateTime,
} from "services/DateUtil";

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
  const { t } = useTranslation();
  function getInitialDates() {
    const parseDate = isDateTime
      ? (value: string) => new Date(value)
      : parseCalendarDate;
    return {
      start: initialStart ? parseDate(initialStart) : null,
      end: initialEnd ? parseDate(initialEnd) : null,
    };
  }

  const [draftDates, setDraftDates] = useState(getInitialDates);
  const [isEditing, setIsEditing] = useState(false);

  // Reset drafts when the initial values change (render-time adjustment
  // instead of an effect; see "You Might Not Need an Effect" in React docs).
  const [prevInitial, setPrevInitial] = useState({
    initialStart,
    initialEnd,
    isDateTime,
  });
  if (
    prevInitial.initialStart !== initialStart ||
    prevInitial.initialEnd !== initialEnd ||
    prevInitial.isDateTime !== isDateTime
  ) {
    setPrevInitial({ initialStart, initialEnd, isDateTime });
    setDraftDates(getInitialDates());
    setIsEditing(false);
  }

  // Existing search URLs can include fractions that the picker does not display.
  const validationError =
    draftDates.start &&
    draftDates.end &&
    getUnixTime(draftDates.start) > getUnixTime(draftDates.end)
      ? isDateTime
        ? t("dateRangePicker.invalidDateTimeRange")
        : t("dateRangePicker.invalidDateRange")
      : null;

  const handleDateChange = (type: "start" | "end", date: Date | null) => {
    setDraftDates((prev) => ({
      ...prev,
      [type]: date,
    }));
    setIsEditing(true);
  };

  const handleApply = () => {
    const { start, end } = draftDates;
    if (!start || !end || !isValid(start) || !isValid(end) || validationError)
      return;
    if (isDateTime) {
      onApply(serializeDateTime(start), serializeDateTime(end));
    } else {
      onApply(serializeCalendarDate(start), serializeCalendarDate(end));
    }
    setIsEditing(false);
  };

  const startLabel = isDateTime
    ? t("dateRangePicker.startDateTime")
    : t("dateRangePicker.startDate");
  const endLabel = isDateTime
    ? t("dateRangePicker.endDateTime")
    : t("dateRangePicker.endDate");

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
            {t("common.cancel")}
          </Button>
          <Button
            variant="contained"
            size="small"
            onClick={handleApply}
            disabled={
              !isValid(draftDates.start) ||
              !isValid(draftDates.end) ||
              !!validationError ||
              disabled
            }
          >
            {t("common.apply")}
          </Button>
        </Box>
      )}
    </Box>
  );
};
