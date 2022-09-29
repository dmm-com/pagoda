import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import RefreshIcon from "@mui/icons-material/Refresh";
import {
  Box,
  Button,
  Container,
  IconButton,
  Input,
  InputAdornment,
  Paper,
  Table,
  TableContainer,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useState } from "react";
import { CopyToClipboard } from "react-copy-to-clipboard";
import { useHistory } from "react-router-dom";

import { UserPasswordFormModal } from "./UserPasswordFormModal";

import { usersPath } from "Routes";
import { AironeUserProps } from "pages/EditUserPage";
import {
  createUser,
  refreshAccessToken,
  updateUser,
} from "utils/AironeAPIClient";
import { DjangoContext } from "utils/DjangoContext";

interface Props {
  userInfo: AironeUserProps;
  setUserInfo: (userInfo: AironeUserProps) => void;
}

const StyledTableRow = styled(TableRow)(() => ({
  "&:nth-of-type(odd)": {
    backgroundColor: "#607D8B0A",
  },
  "&:last-child td, &:last-child th": {
    border: 0,
  },
}));

const InputBox: FC = ({ children }) => {
  return (
    <Box
      component="form"
      sx={{
        m: 1,
        p: "2px 4px",
        display: "flex",
        alignItems: "center",
        width: "90%",
      }}
    >
      {children}
    </Box>
  );
};

const ElemChangingPassword: FC<Props> = ({ userInfo, setUserInfo }) => {
  const [openModal, setOpenModal] = useState(false);
  const handleOpenModal = () => {
    setOpenModal(true);
  };

  const handleCloseModal = () => {
    setOpenModal(false);
  };

  return (
    <StyledTableRow>
      <TableCell sx={{ width: "400px", wordBreak: "break-word" }}>
        パスワード変更
      </TableCell>
      <TableCell sx={{ width: "750px", p: "0px", wordBreak: "break-word" }}>
        <InputBox>
          <Button variant="contained" onClick={handleOpenModal}>
            パスワードの再設定
          </Button>
          <UserPasswordFormModal
            userId={userInfo.id}
            openModal={openModal}
            onClose={handleCloseModal}
          />
        </InputBox>
      </TableCell>
    </StyledTableRow>
  );
};

const ElemAuthenticationMethod: FC<Props> = ({ userInfo, setUserInfo }) => {
  const djangoContext = DjangoContext.getInstance();

  return (
    <StyledTableRow>
      <TableCell sx={{ width: "400px", wordBreak: "break-word" }}>
        認証方法
      </TableCell>
      <TableCell sx={{ width: "750px", p: "0px", wordBreak: "break-word" }}>
        <InputBox>
          {userInfo.authenticateType == djangoContext.userAuthenticateType.local
            ? "ローカル認証"
            : "LDAP 認証"}
        </InputBox>
      </TableCell>
    </StyledTableRow>
  );
};

const ElemAccessTokenConfiguration: FC<Props> = ({ userInfo, setUserInfo }) => {
  return (
    <StyledTableRow>
      <TableCell sx={{ width: "400px", wordBreak: "break-word" }}>
        アクセストークンの有効期限設定
      </TableCell>
      <TableCell sx={{ width: "750px", p: "0px", wordBreak: "break-word" }}>
        <InputBox>
          <Box sx={{ flexDirecton: "column" }}>
            <Box sx={{ pb: "20px" }}>
              {/* This TextField only allow to accept numeric string */}
              <TextField
                label="With normal TextField"
                id="outlined-start-adornment"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">秒</InputAdornment>
                  ),
                }}
                variant="standard"
                onChange={(e) => {
                  setUserInfo({
                    ...userInfo,
                    token: {
                      ...userInfo.token,
                      lifetime: Number(e.target.value.replace(/[^0-9]/g, "")),
                    },
                  });
                }}
                value={userInfo.token.lifetime}
              />
            </Box>

            <Box>
              <TextField
                disabled
                label="作成日"
                id="outlined-start-adornment"
                variant="standard"
                //value="2022/09/15 11:29:30"
                value={userInfo.token.created}
                InputProps={{ disableUnderline: true }}
              />

              <TextField
                disabled
                label="有効期限"
                id="outlined-start-adornment"
                variant="standard"
                value={
                  userInfo.token.lifetime === 0
                    ? "無期限"
                    : userInfo.token.expire
                }
                InputProps={{ disableUnderline: true }}
              />
            </Box>
          </Box>
        </InputBox>
      </TableCell>
    </StyledTableRow>
  );
};

const ElemAccessToken: FC<Props> = ({ userInfo, setUserInfo }) => {
  const handleRefreshToken = () => {
    const newTokenValue = "(FIXME) new access token";
    // FIXME: call API to get new access token, which is generated by AirOne
    setUserInfo({
      ...userInfo,
      token: {
        ...userInfo.token,
        value: newTokenValue,
      },
    });
  };

  return (
    <StyledTableRow>
      <TableCell sx={{ width: "400px", wordBreak: "break-word" }}>
        アクセストークン
      </TableCell>
      <TableCell sx={{ width: "750px", p: "0px", wordBreak: "break-word" }}>
        <InputBox>
          <Input
            disabled={true}
            sx={{ width: "90%" }}
            placeholder="右側の更新ボタンを押してトークンをリフレッシュさせてください"
            inputProps={{ "aria-label": "search google maps" }}
            value={userInfo.token.value}
          />
          <IconButton type="button" sx={{ p: "10px" }} aria-label="search">
            <CopyToClipboard text={"hoge"}>
              <ContentCopyIcon />
            </CopyToClipboard>
          </IconButton>
          <IconButton
            type="button"
            sx={{ p: "10px" }}
            aria-label="search"
            onClick={handleRefreshToken}
          >
            <RefreshIcon />
          </IconButton>
        </InputBox>
      </TableCell>
    </StyledTableRow>
  );
};

const ElemEmailAddress: FC<Props> = ({ userInfo, setUserInfo }) => {
  return (
    <StyledTableRow>
      <TableCell sx={{ width: "400px", wordBreak: "break-word" }}>
        メールアドレス
      </TableCell>
      <TableCell sx={{ width: "750px", p: "0px", wordBreak: "break-word" }}>
        <InputBox>
          <Input
            type="email"
            placeholder="メールアドレスを入力してください"
            sx={{ width: "100%" }}
            value={userInfo.email}
            onChange={(e) =>
              setUserInfo({
                ...userInfo,
                email: e.target.value,
              })
            }
          />
        </InputBox>
      </TableCell>
    </StyledTableRow>
  );
};

const ElemUserName: FC<Props> = ({ userInfo, setUserInfo }) => {
  return (
    <StyledTableRow>
      <TableCell sx={{ width: "400px", wordBreak: "break-word" }}>
        名前
      </TableCell>
      <TableCell sx={{ width: "750px", p: "0px", wordBreak: "break-word" }}>
        <InputBox>
          <Input
            type="text"
            placeholder="ユーザ名を入力してください"
            sx={{ width: "100%" }}
            value={userInfo.username}
            onChange={(e) => {
              setUserInfo({ ...userInfo, username: e.target.value });
            }}
          />
        </InputBox>
      </TableCell>
    </StyledTableRow>
  );
};

const ElemUserPassword: FC<Props> = ({ userInfo, setUserInfo }) => {
  return (
    <StyledTableRow>
      <TableCell sx={{ width: "400px", wordBreak: "break-word" }}>
        パスワード
      </TableCell>
      <TableCell sx={{ width: "750px", p: "0px", wordBreak: "break-word" }}>
        <InputBox>
          <Input
            type="password"
            placeholder="パスワードを入力してください"
            sx={{ width: "100%" }}
            value={userInfo.password}
            onChange={(e) => {
              setUserInfo({ ...userInfo, password: e.target.value });
            }}
          />
        </InputBox>
      </TableCell>
    </StyledTableRow>
  );
};

export const UserForm: FC<Props> = ({ userInfo, setUserInfo }) => {
  const history = useHistory();

  const isCreateMode = userInfo.id === 0;
  const [password, setPassword] = useState(isCreateMode ? "" : undefined);
  const [tokenLifetime, setTokenLifetime] = useState(userInfo?.token?.lifetime);

  const handleSubmit = (event) => {
    if (isCreateMode) {
      createUser(
        userInfo.username,
        userInfo.email,
        password,
        userInfo.isSuperuser,
        userInfo.token.lifetime
      ).then(() => history.replace(usersPath()));
    } else {
      updateUser(
        userInfo.id,
        userInfo.username,
        userInfo.email,
        userInfo.isSuperuser,
        userInfo.token.lifetime
      ).then(() => history.replace(usersPath()));
    }
    event.preventDefault();
  };

  const handleRefreshAccessToken = async () => {
    await refreshAccessToken();
    history.go(0);
  };

  return (
    <Container maxWidth="lg" sx={{ pt: "50px", pb: "50px" }}>
      <TableContainer component={Paper}>
        <Table className="table table-bordered">
          <TableHead>
            <TableRow sx={{ backgroundColor: "#455A64" }}>
              <TableCell sx={{ color: "#FFFFFF" }}>項目</TableCell>
              <TableCell sx={{ color: "#FFFFFF" }}>内容</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            <ElemUserName userInfo={userInfo} setUserInfo={setUserInfo} />
            <ElemEmailAddress userInfo={userInfo} setUserInfo={setUserInfo} />

            {userInfo.id > 0 ? (
              <>
                {/* Undisplay other user's token information */}
                {userInfo.token && (
                  <ElemAccessToken
                    userInfo={userInfo}
                    setUserInfo={setUserInfo}
                  />
                )}
                {userInfo.token && (
                  <ElemAccessTokenConfiguration
                    userInfo={userInfo}
                    setUserInfo={setUserInfo}
                  />
                )}

                <ElemAuthenticationMethod
                  userInfo={userInfo}
                  setUserInfo={setUserInfo}
                />

                <ElemChangingPassword
                  userInfo={userInfo}
                  setUserInfo={setUserInfo}
                />
              </>
            ) : (
              <ElemUserPassword userInfo={userInfo} setUserInfo={setUserInfo} />
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Container>
  );
};
