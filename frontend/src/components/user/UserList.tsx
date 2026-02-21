import AddIcon from "@mui/icons-material/Add";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import {
  Box,
  Button,
  Card,
  CardActionArea,
  CardHeader,
  IconButton,
  Tooltip,
  Typography,
} from "@mui/material";
import Grid from "@mui/material/Grid2";
import { styled } from "@mui/material/styles";
import { useSnackbar } from "notistack";
import { FC, KeyboardEvent, Suspense, useMemo, useState } from "react";
import { Link } from "react-router";

import { UserControlMenu } from "./UserControlMenu";
import { UserPasswordFormModal } from "./UserPasswordFormModal";

import { ClipboardCopyButton } from "components/common/ClipboardCopyButton";
import { Loading } from "components/common/Loading";
import { PaginationFooter } from "components/common/PaginationFooter";
import { SearchBox } from "components/common/SearchBox";
import { usePage } from "hooks/usePage";
import { usePagodaSWR } from "hooks/usePagodaSWR";
import { aironeApiClient } from "repository/AironeApiClient";
import { newUserPath, userPath } from "routes/Routes";
import { UserListParam } from "services/Constants";
import { ServerContext } from "services/ServerContext";
import { normalizeToMatch } from "services/StringUtil";

const StyledCardHeader = styled(CardHeader)(({}) => ({
  p: "0px",
  mt: "24px",
  mx: "16px",
  mb: "16px",
  ".MuiCardHeader-content": {
    width: "80%",
  },
}));

const UserName = styled(Typography)(({}) => ({
  textOverflow: "ellipsis",
  overflow: "hidden",
  whiteSpace: "nowrap",
}));

const UserListContent: FC = () => {
  const { page, query, changePage, changeQuery } = usePage();
  const [userAnchorEls, setUserAnchorEls] = useState<{
    [key: number]: HTMLButtonElement | null;
  }>({});
  const { data: users, mutate: refreshUsers } = usePagodaSWR(
    ["users", page, query],
    () => aironeApiClient.getUsers(page, query),
    { suspense: true },
  );

  const serverContext = useMemo(() => ServerContext.getInstance(), []);
  const currentUsername = useMemo(
    () => serverContext?.user?.username,
    [serverContext],
  );
  const isSuperuser = useMemo(
    () => serverContext?.user?.isSuperuser === true,
    [serverContext],
  );

  const handleChangeQuery = changeQuery;

  const [passwordModalUserId, setPasswordModalUserId] = useState<number | null>(
    null,
  );
  const { enqueueSnackbar } = useSnackbar();

  const handleOpenPasswordModal = (userId: number) => {
    setPasswordModalUserId(userId);
  };

  const handleClosePasswordModal = () => {
    setPasswordModalUserId(null);
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" mb="16px">
        <Box width={500}>
          <SearchBox
            placeholder="ユーザを絞り込む"
            defaultValue={query}
            onKeyPress={(e: KeyboardEvent<HTMLDivElement>, value: string) => {
              if (e.key === "Enter") {
                handleChangeQuery(normalizeToMatch(value));
              }
            }}
          />
        </Box>
        <Button
          color="secondary"
          variant="contained"
          disabled={!isSuperuser}
          component={Link}
          to={newUserPath()}
          sx={{ borderRadius: "24px", height: "100%" }}
        >
          <AddIcon />
          新規ユーザを登録
        </Button>
      </Box>

      <Grid container spacing={2} id="user_list">
        {users.results?.map((user) => {
          const isCurrentUser = user.username === currentUsername;
          const isLinkVisible = isSuperuser || isCurrentUser;
          const isMenuVisible = isSuperuser || isCurrentUser;

          return (
            <Grid size={4} key={user.id}>
              <Card sx={{ height: "100%" }}>
                <StyledCardHeader
                  title={
                    isLinkVisible ? (
                      <CardActionArea component={Link} to={userPath(user.id)}>
                        <Tooltip title={user.username} placement="bottom-start">
                          <UserName>{user.username}</UserName>
                        </Tooltip>
                      </CardActionArea>
                    ) : (
                      <Tooltip title={user.username} placement="bottom-start">
                        <UserName>{user.username}</UserName>
                      </Tooltip>
                    )
                  }
                  action={
                    <>
                      <ClipboardCopyButton name={user.username} />
                      {isMenuVisible && (
                        <>
                          <IconButton
                            onClick={(e) => {
                              setUserAnchorEls({
                                ...userAnchorEls,
                                [user.id]: e.currentTarget,
                              });
                            }}
                          >
                            <MoreVertIcon fontSize="small" />
                          </IconButton>
                          <UserControlMenu
                            user={user}
                            isSelf={isCurrentUser}
                            anchorElem={userAnchorEls[user.id]}
                            handleClose={(userId: number) =>
                              setUserAnchorEls({
                                ...userAnchorEls,
                                [userId]: null,
                              })
                            }
                            onClickEditPassword={handleOpenPasswordModal}
                            setToggle={() => refreshUsers()}
                          />
                        </>
                      )}
                    </>
                  }
                />
              </Card>
            </Grid>
          );
        })}
      </Grid>
      {passwordModalUserId !== null && (
        <UserPasswordFormModal
          userId={passwordModalUserId}
          openModal={true}
          onClose={handleClosePasswordModal}
          onSubmitSuccess={() => {
            enqueueSnackbar("パスワードの変更が完了しました", {
              variant: "success",
            });
            handleClosePasswordModal();
            refreshUsers();
          }}
        />
      )}
      <PaginationFooter
        count={users.count ?? 0}
        maxRowCount={UserListParam.MAX_ROW_COUNT}
        page={page}
        changePage={changePage}
      />
    </Box>
  );
};

export const UserList: FC = () => {
  return (
    <Suspense fallback={<Loading />}>
      <UserListContent />
    </Suspense>
  );
};
