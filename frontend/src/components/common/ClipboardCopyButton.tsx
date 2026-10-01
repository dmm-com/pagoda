import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { IconButton, Tooltip } from "@mui/material";
import { FC, useState } from "react";

import { useTranslation } from "../../hooks/useTranslation";

interface Props {
  name: string;
}

export const ClipboardCopyButton: FC<Props> = ({ name }) => {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);
  return (
    <Tooltip
      title={copied ? t("clipboard.copied") : t("clipboard.copyName")}
      onClose={() => setCopied(false)}
    >
      <IconButton
        aria-label={t("clipboard.copyName")}
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
