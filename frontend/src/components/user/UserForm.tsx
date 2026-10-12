import {
  UserRetrieve,
  UserRetrieveAuthenticateTypeEnum,
  UserRole,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import {
  Box,
  Button,
  Checkbox,
  Chip,
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
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { useSnackbar } from "notistack";
import {
  BaseSyntheticEvent,
  FC,
  ReactNode,
  useCallback,
  useMemo,
  useState,
} from "react";
import { Control, Controller, useWatch } from "react-hook-form";

import { ChangeUserAuthModal } from "./ChangeUserAuthModal";
import { Schema } from "./userForm/UserFormSchema";

import { AironeLink } from "components/common/AironeLink";
import { FlexBox } from "components/common/FlexBox";
import { useTranslation } from "hooks/useTranslation";
import { translate } from "i18n/config";
import { groupPath, rolePath, userPath } from "routes/Routes";
import { ServerContext } from "services/ServerContext";
import { User } from "services/ServerContext";

type CoUserLink = { id: number; username: string };

type UserWithCoUsers = UserRetrieve & {
  coUsers?: CoUserLink[];
};

const StyledTableRow = styled(TableRow)(() => ({
  "&:nth-of-type(odd)": {
    backgroundColor: "#607D8B0A",
  },
  "&:last-child td, &:last-child th": {
    border: 0,
  },
}));

const ChipBox = styled(Box)(({ theme }) => ({
  display: "flex",
  flexWrap: "wrap",
  gap: theme.spacing(0.5),
  margin: theme.spacing(1),
}));

const EmptyMessage = styled(Typography)(({ theme }) => ({
  margin: theme.spacing(1),
  color: theme.palette.text.secondary,
}));

interface Props {
  control: Control<Schema>;
}

interface ReadonlyProps {
  user: UserRetrieve;
}

const InputBox: FC<{ children: ReactNode; sx?: object }> = ({
  children,
  sx,
}) => {
  return (
    <Box
      component="form"
      sx={{
        m: 1,
        p: "2px 4px",
        display: "flex",
        alignItems: "center",
        width: "90%",
        ...sx,
      }}
    >
      {children}
    </Box>
  );
};

const ElemAuthenticationMethod: FC<ReadonlyProps> = ({ user }) => {
  const [openModal, setOpenModal] = useState(false);
  const { t } = useTranslation();

  return (
    <StyledTableRow>
      <TableCell sx={{ width: "400px", wordBreak: "break-word" }}>
        {t("user.form.authMethod")}
      </TableCell>
      <TableCell sx={{ width: "750px", p: "0px", wordBreak: "break-word" }}>
        {user.authenticateType ===
        UserRetrieveAuthenticateTypeEnum.AUTH_TYPE_LOCAL ? (
          <Box sx={{ m: 1 }}>
            <Box sx={{ my: 1 }}>{t("user.form.localAuth")}</Box>
            <Button variant="outlined" onClick={() => setOpenModal(true)}>
              {t("user.form.changeToLdap")}
            </Button>
          </Box>
        ) : (
          <InputBox>{t("user.form.ldapAuth")}</InputBox>
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
  const { t } = useTranslation();

  return (
    <StyledTableRow>
      <TableCell sx={{ width: "400px", wordBreak: "break-word" }}>
        {t("user.form.accessTokenExpiry")}
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
                      label={t("user.form.tokenLifetimeLabel")}
                      InputProps={{
                        endAdornment: (
                          <InputAdornment position="end">
                            {t("user.form.secondsUnit")}
                          </InputAdornment>
                        ),
                      }}
                      error={error != null}
                      helperText={
                        error?.message ?? t("user.form.tokenLifetimeHelperText")
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
                  label={t("user.form.tokenCreatedAt")}
                  id="token-created"
                  InputProps={{ disableUnderline: true, readOnly: true }}
                  value={user.token.created}
                  disabled
                  data-testid="token-created"
                  sx={{ mr: 2 }}
                />

                <TextField
                  variant="standard"
                  label={t("user.form.tokenExpiresAt")}
                  id="token-expire"
                  InputProps={{ disableUnderline: true, readOnly: true }}
                  value={
                    user.token.lifetime === 0
                      ? t("user.form.tokenUnlimited")
                      : user.token.expire
                  }
                  disabled
                  data-testid="token-expire"
                />
              </Box>
            </Box>
          ) : (
            <Box>{t("user.form.accessTokenNotIssued")}</Box>
          )}
        </InputBox>
      </TableCell>
    </StyledTableRow>
  );
};

const ElemAccessToken: FC<ReadonlyProps> = ({ user }) => {
  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation();

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(user.token?.value ?? "");
      enqueueSnackbar(t("user.form.copyTokenSuccess"), {
        variant: "success",
      });
    } catch (error) {
      enqueueSnackbar(t("user.form.copyTokenFailure"), {
        variant: "error",
      });
    }
  }, [enqueueSnackbar, user.token?.value, t]);

  return (
    <StyledTableRow>
      <TableCell sx={{ width: "400px", wordBreak: "break-word" }}>
        {t("user.form.accessToken")}
      </TableCell>
      <TableCell sx={{ width: "750px", p: "0px", wordBreak: "break-word" }}>
        <InputBox>
          <TextField
            sx={{ width: "100%" }}
            placeholder={t("user.form.accessTokenPlaceholder")}
            inputProps={{
              "aria-label": "search google maps",
              readOnly: true,
            }}
            value={user.token?.value}
            disabled
          />
          <IconButton
            type="button"
            sx={{ p: "10px" }}
            aria-label="copy-token"
            onClick={handleCopy}
          >
            <ContentCopyIcon />
          </IconButton>
        </InputBox>
      </TableCell>
    </StyledTableRow>
  );
};

const ElemEmailAddress: FC<Props> = ({ control }) => {
  const { t } = useTranslation();

  return (
    <StyledTableRow>
      <TableCell sx={{ width: "400px", wordBreak: "break-word" }}>
        {t("user.form.email")}
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
                placeholder={t("user.form.emailPlaceholder")}
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

const ElemUserName: FC<Props & { isMyself: boolean; isCoUser: boolean }> = ({
  control,
  isMyself,
  isCoUser,
}) => {
  const userInfo = useWatch({ control });
  const loginUser: User | undefined = useMemo(
    () => ServerContext.getInstance()?.user,
    [],
  );
  const { t } = useTranslation();

  return (
    <StyledTableRow>
      <TableCell sx={{ width: "400px", wordBreak: "break-word" }}>
        {t("user.form.name")}
      </TableCell>
      <TableCell sx={{ width: "750px", p: "0px", wordBreak: "break-word" }}>
        {isMyself || isCoUser ? (
          <InputBox>
            <Typography>{userInfo.username}</Typography>
          </InputBox>
        ) : (
          <FlexBox alignItems={"center"}>
            {loginUser && !loginUser.isSuperuser && (
              <Typography sx={{ whiteSpace: "nowrap" }}>
                {loginUser.username}-
              </Typography>
            )}
            <InputBox sx={{ flex: 1, width: "auto" }}>
              <Controller
                name="username"
                control={control}
                defaultValue=""
                render={({ field, fieldState: { error } }) => (
                  <TextField
                    {...field}
                    type="text"
                    placeholder={t("user.form.usernamePlaceholder")}
                    error={error != null}
                    helperText={error?.message}
                    sx={{ width: "100%" }}
                  />
                )}
              />
            </InputBox>
          </FlexBox>
        )}
      </TableCell>
    </StyledTableRow>
  );
};

const ElemGroups: FC<ReadonlyProps> = ({ user }) => {
  const { t } = useTranslation();
  return (
    <StyledTableRow>
      <TableCell sx={{ width: "400px", wordBreak: "break-word" }}>
        {t("user.form.belongingGroups")}
      </TableCell>
      <TableCell sx={{ width: "750px", p: "0px", wordBreak: "break-word" }}>
        {user.groups.length > 0 ? (
          <ChipBox>
            {user.groups.map((group) => (
              <Chip
                key={group.id}
                label={
                  group.isDirect
                    ? group.name
                    : t("user.form.inheritedGroupLabel", {
                        name: group.name,
                      })
                }
                size="small"
                variant={group.isDirect ? "filled" : "outlined"}
                component={AironeLink}
                to={groupPath(group.id)}
                clickable
              />
            ))}
          </ChipBox>
        ) : (
          <EmptyMessage>{t("user.form.noBelongingGroups")}</EmptyMessage>
        )}
      </TableCell>
    </StyledTableRow>
  );
};

/**
 * Builds a chip label that tells why the user belongs to the role, because a
 * role can be granted through a group instead of being assigned directly.
 */
const getRoleLabel = (role: UserRole): string => {
  const notes: string[] = [];
  if (role.isAdmin) {
    notes.push(translate("user.form.adminNote"));
  }
  if (!role.isDirect && role.viaGroups.length > 0) {
    notes.push(
      translate("user.form.viaGroupsNote", {
        names: role.viaGroups.map((g) => g.name).join(", "),
      }),
    );
  }

  return notes.length > 0 ? `${role.name} (${notes.join(" / ")})` : role.name;
};

const ElemRoles: FC<ReadonlyProps> = ({ user }) => {
  const { t } = useTranslation();
  return (
    <StyledTableRow>
      <TableCell sx={{ width: "400px", wordBreak: "break-word" }}>
        {t("user.form.belongingRoles")}
      </TableCell>
      <TableCell sx={{ width: "750px", p: "0px", wordBreak: "break-word" }}>
        {user.roles.length > 0 ? (
          <ChipBox>
            {user.roles.map((role) => (
              <Chip
                key={role.id}
                label={getRoleLabel(role)}
                size="small"
                variant={role.isDirect ? "filled" : "outlined"}
                component={AironeLink}
                to={rolePath(role.id)}
                clickable
              />
            ))}
          </ChipBox>
        ) : (
          <EmptyMessage>{t("user.form.noBelongingRoles")}</EmptyMessage>
        )}
      </TableCell>
    </StyledTableRow>
  );
};

const ElemCoUsers: FC<ReadonlyProps> = ({ user }) => {
  const { t } = useTranslation();
  const coUsers = (user as UserWithCoUsers).coUsers ?? [];
  if (coUsers.length === 0) return null;

  return (
    <StyledTableRow>
      <TableCell sx={{ width: "400px", wordBreak: "break-word" }}>
        {t("user.form.createdReadOnlyUsers")}
      </TableCell>
      <TableCell sx={{ width: "750px", p: "0px", wordBreak: "break-word" }}>
        {
          <ChipBox>
            {coUsers.map((coUser) => (
              <Chip
                key={coUser.id}
                label={coUser.username}
                size="small"
                component={AironeLink}
                to={userPath(coUser.id)}
                clickable
              />
            ))}
          </ChipBox>
        }
      </TableCell>
    </StyledTableRow>
  );
};

const ElemUserPassword: FC<Props> = ({ control }) => {
  const { t } = useTranslation();

  return (
    <StyledTableRow>
      <TableCell sx={{ width: "400px", wordBreak: "break-word" }}>
        {t("user.form.password")}
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
                placeholder={t("user.form.passwordPlaceholder")}
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
  const loginUser = useMemo(() => ServerContext.getInstance()?.user, []);
  const { t } = useTranslation();

  return (
    <StyledTableRow>
      <TableCell sx={{ width: "400px", wordBreak: "break-word" }}>
        {t("user.form.isSuperuser")}
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
              disabled={!(loginUser?.isSuperuser ?? false)}
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
  isMyself: boolean;
  isCoUser: boolean;
  isSubmittable: boolean;
  handleSubmit: (e?: BaseSyntheticEvent) => Promise<void>;
  handleCancel: () => void;
}

export const UserForm: FC<UserFormProps> = ({
  user,
  control,
  isCreateMode,
  isMyself,
  isCoUser,
  isSubmittable,
  handleSubmit,
  handleCancel,
}) => {
  const loginUser = useMemo(() => ServerContext.getInstance()?.user, []);
  const { t } = useTranslation();

  return (
    <Box>
      <Box display="flex" justifyContent="flex-end" pb="24px">
        <Box mx="4px">
          <Button
            variant="contained"
            color="secondary"
            disabled={!isSubmittable || (loginUser?.isReadonly && !isMyself)}
            onClick={handleSubmit}
          >
            {t("common.save")}
          </Button>
        </Box>
        <Box mx="4px">
          <Button variant="outlined" color="primary" onClick={handleCancel}>
            {t("common.cancel")}
          </Button>
        </Box>
      </Box>
      <TableContainer component={Paper}>
        <Table className="table table-bordered">
          <TableHead>
            <TableRow sx={{ backgroundColor: "#455A64" }}>
              <TableCell sx={{ color: "#FFFFFF" }}>
                {t("user.form.columnItem")}
              </TableCell>
              <TableCell sx={{ color: "#FFFFFF" }}>
                {t("user.form.columnContent")}
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            <ElemUserName
              control={control}
              isMyself={isMyself}
              isCoUser={isCoUser}
            />

            {!isCreateMode && user != null && (
              <>
                <ElemGroups user={user} />
                <ElemRoles user={user} />
                <ElemCoUsers user={user} />
              </>
            )}

            {loginUser?.isSuperuser && (
              <>
                <ElemEmailAddress control={control} />
                <ElemIsSuperuser control={control} />
              </>
            )}

            {isCreateMode && <ElemUserPassword control={control} />}

            {/* Hide other user's token information */}
            {!isCreateMode && (isMyself || isCoUser) && user != null && (
              <>
                <ElemAccessToken user={user} />
                <ElemAccessTokenConfiguration user={user} control={control} />
                {isMyself && <ElemAuthenticationMethod user={user} />}
              </>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};
