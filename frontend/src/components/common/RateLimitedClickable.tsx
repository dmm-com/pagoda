import { Box } from "@mui/material";
import React, { FC, SyntheticEvent, useRef } from "react";

interface Props {
  intervalSec: number;
  onClick: (e: SyntheticEvent) => void;
}

/**
 * A Box enforces caller executes onClock() with the interval sec.
 *
 * @param intervalSec
 * @param onClick
 * @param children
 * @constructor
 */
export const RateLimitedClickable: FC<Props> = ({
  intervalSec,
  onClick,
  children,
}) => {
  const lastProcessingDate = useRef<Date>();

  const handleClick = (e: SyntheticEvent) => {
    const allowedAfter = (() => {
      if (lastProcessingDate.current != null) {
        const date = new Date(lastProcessingDate.current.getTime());
        date.setSeconds(date.getSeconds() + intervalSec);
        return date;
      } else {
        return null;
      }
    })();
    const now = new Date();

    if (allowedAfter != null && now < allowedAfter) {
      return;
    }

    onClick(e);

    lastProcessingDate.current = now;
  };

  return <Box onClick={handleClick}>{children}</Box>;
};
