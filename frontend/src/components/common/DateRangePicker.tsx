import { FC } from "react";

import { BaseDateRangePicker } from "./BaseDateRangePicker";

interface DateRangePickerProps {
  initialStart?: string;
  initialEnd?: string;
  onApply: (start: string, end: string) => void;
  onCancel: () => void;
  disabled?: boolean;
}

export const DateRangePicker: FC<DateRangePickerProps> = (props) => {
  return (
    <BaseDateRangePicker {...props} format="yyyy/MM/dd" isDateTime={false} />
  );
};
