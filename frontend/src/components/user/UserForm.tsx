import {
  UserRetrieve,
  UserRetrieveAuthenticateTypeEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import {
  Box,
  Button,
  Checkbox,
  IconButton,
  InputAdornment,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { useSnackbar } from "notistack";
import {
  BaseSyntheticEvent,
  FC,
  ReactNode,
  useCallback,
  useState,
} from "react";
import { CopyToClipboard } from "react-copy-to-clipboard";
import { Control, Controller } from "react-hook-form";

import { ChangeUserAuthModal } from "./ChangeUserAuthModal";
import { Schema } from "./userForm/UserFormSchema";

import { ServerContext } from "services/ServerContext";

const StyledTableRow = styled(TableRow)(() => ({
  "&:nth-of-type(odd)": {
    backgroundColor: "#607D8B0A",
  },
  "&:last-child td, &:last-child th": {
    border: 0,
  },
}));

interface Props {
  control: Control<Schema>;
}

interface ReadonlyProps {
  user: UserRetrieve;
}

const InputBox: FC<{ children: ReactNode }> = ({ children }) => {
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

const ElemAuthenticationMethod: FC<ReadonlyProps> = ({ user }) => {
  const [openModal, setOpenModal] = useState(false);

  return (
    <StyledTableRow>
      <TableCell sx={{ width: "400px", wordBreak: "break-word" }}>
        認証方法
      </TableCell>
      <TableCell sx={{ width: "750px", p: "0px", wordBreak: "break-word" }}>
        {user.authenticateType ===
        UserRetrieveAuthenticateTypeEnum.AUTH_TYPE_LOCAL ? (
          <Box sx={{ m: 1 }}>
            <Box sx={{ my: 1 }}>ローカル認証</Box>
            <Button variant="outlined" onClick={() => setOpenModal(true)}>
              認証方法をLDAPに変更する
            </Button>
          </Box>
        ) : (
          <InputBox>LDAP 認証</InputBox>
        )}
      </TableCell>

      <ChangeUserAuthModal
        user={user}
        openModal={openModal}
        closeModal={() => setOpenModal(false)}
      />
    </StyledTableRow>
  );
};

const ElemAccessTokenConfiguration: FC<Props & ReadonlyProps> = ({
  control,
  user,
}) => {
  return (
    <StyledTableRow>
      <TableCell sx={{ width: "400px", wordBreak: "break-word" }}>
        アクセストークンの有効期限設定
      </TableCell>
      <TableCell sx={{ width: "750px", p: "0px", wordBreak: "break-word" }}>
        <InputBox>
          {user.token != null ? (
            <Box sx={{ flexDirection: "column", width: "100%" }}>
              <Box sx={{ pb: "20px" }}>
                <Controller
                  name="tokenLifetime"
                  control={control}
                  defaultValue={user.token?.lifetime ?? 0}
                  render={({ field, fieldState: { error } }) => (
                    <TextField
                      {...field}
                      type="number"
                      variant="standard"
                      label="アクセストークンが有効な期間"
                      InputProps={{
                        endAdornment: (
                          <InputAdornment position="end">秒</InputAdornment>
                        ),
                      }}
                      error={error != null}
                      helperText={
                        error?.message ??
                        "※0 を入力した場合は期限は無期限になります"
                      }
                      sx={{ width: "100%" }}
                      data-testid="token-lifetime"
                    />
                  )}
                />
              </Box>

              <Box>
                <TextField
                  variant="standard"
                  label="作成日"
                  id="token-created"
                  InputProps={{ disableUnderline: true, readOnly: true }}
                  value={user.token.created}
                  disabled
                  data-testid="token-created"
                  sx={{ mr: 2 }}
                />

                <TextField
                  variant="standard"
                  label="有効期限"
                  id="token-expire"
                  InputProps={{ disableUnderline: true, readOnly: true }}
                  value={
                    user.token.lifetime === 0 ? "無期限" : user.token.expire
                  }
                  disabled
                  data-testid="token-expire"
                />
              </Box>
            </Box>
          ) : (
            <Box>アクセストークンが発行されていません</Box>
          )}
        </InputBox>
      </TableCell>
    </StyledTableRow>
  );
};

const ElemAccessToken: FC<ReadonlyProps> = ({ user }) => {
  const { enqueueSnackbar } = useSnackbar();

  const handleCopy = useCallback(() => {
    enqueueSnackbar("アクセストークンをクリップボードにコピーしました", {
      variant: "success",
    });
  }, [enqueueSnackbar]);

  return (
    <StyledTableRow>
      <TableCell sx={{ width: "400px", wordBreak: "break-word" }}>
        アクセストークン
      </TableCell>
      <TableCell sx={{ width: "750px", p: "0px", wordBreak: "break-word" }}>
        <InputBox>
          <TextField
            sx={{ width: "100%" }}
            placeholder="「ACCESS TOKEN をリフレッシュ」ボタンを押して発行してください"
            inputProps={{
              "aria-label": "search google maps",
              readOnly: true,
            }}
            value={user.token?.value}
            disabled
          />
          <IconButton type="button" sx={{ p: "10px" }} aria-label="search">
            <CopyToClipboard text={user.token?.value ?? ""} onCopy={handleCopy}>
              <ContentCopyIcon />
            </CopyToClipboard>
          </IconButton>
        </InputBox>
      </TableCell>
    </StyledTableRow>
  );
};

const ElemEmailAddress: FC<Props> = ({ control }) => {
  return (
    <StyledTableRow>
      <TableCell sx={{ width: "400px", wordBreak: "break-word" }}>
        メールアドレス
      </TableCell>
      <TableCell sx={{ width: "750px", p: "0px", wordBreak: "break-word" }}>
        <InputBox>
          <Controller
            name="email"
            control={control}
            defaultValue=""
            render={({ field, fieldState: { error } }) => (
              <TextField
                {...field}
                type="email"
                placeholder="メールアドレスを入力してください"
                error={error != null}
                helperText={error?.message}
                sx={{ width: "100%" }}
              />
            )}
          />
        </InputBox>
      </TableCell>
    </StyledTableRow>
  );
};

const ElemUserName: FC<Props> = ({ control }) => {
  return (
    <StyledTableRow>
      <TableCell sx={{ width: "400px", wordBreak: "break-word" }}>
        名前
      </TableCell>
      <TableCell sx={{ width: "750px", p: "0px", wordBreak: "break-word" }}>
        <InputBox>
          <Controller
            name="username"
            control={control}
            defaultValue=""
            render={({ field, fieldState: { error } }) => (
              <TextField
                {...field}
                type="text"
                placeholder="ユーザ名を入力してください"
                error={error != null}
                helperText={error?.message}
                sx={{ width: "100%" }}
              />
            )}
          />
        </InputBox>
      </TableCell>
    </StyledTableRow>
  );
};

const ElemUserPassword: FC<Props> = ({ control }) => {
  return (
    <StyledTableRow>
      <TableCell sx={{ width: "400px", wordBreak: "break-word" }}>
        パスワード
      </TableCell>
      <TableCell sx={{ width: "750px", p: "0px", wordBreak: "break-word" }}>
        <InputBox>
          <Controller
            name="password"
            control={control}
            defaultValue=""
            render={({ field, fieldState: { error } }) => (
              <TextField
                {...field}
                type="password"
                placeholder="パスワードを入力してください"
                error={error != null}
                helperText={error?.message}
                sx={{ width: "100%" }}
              />
            )}
          />
        </InputBox>
      </TableCell>
    </StyledTableRow>
  );
};

const ElemIsSuperuser: FC<Props> = ({ control }) => {
  const serverContext = ServerContext.getInstance();

  return (
    <StyledTableRow>
      <TableCell sx={{ width: "400px", wordBreak: "break-word" }}>
        管理者権限
      </TableCell>
      <TableCell sx={{ width: "750px", p: "0px", wordBreak: "break-word" }}>
        <Controller
          name="isSuperuser"
          control={control}
          defaultValue={false}
          render={({ field }) => (
            <Checkbox
              checked={field.value}
              onChange={(e) => field.onChange(e.target.checked)}
              disabled={!(serverContext?.user?.isSuperuser ?? false)}
            />
          )}
        />
      </TableCell>
    </StyledTableRow>
  );
};

interface UserFormProps {
  user?: UserRetrieve;
  control: Control<Schema>;
  isCreateMode: boolean;
  isSuperuser: boolean;
  isMyself: boolean;
  isSubmittable: boolean;
  handleSubmit: (e?: BaseSyntheticEvent) => Promise<void>;
  handleCancel: () => void;
}

export const UserForm: FC<UserFormProps> = ({
  user,
  control,
  isCreateMode,
  isSuperuser,
  isMyself,
  isSubmittable,
  handleSubmit,
  handleCancel,
}) => {
  return (
    <Box>
      <Box display="flex" justifyContent="flex-end" pb="24px">
        <Box mx="4px">
          <Button
            variant="contained"
            color="secondary"
            disabled={!isSubmittable}
            onClick={handleSubmit}
          >
            保存
          </Button>
        </Box>
        <Box mx="4px">
          <Button variant="outlined" color="primary" onClick={handleCancel}>
            キャンセル
          </Button>
        </Box>
      </Box>
      <TableContainer component={Paper}>
        <Table className="table table-bordered">
          <TableHead>
            <TableRow sx={{ backgroundColor: "#455A64" }}>
              <TableCell sx={{ color: "#FFFFFF" }}>項目</TableCell>
              <TableCell sx={{ color: "#FFFFFF" }}>内容</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            <ElemUserName control={control} />
            <ElemEmailAddress control={control} />
            {isSuperuser && <ElemIsSuperuser control={control} />}

            {isCreateMode && <ElemUserPassword control={control} />}

            {/* Hide other user's token information */}
            {!isCreateMode && isMyself && user != null && (
              <>
                <ElemAccessToken user={user} />
                <ElemAccessTokenConfiguration user={user} control={control} />
                <ElemAuthenticationMethod user={user} />
              </>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};
