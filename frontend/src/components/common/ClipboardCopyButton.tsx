import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { ClickAwayListener, IconButton, Tooltip } from "@mui/material";
import React, { FC, useState } from "react";

interface Props {
  name: string;
}

export const ClipboardCopyButton: FC<Props> = ({ name }) => {
  const [open, setOpen] = useState<boolean>(false);
  return (
    <ClickAwayListener onClickAway={() => setOpen(false)}>
      <Tooltip
        title="名前をコピーしました"
        open={open}
        disableHoverListener
        disableFocusListener
      >
        <IconButton
          onClick={() => {
            global.navigator.clipboard.writeText(name);
            setOpen(true);
          }}
        >
          <ContentCopyIcon fontSize="small" />
        </IconButton>
      </Tooltip>
    </ClickAwayListener>
  );
};
