import { zodResolver } from "@hookform/resolvers/zod/dist/zod";
import { Box, Typography, Button, Container } from "@mui/material";
import { useSnackbar } from "notistack";
import React, { FC, useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { useToggle } from "react-use";

import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Confirmable } from "components/common/Confirmable";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { UserForm } from "components/user/UserForm";
import { UserPasswordFormModal } from "components/user/UserPasswordFormModal";
import { schema, Schema } from "components/user/userForm/UserFormSchema";
import { useAsyncWithThrow } from "hooks/useAsyncWithThrow";
import { useFormNotification } from "hooks/useFormNotification";
import { usePrompt } from "hooks/usePrompt";
import { useTypedParams } from "hooks/useTypedParams";
import { aironeApiClient } from "repository/AironeApiClient";
import { topPath, usersPath } from "routes/Routes";
import {
  extractAPIException,
  isResponseError,
} from "services/AironeAPIErrorUtil";
import { ServerContext } from "services/ServerContext";

export const UserEditPage: FC = () => {
  const { userId } = useTypedParams<{ userId?: number }>();
  const willCreate = userId == null;

  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const { enqueueSubmitResult } = useFormNotification("ユーザ", willCreate);
  const [shouldRefresh, toggleShouldRefresh] = useToggle(false);

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
    "編集した内容は失われてしまいますが、このページを離れてもよろしいですか？"
  );

  const user = useAsyncWithThrow(async () => {
    if (userId) {
      return await aironeApiClient.getUser(userId);
    }
  }, [userId, shouldRefresh]);

  useEffect(() => {
    !user.loading && reset(user.value);
  }, [user.value]);

  useEffect(() => {
    isSubmitSuccessful && navigate(usersPath());
  }, [isSubmitSuccessful]);

  // These state variables and handlers are used for password reset feature
  const [openModal, setOpenModal] = useState(false);
  const handleOpenModal = () => {
    setOpenModal(true);
  };
  const handleCloseModal = () => {
    setOpenModal(false);
  };

  const isCreateMode = useMemo(() => {
    return user.value?.id == null;
  }, [user.value]);

  const [isSuperuser, isMyself] = useMemo(() => {
    const serverContext = ServerContext.getInstance();
    return [
      serverContext?.user?.isSuperuser != null &&
        serverContext.user.isSuperuser,
      user.value?.id != null &&
        serverContext?.user?.id != null &&
        user.value.id === serverContext.user.id,
    ];
  }, [user.loading]);

  const handleSubmitOnValid = async (user: Schema) => {
    try {
      if (isCreateMode) {
        await aironeApiClient.createUser(
          user.username,
          user.password ?? "",
          user.email,
          user.isSuperuser
        );
      } else {
        await aironeApiClient.updateUser(
          userId ?? 0,
          user.username,
          user.email,
          user.isSuperuser
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
          }
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
      toggleShouldRefresh();
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
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography component={Link} to={usersPath()}>
          ユーザ管理
        </Typography>
        <Typography color="textPrimary">ユーザ情報の設定</Typography>
      </AironeBreadcrumbs>
      <PageHeader
        title={user.value != null ? user.value.username : "新規ユーザの作成"}
        description={user.value != null ? "ユーザ編集" : undefined}
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
              userId={user.value?.id ?? 0}
              openModal={openModal}
              onClose={handleCloseModal}
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

      {user.loading ? (
        <Loading />
      ) : (
        <Container>
          <UserForm
            user={user.value}
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
