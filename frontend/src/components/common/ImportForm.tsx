import { Box, Button, Input, Typography } from "@mui/material";
import Encoding from "encoding-japanese";
import { useSnackbar } from "notistack";
import { ChangeEvent, FC, useState } from "react";
import { useNavigate } from "react-router";

import {
  isResponseError,
  toReportableNonFieldErrors,
} from "../../services/AironeAPIErrorUtil";

import { ImportPreview } from "./ImportPreview";
import { ImportPreviewResult } from "./ImportPreviewResult";

interface Props {
  handleImport: (data: string | ArrayBuffer) => Promise<void>;
  handleCancel?: () => void;
  /**
   * When given, the user can review what the file would change before importing
   * it. Previewing stays optional: importing directly is always available, which
   * matters both for users in a hurry and for files too large to preview.
   */
  handlePreview?: (data: string | ArrayBuffer) => Promise<ImportPreview>;
}

// The file is read once and decoded in place. Reading it again through a
// FileReader would only repeat work the ArrayBuffer already gave us.
const readFileAsText = async (file: File): Promise<string> => {
  const bytes = new Uint8Array(await file.arrayBuffer());
  const detected = Encoding.detect(bytes);

  return Encoding.convert(bytes, {
    to: "UNICODE",
    from: typeof detected === "string" ? detected : "AUTO",
    type: "string",
  });
};

export const ImportForm: FC<Props> = ({
  handleImport,
  handleCancel,
  handlePreview,
}) => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File>();
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [preview, setPreview] = useState<ImportPreview>();
  const [processing, setProcessing] = useState(false);
  const { enqueueSnackbar } = useSnackbar();

  const onChange = (event: ChangeEvent<HTMLInputElement>) => {
    event.target.files && setFile(event.target.files[0]);
    setPreview(undefined);
    setErrorMessage("");
  };

  const reportError = async (e: unknown, fallback: string) => {
    if (e instanceof Error && isResponseError(e)) {
      if (e.response.status === 403) {
        setErrorMessage("この操作を行う権限がありません。");
        enqueueSnackbar("この操作を行う権限がありません。", {
          variant: "error",
        });
        return;
      }
      const reportableError = await toReportableNonFieldErrors(e);
      const message = `${fallback}: ${reportableError ?? ""}`;
      setErrorMessage(message);
      enqueueSnackbar(message, { variant: "error" });
      return;
    }
    setErrorMessage(fallback);
    enqueueSnackbar(fallback, { variant: "error" });
  };

  const onPreview = async () => {
    if (!file || handlePreview == null) {
      return;
    }

    setProcessing(true);
    try {
      setPreview(await handlePreview(await readFileAsText(file)));
      setErrorMessage("");
    } catch (e) {
      setPreview(undefined);
      await reportError(e, "変更内容の確認に失敗しました");
    } finally {
      setProcessing(false);
    }
  };

  const onImport = async () => {
    if (!file) {
      return;
    }

    setProcessing(true);
    try {
      await handleImport(await readFileAsText(file));
      navigate(0);
    } catch (e) {
      await reportError(e, "ファイルのアップロードに失敗しました");
    } finally {
      setProcessing(false);
    }
  };

  return (
    <Box display="flex" flexDirection="column">
      <Input type="file" onChange={onChange} data-testid="upload-import-file" />

      {preview && <ImportPreviewResult preview={preview} />}

      <Typography color="error" variant="caption" my="4px">
        {errorMessage}
      </Typography>
      <Box display="flex" justifyContent="flex-end">
        {handlePreview != null && preview == null && (
          <Button
            variant="outlined"
            color="secondary"
            disabled={!file || processing}
            onClick={onPreview}
            sx={{ m: "4px" }}
            data-testid="preview-import-file"
          >
            変更内容を確認
          </Button>
        )}
        <Button
          type="submit"
          variant="contained"
          color="secondary"
          disabled={processing}
          onClick={onImport}
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
