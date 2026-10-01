import { zodResolver } from "@hookform/resolvers/zod";
import { Box, Button, Container, Typography } from "@mui/material";
import { useSnackbar } from "notistack";
import { FC, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router";

import { AironeLink } from "components";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Confirmable } from "components/common/Confirmable";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { UserForm } from "components/user/UserForm";
import { UserPasswordFormModal } from "components/user/UserPasswordFormModal";
import { schema, Schema } from "components/user/userForm/UserFormSchema";
import { useFormNotification } from "hooks/useFormNotification";
import { usePageTitle } from "hooks/usePageTitle";
import { usePagodaSWR } from "hooks/usePagodaSWR";
import { usePrompt } from "hooks/usePrompt";
import { useTranslation } from "hooks/useTranslation";
import { useTypedParams } from "hooks/useTypedParams";
import { aironeApiClient } from "repository/AironeApiClient";
import { topPath, usersPath, loginPath } from "routes/Routes";
import { TITLE_TEMPLATES } from "services";
import {
  extractAPIException,
  isResponseError,
} from "services/AironeAPIErrorUtil";
import { ServerContext } from "services/ServerContext";

export const UserEditPage: FC = () => {
  const { userId } = useTypedParams<{ userId?: number }>({ allowEmpty: true });
  const willCreate = userId == null;

  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation();
  const { enqueueSubmitResult } = useFormNotification(
    t("common.target.user"),
    willCreate,
  );
  const {
    data: user,
    isLoading: userLoading,
    mutate: refreshUser,
  } = usePagodaSWR(userId ? ["user", userId] : null, () =>
    aironeApiClient.getUser(userId!),
  );

  // Fill schema-required defaults for optional API fields.
  const formValues: Schema | undefined = useMemo(
    () =>
      user != null
        ? {
            username: user.username,
            email: user.email ?? "",
            isSuperuser: user.isSuperuser ?? false,
            tokenLifetime: user.token?.lifetime ?? 0,
          }
        : undefined,
    [user],
  );

  const {
    formState: { isValid, isDirty, isSubmitting },
    handleSubmit,
    reset,
    setError,
    control,
  } = useForm<Schema>({
    resolver: zodResolver(schema),
    mode: "onBlur",
    // Sync form values when the fetched user arrives. Dirty fields are
    // kept so a background revalidation does not clobber user edits.
    values: formValues,
    resetOptions: { keepDirtyValues: true },
  });

  usePrompt(isDirty && !isSubmitting, t("user.edit.confirmLeave"));

  usePageTitle(
    userLoading ? t("user.edit.loading") : TITLE_TEMPLATES.userEdit,
    {
      prefix:
        user?.username ??
        (willCreate ? t("user.edit.newUserPrefix") : undefined),
    },
  );

  // These state variables and handlers are used for password reset feature
  const [openModal, setOpenModal] = useState(false);
  const handleOpenModal = () => {
    setOpenModal(true);
  };
  const handleCloseModal = () => {
    setOpenModal(false);
  };

  const isCreateMode = useMemo(() => {
    return user?.id == null;
  }, [user]);

  const [isSuperuser, isMyself, isCoUser] = useMemo(() => {
    const serverContext = ServerContext.getInstance();
    return [
      serverContext?.user?.isSuperuser != null &&
        serverContext.user.isSuperuser,
      user?.id != null &&
        serverContext?.user?.id != null &&
        user.id === serverContext.user.id,
      user?.parentUser != null &&
        serverContext?.user?.id != null &&
        user.parentUser === serverContext.user.id,
    ];
  }, [user?.id, user?.parentUser]);

  const handleSubmitOnValid = async (user: Schema) => {
    try {
      if (isCreateMode) {
        await aironeApiClient.createUser(
          user.username,
          user.password ?? "",
          user.email,
          user.isSuperuser,
        );
      } else {
        await aironeApiClient.updateUser(
          userId ?? 0,
          user.username,
          user.email,
          user.isSuperuser,
          user.tokenLifetime,
        );
      }
      if (!isCreateMode) {
        await refreshUser();
        reset(user);
      }
      enqueueSubmitResult(true);
      if (isCreateMode) {
        reset(user);
        navigate(usersPath());
      }
    } catch (e) {
      if (e instanceof Error && isResponseError(e)) {
        await extractAPIException<Schema>(
          e,
          (message) =>
            enqueueSubmitResult(
              false,
              t("user.edit.submitFailureDetail", { message }),
            ),
          (name, message) => {
            setError(name, { type: "custom", message: message });
            enqueueSubmitResult(false);
          },
        );
      } else {
        enqueueSubmitResult(false);
      }
    }
  };

  const handleCancel = () => {
    navigate(usersPath());
  };

  const handleRefreshToken = async () => {
    try {
      if (isCoUser && userId != null) {
        await aironeApiClient.updateUserTokenForCoUser(userId);
      } else {
        await aironeApiClient.updateUserToken();
      }
      refreshUser();
    } catch (e) {
      if (e instanceof Response) {
        const json = await e.json();
        const reason = json["code"];
        enqueueSnackbar(
          t("user.edit.tokenUpdateFailureWithReason", { reason }),
          {
            variant: "error",
          },
        );
      } else {
        enqueueSnackbar(t("user.edit.tokenUpdateFailure"), {
          variant: "error",
        });
      }
    }
  };

  return (
    <Box>
      <AironeBreadcrumbs>
        <Typography component={AironeLink} to={topPath()}>
          Top
        </Typography>
        <Typography component={AironeLink} to={usersPath()}>
          {t("user.list.pageTitle")}
        </Typography>
        <Typography color="textPrimary">{t("user.edit.pageTitle")}</Typography>
      </AironeBreadcrumbs>
      <PageHeader
        title={user != null ? user.username : t("user.edit.newUserTitle")}
        description={user != null ? t("user.edit.description") : undefined}
      >
        <Box display="flex" justifyContent="center">
          <Box mx="4px">
            <Button
              variant="contained"
              color="info"
              disabled={isCreateMode || !(isMyself || isSuperuser || isCoUser)}
              onClick={handleOpenModal}
            >
              {t("user.edit.resetPassword")}
            </Button>
            <UserPasswordFormModal
              userId={user?.id ?? 0}
              openModal={openModal}
              onClose={handleCloseModal}
              onSubmitSuccess={() => {
                enqueueSnackbar(t("user.edit.passwordChanged"), {
                  variant: "success",
                });

                if (user?.id === ServerContext.getInstance()?.user?.id) {
                  navigate(loginPath(), { replace: true });
                } else {
                  navigate(usersPath(), { replace: true });
                }
              }}
            />
          </Box>
          <Box mx="4px">
            <Confirmable
              componentGenerator={(handleOpen) => (
                <Button
                  variant="contained"
                  color="info"
                  disabled={isCreateMode || !(isMyself || isCoUser)}
                  onClick={handleOpen}
                >
                  {t("user.edit.refreshToken")}
                </Button>
              )}
              dialogTitle={t("user.edit.refreshTokenConfirm")}
              onClickYes={() => handleRefreshToken()}
            />
          </Box>
        </Box>
      </PageHeader>

      {userLoading ? (
        <Loading />
      ) : (
        <Container>
          <UserForm
            user={user}
            control={control}
            isCreateMode={isCreateMode}
            isMyself={isMyself}
            isCoUser={isCoUser}
            isSubmittable={isDirty && isValid && !isSubmitting}
            handleSubmit={handleSubmit(handleSubmitOnValid)}
            handleCancel={handleCancel}
          />
        </Container>
      )}
    </Box>
  );
};
