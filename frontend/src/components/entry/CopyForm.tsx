import { EntryRetrieve } from "@dmm-com/airone-apiclient-typescript-fetch";
import { Box, TextField, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import { FC } from "react";

import { useTranslation } from "hooks/useTranslation";

const SampleBox = styled(Box)({
  width: "100%",
  margin: "80px 0",
  backgroundColor: "#607D8B0A",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
});

const SampleTextField = styled(TextField)({
  margin: "8px 0",
  width: "95%",
});

export interface CopyFormProps {
  entries: string;
  setEntries: (entries: string) => void;
  templateEntry: EntryRetrieve;
}

export const CopyForm: FC<CopyFormProps> = ({
  entries,
  setEntries,
  templateEntry,
}) => {
  const { t } = useTranslation();

  return (
    <>
      <Typography>
        {t("entryForm.copyForm.description", {
          name: templateEntry.name.substring(0, 50),
        })}
      </Typography>
      <TextField
        id="copy-name"
        fullWidth
        minRows={6}
        maxRows={15}
        placeholder={t("entryForm.copyForm.placeholder")}
        multiline
        value={entries}
        onChange={(e) => setEntries(e.target.value)}
        inputProps={{ sx: { resize: "vertical" } }}
      />
      <SampleBox display="flex">
        <Typography variant="h6" mt="24px" color="primary">
          SAMPLE
        </Typography>
        <Typography color="primary">
          {t("entryForm.copyForm.sampleDescription")}
        </Typography>
        <SampleTextField
          multiline
          disabled
          label={t("entryForm.copyForm.placeholder")}
          value="vm0001
vm0002
vm0003
vm0004
vm0005
vm0006"
        />
      </SampleBox>
    </>
  );
};
