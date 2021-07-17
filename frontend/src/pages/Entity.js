import React, { useEffect, useState } from "react";
import Button from "@material-ui/core/Button";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
} from "@material-ui/core";
import Paper from "@material-ui/core/Paper";
import { Link } from "react-router-dom";
import EditIcon from "@material-ui/icons/Edit";
import HistoryIcon from "@material-ui/icons/History";
import GroupIcon from "@material-ui/icons/Group";
import DeleteIcon from "@material-ui/icons/Delete";
import { makeStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import AironeBreadcrumbs from "../components/AironeBreadcrumbs";
import { deleteEntity, getEntities } from "../utils/AironeAPIClient";
import ConfirmableButton from "../components/ConfirmableButton";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
  entityName: {
    margin: theme.spacing(1),
  },
}));

export default function Entity(props) {
  const classes = useStyles();

  const [keyword, setKeyword] = useState("");
  const [entities, setEntities] = useState([]);
  const [filteredEntities, setFilteredEntities] = useState([]);

  const [page, setPage] = React.useState(0);
  const [rowsPerPage, setRowsPerPage] = React.useState(100);

  const [updated, setUpdated] = useState(false);

  useEffect(() => {
    getEntities()
      .then((resp) => resp.json())
      .then((data) => {
        setEntities(data.entities);
        setFilteredEntities(data.entities);
      });
    setUpdated(false);
  }, [updated]);

  const onChangeKeyword = (event) => {
    setKeyword(event.target.value);
  };

  const onKeyPressKeyword = (event) => {
    if (event.key === "Enter" && keyword) {
      setFilteredEntities(
        entities.filter((entity) => {
          return entity.name.indexOf(keyword) !== -1;
        })
      );
    } else {
      setFilteredEntities(entities);
    }
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(+event.target.value);
    setPage(0);
  };

  const handleDelete = (event, entityId) => {
    deleteEntity(entityId).then((_) => setUpdated(true));
  };

  return (
    <div className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to="/new-ui/">
          Top
        </Typography>
        <Typography color="textPrimary">エンティティ一覧</Typography>
      </AironeBreadcrumbs>

      <div className="row">
        <div className="col">
          <div className="float-left">
            <Button
              variant="outlined"
              color="primary"
              className={classes.button}
              component={Link}
              to={`/new-ui/entities/new`}
            >
              エンティティ作成
            </Button>
            <Button
              className={classes.button}
              variant="outlined"
              color="secondary"
            >
              エクスポート
            </Button>
            <Button
              variant="outlined"
              color="secondary"
              className={classes.button}
              component={Link}
              to={`/new-ui/import`}
            >
              インポート
            </Button>
          </div>
          <div className="float-right"></div>
        </div>
      </div>

      <Paper>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>
                  <span className={classes.entityName}>エンティティ名</span>
                  <input
                    className={classes.entityName}
                    text="text"
                    placeholder="絞り込む"
                    value={keyword}
                    onChange={onChangeKeyword}
                    onKeyPress={onKeyPressKeyword}
                  />
                </TableCell>
                <TableCell>
                  <Typography>備考</Typography>
                </TableCell>
                <TableCell align="right" />
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredEntities
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((entity) => (
                  <TableRow>
                    <TableCell>
                      <Typography
                        component={Link}
                        to={`/new-ui/entities/${entity.id}/entries`}
                      >
                        {entity.name}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography>{entity.note}</Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Button
                        variant="contained"
                        color="primary"
                        className={classes.button}
                        startIcon={<EditIcon />}
                        component={Link}
                        to={`/new-ui/entities/${entity.id}`}
                      >
                        エンティティ編集
                      </Button>
                      <Button
                        variant="contained"
                        color="primary"
                        className={classes.button}
                        startIcon={<HistoryIcon />}
                        component={Link}
                        to={`/new-ui/entities/${entity.id}/history`}
                      >
                        変更履歴
                      </Button>
                      <Button
                        variant="contained"
                        color="primary"
                        className={classes.button}
                        startIcon={<GroupIcon />}
                        component={Link}
                        to={`/new-ui/acl/${entity.id}`}
                      >
                        ACL
                      </Button>
                      <ConfirmableButton
                        variant="contained"
                        color="secondary"
                        className={classes.button}
                        startIcon={<DeleteIcon />}
                        component={Link}
                        dialogTitle="本当に削除しますか？"
                        onClickYes={(e) => handleDelete(e, entity.id)}
                      >
                        削除
                      </ConfirmableButton>
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          rowsPerPageOptions={[100, 250, 1000]}
          component="div"
          count={filteredEntities.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onChangePage={handleChangePage}
          onChangeRowsPerPage={handleChangeRowsPerPage}
        />
      </Paper>
    </div>
  );
}
