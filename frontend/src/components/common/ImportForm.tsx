import { Box, Button, Input, Typography } from "@mui/material";
import Encoding from "encoding-japanese";
import { useSnackbar } from "notistack";
import React, { ChangeEvent, FC, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  isResponseError,
  toReportableNonFieldErrors,
} from "../../services/AironeAPIErrorUtil";

interface Props {
  handleImport: (data: string | ArrayBuffer) => Promise<void>;
  handleCancel?: () => void;
}

export const ImportForm: FC<Props> = ({ handleImport, handleCancel }) => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File>();
  const [errorMessage, setErrorMessage] = useState<string>("");
  const { enqueueSnackbar } = useSnackbar();

  const onChange = (event: ChangeEvent<HTMLInputElement>) => {
    event.target.files && setFile(event.target.files[0]);
  };

  const onClick = async () => {
    if (file) {
      // TODO its better to avoid reading file twice
      const arrayBuffer = await file.arrayBuffer();
      const bytes = new Uint8Array(arrayBuffer);
      const encodingDetection = Encoding.detect(bytes);
      const encoding =
        typeof encodingDetection === "string" ? encodingDetection : "UNICODE";

      const fileReader = new FileReader();
      fileReader.readAsText(file, encoding);

      fileReader.onload = async () => {
        if (fileReader.result == null) {
          return;
        }

        try {
          await handleImport(fileReader.result);
          navigate(0);
        } catch (e) {
          if (e instanceof Error && isResponseError(e)) {
            const reportableError = await toReportableNonFieldErrors(e);
            setErrorMessage(
              `ファイルのアップロードに失敗しました: ${reportableError ?? ""}`
            );
            enqueueSnackbar(
              `ファイルのアップロードに失敗しました: ${reportableError ?? ""}`,
              {
                variant: "error",
              }
            );
          } else {
            setErrorMessage("ファイルのアップロードに失敗しました。");
            enqueueSnackbar("ファイルのアップロードに失敗しました", {
              variant: "error",
            });
          }
        }
      };
    }
  };

  return (
    <Box display="flex" flexDirection="column">
      <Input type="file" onChange={onChange} data-testid="upload-import-file" />

      <Typography color="error" variant="caption" my="4px">
        {errorMessage}
      </Typography>
      <Box display="flex" justifyContent="flex-end">
        <Button
          type="submit"
          variant="contained"
          color="secondary"
          onClick={onClick}
          sx={{ m: "4px" }}
        >
          インポート
        </Button>
        <Button
          variant="contained"
          color="info"
          onClick={handleCancel}
          sx={{ m: "4px" }}
        >
          キャンセル
        </Button>
      </Box>
    </Box>
  );
};
