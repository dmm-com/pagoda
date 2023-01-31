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
  Pagination,
  Stack,
  Typography,
} from "@mui/material";
import React, { FC, useMemo, useState } from "react";
import { Link, useHistory, useLocation } from "react-router-dom";
import { useAsync } from "react-use";

import { aironeApiClientV2 } from "../../apiclient/AironeApiClientV2";
import { usePage } from "../../hooks/usePage";
import { normalizeToMatch } from "../../utils/StringUtil";
import { Loading } from "../common/Loading";
import { SearchBox } from "../common/SearchBox";

import { UserControlMenu } from "./UserControlMenu";

import { newUserPath, userPath } from "Routes";
import { UserList as ConstUserList } from "utils/Constants";

export const UserList: FC = ({}) => {
  const location = useLocation();
  const history = useHistory();

  const [page, changePage] = usePage();

  const [keyword, setKeyword] = useState("");

  const params = new URLSearchParams(location.search);
  const [query, setQuery] = useState<string>(params.get("query") ?? "");

  const [userAnchorEls, setUserAnchorEls] = useState<{
    [key: number]: HTMLButtonElement | null;
  }>({});

  const users = useAsync(async () => {
    return await aironeApiClientV2.getUsers(page, query);
  }, [page, query]);
  if (!users.loading && users.error) {
    throw new Error("Failed to get users from AirOne APIv2 endpoint");
  }

  const handleChangeQuery = (newQuery?: string) => {
    changePage(1);
    setQuery(newQuery ?? "");

    history.push({
      pathname: location.pathname,
      search: newQuery ? `?query=${newQuery}` : "",
    });
  };

  const totalPageCount = useMemo(() => {
    return users.loading
      ? 0
      : Math.ceil(users.value?.count ?? 0 / ConstUserList.MAX_ROW_COUNT);
  }, [users.loading, users.value]);

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
        <Grid container spacing={2}>
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

      <Box display="flex" justifyContent="center" my="30px">
        <Stack spacing={2}>
          <Pagination
            count={totalPageCount}
            page={page}
            onChange={(_, newPage) => changePage(newPage)}
            color="primary"
          />
        </Stack>
      </Box>
    </Box>
  );
};
