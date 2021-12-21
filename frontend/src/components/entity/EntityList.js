import GroupIcon from "@mui/icons-material/Group";
import HistoryIcon from "@mui/icons-material/History";
import { Button, Input, TableCell, TableRow, Typography } from "@mui/material";
import { makeStyles } from "@mui/styles";
import PropTypes from "prop-types";
import React, { useState } from "react";
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

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
  entityName: {
    margin: theme.spacing(1),
  },
}));

export function EntityList({ entities }) {
  const classes = useStyles();
  const history = useHistory();

  const [keyword, setKeyword] = useState("");

  const handleDelete = (event, entityId) => {
    deleteEntity(entityId).then((_) => history.go(0));
  };

  const filteredEntities = entities.filter((entity) => {
    return entity.name.indexOf(keyword) !== -1;
  });

  return (
    <PaginatedTable
      rows={filteredEntities}
      tableHeadRow={
        <TableRow>
          <TableCell>
            <span className={classes.entityName}>エンティティ名</span>
            <Input
              inputProps={{
                "data-testid": "entityName",
              }}
              className={classes.entityName}
              text="text"
              placeholder="絞り込む"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
            />
          </TableCell>
          <TableCell>
            <Typography>備考</Typography>
          </TableCell>
          <TableCell align="right" />
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
            <EditButton to={entityPath(entity.id)}>エンティティ編集</EditButton>
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
  );
}

EntityList.propTypes = {
  entities: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      name: PropTypes.string.isRequired,
      note: PropTypes.string.isRequired,
    })
  ).isRequired,
};
