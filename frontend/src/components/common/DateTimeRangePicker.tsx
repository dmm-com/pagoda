import { FC } from "react";

import { BaseDateRangePicker } from "./BaseDateRangePicker";

import { ENTRY_DATETIME_FORMAT } from "services/DateUtil";

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
  format = ENTRY_DATETIME_FORMAT,
  ampm = false,
  ...props
}) => {
  return (
    <BaseDateRangePicker
      {...props}
      format={format}
      ampm={ampm}
      isDateTime={true}
    />
  );
};
