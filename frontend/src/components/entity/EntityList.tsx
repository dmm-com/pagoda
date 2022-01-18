import AddIcon from "@mui/icons-material/Add";
import GroupIcon from "@mui/icons-material/Group";
import HistoryIcon from "@mui/icons-material/History";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import SearchIcon from "@mui/icons-material/Search";
import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Fab,
  Grid,
  IconButton,
  InputAdornment,
  TableCell,
  TableRow,
  TextField,
  Theme,
  Typography,
} from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC, useState } from "react";
import { Link, useHistory } from "react-router-dom";

import {
  aclPath,
  entityEntriesPath,
  entityHistoryPath,
  entityPath,
} from "../../Routes";
import { deleteEntity } from "../../utils/AironeAPIClient";
import { DeleteButton } from "../common/DeleteButton";
import { EditButton } from "../common/EditButton";
import { PaginatedTable } from "../common/PaginatedTable";

const useStyles = makeStyles<Theme>((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
  entityName: {
    margin: theme.spacing(1),
  },
  entityNote: {
    color: theme.palette.text.secondary,
  },
}));

interface Props {
  entities: {
    id: number;
    name: string;
    note: string;
  }[];
}

export const EntityList: FC<Props> = ({ entities }) => {
  const classes = useStyles();
  const history = useHistory();

  const [keyword, setKeyword] = useState("");

  const handleDelete = (event, entityId) => {
    deleteEntity(entityId).then(() => history.go(0));
  };

  const filteredEntities = entities.filter((entity) => {
    return entity.name.indexOf(keyword) !== -1;
  });

  return (
    <Box>
      {/* This box shows search box and create button */}
      <Box display="flex" justifyContent="space-between" mb={8}>
        <Box className={classes.search} width={500}>
          <TextField
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            variant="outlined"
            size="small"
            placeholder="Search"
            sx={{
              background: "#0000000B",
            }}
            fullWidth={true}
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
          />
        </Box>
        <Fab color="secondary" aria-label="add" variant="extended">
          <AddIcon />
          新規作成
        </Fab>
      </Box>

      {/* This box shows each entity Cards */}
      <Grid container spacing={2}>
        {filteredEntities.map((entity) => (
          <Grid item xs={4}>
            <Card>
              <CardHeader
                title={entity.name}
                action={
                  <IconButton>
                    <MoreVertIcon />
                  </IconButton>
                }
              />
              <CardContent>
                <Typography className={classes.entityNote}>
                  {entity.note}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* This box shows each entity cards */}
      <PaginatedTable
        rows={filteredEntities}
        tableHeadRow={
          <TableRow>
            <TableCell></TableCell>
            <TableCell />
            <TableCell>新規作成</TableCell>
          </TableRow>
        }
        tableBodyRowGenerator={(entity) => (
          <TableRow key={entity.id} data-testid="entityTableRow">
            <TableCell>
              <Typography component={Link} to={entityEntriesPath(entity.id)}>
                {entity.name}
              </Typography>
            </TableCell>
            <TableCell>
              <Typography>{entity.note}</Typography>
            </TableCell>
            <TableCell align="right">
              <EditButton to={entityPath(entity.id)}>
                エンティティ編集
              </EditButton>
              <Button
                variant="contained"
                color="primary"
                className={classes.button}
                startIcon={<HistoryIcon />}
                component={Link}
                to={entityHistoryPath(entity.id)}
              >
                変更履歴
              </Button>
              <Button
                variant="contained"
                color="primary"
                className={classes.button}
                startIcon={<GroupIcon />}
                component={Link}
                to={aclPath(entity.id)}
              >
                ACL
              </Button>
              <DeleteButton handleDelete={(e) => handleDelete(e, entity.id)}>
                削除
              </DeleteButton>
            </TableCell>
          </TableRow>
        )}
        rowsPerPageOptions={[100, 250, 1000]}
      />
    </Box>
  );
};
