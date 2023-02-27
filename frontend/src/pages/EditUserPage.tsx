import { zodResolver } from "@hookform/resolvers/zod/dist/zod";
import { Box, Typography, Button, Container } from "@mui/material";
import { useSnackbar } from "notistack";
import React, { FC, useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, Prompt } from "react-router-dom";
import { useHistory } from "react-router-dom";
import { useToggle } from "react-use";

import { aironeApiClientV2 } from "../apiclient/AironeApiClientV2";
import { schema, Schema } from "../components/user/UserFormSchema";
import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";
import { useTypedParams } from "../hooks/useTypedParams";
import { ExtractAPIException } from "../services/AironeAPIErrorUtil";
import { DjangoContext } from "../services/DjangoContext";

import { topPath, usersPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Confirmable } from "components/common/Confirmable";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { UserForm } from "components/user/UserForm";
import { UserPasswordFormModal } from "components/user/UserPasswordFormModal";

export const EditUserPage: FC = () => {
  const { userId } = useTypedParams<{ userId: number }>();
  const history = useHistory();
  const { enqueueSnackbar } = useSnackbar();
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

  const user = useAsyncWithThrow(async () => {
    if (userId) {
      return await aironeApiClientV2.getUser(userId);
    }
  }, [userId, shouldRefresh]);

  useEffect(() => {
    !user.loading && reset(user.value);
  }, [user.value]);

  useEffect(() => {
    isSubmitSuccessful && history.push(usersPath());
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
    const djangoContext = DjangoContext.getInstance();
    return [
      djangoContext?.user?.isSuperuser != null &&
        djangoContext.user.isSuperuser,
      user.value?.id != null &&
        djangoContext?.user?.id != null &&
        user.value.id === djangoContext.user.id,
    ];
  }, [user.loading]);

  const handleSubmitOnValid = async (user: Schema) => {
    const operationName = isCreateMode ? "作成" : "更新";

    try {
      if (isCreateMode) {
        await aironeApiClientV2.createUser(
          user.username,
          user.password ?? "",
          user.email,
          user.isSuperuser
        );
      } else {
        await aironeApiClientV2.updateUser(
          userId,
          user.username,
          user.email,
          user.isSuperuser
        );
      }
      enqueueSnackbar(`ユーザの${operationName}に成功しました`, {
        variant: "success",
      });
    } catch (e) {
      if (e instanceof Response) {
        await ExtractAPIException<Schema>(
          e,
          (message) => {
            enqueueSnackbar(
              `ユーザの${operationName}に失敗しました。詳細: "${message}"`,
              {
                variant: "error",
              }
            );
          },
          (name, message) =>
            setError(name, { type: "custom", message: message })
        );
      } else {
        enqueueSnackbar(`ユーザの${operationName}に失敗しました。`, {
          variant: "error",
        });
      }
    }
  };

  const handleCancel = () => {
    history.replace(usersPath());
  };

  const handleRefreshToken = async () => {
    try {
      await aironeApiClientV2.updateUserToken();
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
            isSubmittable={isValid && !isSubmitting && !isSubmitSuccessful}
            handleSubmit={handleSubmit(handleSubmitOnValid)}
            handleCancel={handleCancel}
          />
        </Container>
      )}

      <Prompt
        when={isDirty && !isSubmitSuccessful}
        message="編集した内容は失われてしまいますが、このページを離れてもよろしいですか？"
      />
    </Box>
  );
};
