import { zodResolver } from "@hookform/resolvers/zod/dist/zod";
import { Box, Button, Container, Typography } from "@mui/material";
import { useSnackbar } from "notistack";
import { FC, useEffect, useMemo, useState } from "react";
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
  const { enqueueSubmitResult } = useFormNotification("ユーザ", willCreate);
  const {
    formState: { isValid, isDirty, isSubmitting, isSubmitSuccessful },
    handleSubmit,
    reset,
    setError,
    control,
  } = useForm<Schema>({
    resolver: zodResolver(schema),
    mode: "onBlur",
  });

  usePrompt(
    isDirty && !isSubmitSuccessful,
    "編集した内容は失われてしまいますが、このページを離れてもよろしいですか？",
  );

  const {
    data: user,
    isLoading: userLoading,
    mutate: refreshUser,
  } = usePagodaSWR(userId ? ["user", userId] : null, () =>
    aironeApiClient.getUser(userId!),
  );

  useEffect(() => {
    if (!userLoading && user) {
      reset({
        username: user.username,
        email: user.email,
        isSuperuser: user.isSuperuser,
        tokenLifetime: user.token?.lifetime ?? 0,
      });
    }
  }, [user, userLoading, reset]);

  useEffect(() => {
    isSubmitSuccessful && navigate(usersPath());
  }, [isSubmitSuccessful]);

  usePageTitle(userLoading ? "読み込み中..." : TITLE_TEMPLATES.userEdit, {
    prefix: user?.username ?? (willCreate ? "新規作成" : undefined),
  });

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

  const [isSuperuser, isMyself] = useMemo(() => {
    const serverContext = ServerContext.getInstance();
    return [
      serverContext?.user?.isSuperuser != null &&
        serverContext.user.isSuperuser,
      user?.id != null &&
        serverContext?.user?.id != null &&
        user.id === serverContext.user.id,
    ];
  }, [userLoading]);

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
      enqueueSubmitResult(true);
    } catch (e) {
      if (e instanceof Error && isResponseError(e)) {
        await extractAPIException<Schema>(
          e,
          (message) => enqueueSubmitResult(false, `詳細: "${message}"`),
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
      await aironeApiClient.updateUserToken();
      refreshUser();
    } catch (e) {
      if (e instanceof Response) {
        const json = await e.json();
        const reason = json["code"];
        enqueueSnackbar(`Token の更新に失敗しました。詳細: ${reason}`, {
          variant: "error",
        });
      } else {
        enqueueSnackbar(`Token の更新に失敗しました。`, {
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
          ユーザ管理
        </Typography>
        <Typography color="textPrimary">ユーザ情報の設定</Typography>
      </AironeBreadcrumbs>
      <PageHeader
        title={user != null ? user.username : "新規ユーザの作成"}
        description={user != null ? "ユーザ編集" : undefined}
      >
        <Box display="flex" justifyContent="center">
          <Box mx="4px">
            <Button
              variant="contained"
              color="info"
              disabled={isCreateMode || !(isMyself || isSuperuser)}
              onClick={handleOpenModal}
            >
              パスワードの再設定
            </Button>
            <UserPasswordFormModal
              userId={user?.id ?? 0}
              openModal={openModal}
              onClose={handleCloseModal}
              onSubmitSuccess={() => {
                enqueueSnackbar("パスワードを変更しました", {
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
                  disabled={isCreateMode || !isMyself}
                  onClick={handleOpen}
                >
                  Access Token をリフレッシュ
                </Button>
              )}
              dialogTitle="AccessTokenを更新してもよろしいですか？ ※現在入力中の項目はリセットされます"
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
            isSuperuser={isSuperuser}
            isMyself={isMyself}
            isSubmittable={
              isDirty && isValid && !isSubmitting && !isSubmitSuccessful
            }
            handleSubmit={handleSubmit(handleSubmitOnValid)}
            handleCancel={handleCancel}
          />
        </Container>
      )}
    </Box>
  );
};
