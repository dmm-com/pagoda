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
  Typography,
} from "@mui/material";
import React, { FC, useMemo, useState } from "react";
import { Link, useHistory, useLocation } from "react-router-dom";

import { useAsyncWithThrow } from "../../hooks/useAsyncWithThrow";

import { UserControlMenu } from "./UserControlMenu";

import { newUserPath, userPath } from "Routes";
import { Loading } from "components/common/Loading";
import { PaginationFooter } from "components/common/PaginationFooter";
import { SearchBox } from "components/common/SearchBox";
import { usePage } from "hooks/usePage";
import { aironeApiClient } from "repository/AironeApiClient";
import { UserList as ConstUserList } from "services/Constants";
import { ServerContext } from "services/ServerContext";
import { normalizeToMatch } from "services/StringUtil";

export const UserList: FC = ({}) => {
  const location = useLocation();
  const history = useHistory();
  const [page, changePage] = usePage();
  const params = new URLSearchParams(location.search);
  const [query, setQuery] = useState<string>(params.get("query") ?? "");
  const [keyword, setKeyword] = useState(query ?? "");
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

    history.push({
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
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onKeyPress={(e) => {
              e.key === "Enter" &&
                handleChangeQuery(
                  keyword.length > 0 ? normalizeToMatch(keyword) : undefined
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
                  <CardHeader
                    sx={{
                      p: "0px",
                      mt: "24px",
                      mx: "16px",
                      mb: "16px",
                      ".MuiCardHeader-content": {
                        width: "80%",
                      },
                    }}
                    title={
                      <CardActionArea component={Link} to={userPath(user.id)}>
                        <Typography
                          variant="h6"
                          sx={{
                            textOverflow: "ellipsis",
                            overflow: "hidden",
                            whiteSpace: "nowrap",
                          }}
                        >
                          {user.username}
                        </Typography>
                      </CardActionArea>
                    }
                    action={
                      <>
                        <IconButton
                          onClick={(e) => {
                            setUserAnchorEls({
                              ...userAnchorEls,
                              [user.id]: e.currentTarget,
                            });
                          }}
                        >
                          <MoreVertIcon />
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
        maxRowCount={ConstUserList.MAX_ROW_COUNT}
        page={page}
        changePage={changePage}
      />
    </Box>
  );
};
