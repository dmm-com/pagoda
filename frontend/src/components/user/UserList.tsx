import AddIcon from "@mui/icons-material/Add";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import {
  Box,
  Button,
  Card,
  CardActionArea,
  CardHeader,
  Grid,
  IconButton,
  Tooltip,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useMemo, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router";

import { UserControlMenu } from "./UserControlMenu";

import { ClipboardCopyButton } from "components/common/ClipboardCopyButton";
import { Loading } from "components/common/Loading";
import { PaginationFooter } from "components/common/PaginationFooter";
import { SearchBox } from "components/common/SearchBox";
import { useAsyncWithThrow } from "hooks/useAsyncWithThrow";
import { usePage } from "hooks/usePage";
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

export const UserList: FC = ({}) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [page, changePage] = usePage();
  const params = new URLSearchParams(location.search);
  const [query, setQuery] = useState<string>(params.get("query") ?? "");
  const [userAnchorEls, setUserAnchorEls] = useState<{
    [key: number]: HTMLButtonElement | null;
  }>({});
  const [toggle, setToggle] = useState(false);

  const users = useAsyncWithThrow(async () => {
    return await aironeApiClient.getUsers(page, query);
  }, [page, query, toggle]);

  const isSuperuser = useMemo(() => {
    const serverContext = ServerContext.getInstance();
    return (
      serverContext?.user?.isSuperuser != null && serverContext.user.isSuperuser
    );
  }, []);

  const handleChangeQuery = (newQuery?: string) => {
    changePage(1);
    setQuery(newQuery ?? "");

    navigate({
      pathname: location.pathname,
      search: newQuery ? `?query=${newQuery}` : "",
    });
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" mb="16px">
        <Box width={500}>
          <SearchBox
            placeholder="ユーザを絞り込む"
            defaultValue={query}
            onKeyPress={(e) => {
              e.key === "Enter" &&
                handleChangeQuery(
                  normalizeToMatch((e.target as HTMLInputElement).value ?? "")
                );
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

      {users.loading ? (
        <Loading />
      ) : (
        <Grid container spacing={2} id="user_list">
          {users.value?.results?.map((user) => {
            return (
              <Grid item xs={4} key={user.id}>
                <Card sx={{ height: "100%" }}>
                  <StyledCardHeader
                    title={
                      <CardActionArea component={Link} to={userPath(user.id)}>
                        <Tooltip title={user.username} placement="bottom-start">
                          <UserName>{user.username}</UserName>
                        </Tooltip>
                      </CardActionArea>
                    }
                    action={
                      <>
                        <ClipboardCopyButton name={user.username} />

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
                          anchorElem={userAnchorEls[user.id]}
                          handleClose={(userId: number) =>
                            setUserAnchorEls({
                              ...userAnchorEls,
                              [userId]: null,
                            })
                          }
                          setToggle={() => setToggle(!toggle)}
                        />
                      </>
                    }
                  />
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}

      <PaginationFooter
        count={users.value?.count ?? 0}
        maxRowCount={UserListParam.MAX_ROW_COUNT}
        page={page}
        changePage={changePage}
      />
    </Box>
  );
};
