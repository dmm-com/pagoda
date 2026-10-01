import { SnackbarKey, useSnackbar } from "notistack";

import { translate } from "i18n/config";
import { NotificationMessages } from "services/NotificationMessages";

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

  const operationName = willCreate
    ? translate("common.create")
    : translate("common.update");

  return {
    enqueueSubmitResult: (finished: boolean, additionalMessage?: string) => {
      const message = finished
        ? NotificationMessages.operationCompleted(targetName, operationName)
        : NotificationMessages.operationFailed(targetName, operationName);
      return enqueueSnackbar(`${message}${additionalMessage ?? ""}`, {
        variant: finished ? "success" : "error",
      });
    },
  };
};
