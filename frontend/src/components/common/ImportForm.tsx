import {
  Box,
  Button,
  CircularProgress,
  Input,
  Typography,
} from "@mui/material";
import Encoding from "encoding-japanese";
import { useSnackbar } from "notistack";
import { ChangeEvent, FC, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router";

import {
  isResponseError,
  toReportableNonFieldErrors,
} from "../../services/AironeAPIErrorUtil";

import { ImportPreview, ImportPreviewAction } from "./ImportPreview";
import { ImportPreviewResult } from "./ImportPreviewResult";

import { aironeApiClient } from "repository/AironeApiClient";
import { ImportPreviewParam } from "services/Constants";
import {
  ImportPreviewFailure,
  fetchImportPreviewPage,
  waitForImportPreviews,
} from "services/ImportPreviewJob";

interface Props {
  /** Receives the preview the user approved, when they previewed at all. */
  handleImport: (
    data: string | ArrayBuffer,
    previewJobIds: number[],
  ) => Promise<void>;
  handleCancel?: () => void;
  /**
   * When given, the user can review what the file would change before importing
   * it. The callback starts the preview jobs and returns their ids; this form
   * waits for all of them. Previewing stays optional -- importing directly is
   * always one click away, for users in a hurry or files not worth the wait.
   */
  handlePreview?: (data: string | ArrayBuffer) => Promise<number[]>;
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
  // A ref, not state: the cancel button is on screen before the jobs have been
  // started, and it has to reach the ids the moment they exist.
  const previewJobIds = useRef<number[]>([]);
  const [actions, setActions] = useState<ImportPreviewAction[]>([]);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState<string>();
  const abandoned = useRef(false);
  const { enqueueSnackbar } = useSnackbar();

  // Leaving the form (closing the dialog) has to stop the polling loop, or it
  // would keep asking about a job nobody is waiting for any more. The flag is
  // cleared on mount as well, since StrictMode runs the cleanup once before the
  // real mount and would otherwise leave the form permanently abandoned.
  useEffect(() => {
    abandoned.current = false;
    return () => {
      abandoned.current = true;
    };
  }, []);

  const onChange = (event: ChangeEvent<HTMLInputElement>) => {
    event.target.files && setFile(event.target.files[0]);
    setPreview(undefined);
    previewJobIds.current = [];
    setActions([]);
    setErrorMessage("");
  };

  const reportError = async (e: unknown, fallback: string) => {
    if (e instanceof ImportPreviewFailure) {
      setErrorMessage(e.message);
      enqueueSnackbar(e.message, { variant: "error" });
      return;
    }
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
    setProgress("変更内容を確認しています...");
    try {
      const jobIds = await handlePreview(await readFileAsText(file));
      previewJobIds.current = jobIds;
      setPreview(
        await waitForImportPreviews(jobIds, {
          onProgress: setProgress,
          isAbandoned: () => abandoned.current,
        }),
      );
      setErrorMessage("");
    } catch (e) {
      setPreview(undefined);
      await reportError(e, "変更内容の確認に失敗しました");
    } finally {
      setProcessing(false);
      setProgress(undefined);
    }
  };

  // Filtering and paging re-read the finished jobs; the file is never sent again.
  const readPage = async (
    nextActions: ImportPreviewAction[],
    offset: number,
  ) => {
    setProcessing(true);
    try {
      const page = await fetchImportPreviewPage(previewJobIds.current, {
        action: nextActions,
        offset,
        limit: ImportPreviewParam.MAX_ROW_COUNT,
      });
      setPreview((current) =>
        offset > 0 && current != null
          ? { ...page, rows: [...current.rows, ...page.rows] }
          : page,
      );
    } catch (e) {
      await reportError(e, "変更内容の読み込みに失敗しました");
    } finally {
      setProcessing(false);
    }
  };

  const onChangeActions = async (nextActions: ImportPreviewAction[]) => {
    setActions(nextActions);
    await readPage(nextActions, 0);
  };

  const onLoadMore = () => readPage(actions, preview?.rows.length ?? 0);

  // Previewing a large file takes as long as importing it, so it has to be
  // possible to give up on one -- which is why previews run as cancelable jobs.
  const onDownloadPreview = async () => {
    await Promise.all(
      previewJobIds.current.map((jobId) =>
        aironeApiClient.downloadImportPreview(
          jobId,
          previewJobIds.current.length > 1
            ? `import_preview_${jobId}.csv`
            : "import_preview.csv",
        ),
      ),
    );
  };

  const onCancelPreview = async () => {
    await Promise.all(
      previewJobIds.current.map((jobId) => aironeApiClient.cancelJob(jobId)),
    );
  };

  const onImport = async () => {
    if (!file) {
      return;
    }

    setProcessing(true);
    try {
      await handleImport(await readFileAsText(file), previewJobIds.current);
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

      {processing && progress != null && (
        <Box display="flex" alignItems="center" gap="8px" my="12px">
          <CircularProgress size={16} />
          <Typography variant="body2">{progress}</Typography>
          <Button
            size="small"
            color="info"
            onClick={onCancelPreview}
            data-testid="cancel-import-preview"
          >
            中止
          </Button>
        </Box>
      )}

      {preview && (
        <ImportPreviewResult
          preview={preview}
          actions={actions}
          onChangeActions={onChangeActions}
          onLoadMore={onLoadMore}
          onDownload={onDownloadPreview}
          loading={processing}
        />
      )}

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
