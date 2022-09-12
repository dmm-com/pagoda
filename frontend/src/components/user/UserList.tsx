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
  Theme,
  Typography,
} from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC, useState } from "react";
import { Link, useHistory } from "react-router-dom";
import { useAsync } from "react-use";

import { aironeApiClientV2 } from "../../apiclient/AironeApiClientV2";
import { Loading } from "../common/Loading";
import { SearchBox } from "../common/SearchBox";

import { UserControlMenu } from "./UserControlMenu";

import { newUserPath, userPath } from "Routes";
import { UserList as ConstUserList } from "utils/Constants";

const useStyles = makeStyles<Theme>((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

export const UserList: FC = ({}) => {
  const classes = useStyles();
  const history = useHistory();

  const [keyword, setKeyword] = useState("");
  const [page, setPage] = useState(1);

  const [userAnchorEls, setUserAnchorEls] = useState<{
    [key: number]: HTMLButtonElement;
  } | null>({});

  const users = useAsync(async () => {
    return await aironeApiClientV2.getUsers(page, keyword);
  }, [page, keyword]);
  if (!users.loading && users.error) {
    throw new Error("Failed to get users from AirOne APIv2 endpoint");
  }

  const handleChange = (event, value) => {
    setPage(value);
  };

  const totalPageCount = users.loading
    ? 0
    : Math.ceil(users.value.count / ConstUserList.MAX_ROW_COUNT);

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" mb={8}>
        <Box width={500}>
          <SearchBox
            placeholder="ユーザを絞り込む"
            value={keyword}
            onChange={(e) => {
              setKeyword(e.target.value);
              /* Reset page number to prevent vanishing entities from display
               * when user move other page */
              setPage(1);
            }}
          />
        </Box>
        <Button
          color="secondary"
          variant="contained"
          component={Link}
          to={newUserPath()}
          sx={{ borderRadius: "24px" }}
        >
          <AddIcon />
          新規ユーザを登録
        </Button>
      </Box>

      {users.loading ? (
        <Loading />
      ) : (
        <Grid container spacing={2}>
          {users.value.results.map((user) => {
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
            onChange={handleChange}
            color="primary"
          />
        </Stack>
      </Box>
    </Box>
  );
};
