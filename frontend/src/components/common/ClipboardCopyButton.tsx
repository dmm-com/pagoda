import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { IconButton, Tooltip } from "@mui/material";
import { FC, useState } from "react";

interface Props {
  name: string;
}

export const ClipboardCopyButton: FC<Props> = ({ name }) => {
  const [copied, setCopied] = useState(false);
  return (
    <Tooltip
      title={copied ? "名前をコピーしました" : "名前をコピーする"}
      onClose={() => setCopied(false)}
    >
      <IconButton
        aria-label="名前をコピーする"
        onClick={() => {
          global.navigator.clipboard.writeText(name);
          setCopied(true);
          setTimeout(() => setCopied(false), 1000);
        }}
      >
        <ContentCopyIcon fontSize="small" />
      </IconButton>
    </Tooltip>
  );
};
