import { FC } from "react";

import { BaseDateRangePicker } from "./BaseDateRangePicker";

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
  format = "yyyy/MM/dd HH:mm",
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
