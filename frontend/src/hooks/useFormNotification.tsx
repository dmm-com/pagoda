import { SnackbarKey, useSnackbar } from "notistack";

interface formNotification {
  enqueueSubmitResult: (
    finished: boolean,
    additionalMessage?: string,
  ) => SnackbarKey;
}

/**
 * A hook enqueues common notification message on form page to snackbar.
 *
 */
export const useFormNotification = (
  targetName: string,
  willCreate: boolean,
): formNotification => {
  const { enqueueSnackbar } = useSnackbar();

  const operationName = willCreate ? "作成" : "更新";

  return {
    enqueueSubmitResult: (finished: boolean, additionalMessage?: string) => {
      return enqueueSnackbar(
        `${targetName}の${operationName}が${
          finished ? "完了" : "失敗"
        }しました。${additionalMessage ?? ""}`,
        {
          variant: finished ? "success" : "error",
        },
      );
    },
  };
};
