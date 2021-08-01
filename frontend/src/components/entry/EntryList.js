import React, { useRef, useState } from "react";
import { Link, useHistory } from "react-router-dom";
import { makeStyles } from "@material-ui/core/styles";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
} from "@material-ui/core";
import Typography from "@material-ui/core/Typography";
import Paper from "@material-ui/core/Paper";
import DeleteButton from "../common/DeleteButton";
import PropTypes from "prop-types";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
  entryName: {
    margin: theme.spacing(1),
  },
}));

export default function EntryList({ entityId, entries }) {
  const classes = useStyles();
  const history = useHistory();

  const keywordRef = useRef({ value: "" });
  const [keyword, setKeyword] = useState("");

  const [page, setPage] = React.useState(0);
  const [rowsPerPage, setRowsPerPage] = React.useState(100);

  const handleKeyPressKeyword = (event) => {
    if (event.key === "Enter") {
      setKeyword(keywordRef.current.value);
    }
  };

  const handleDelete = (event, entryId) => {
    deleteEntry(entryId).then((_) => history.go(0));
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(+event.target.value);
    setPage(0);
  };

  const filteredEntries = entries.filter((e) => {
    return e.name.indexOf(keyword) !== -1;
  });

  return (
    <Paper>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>
                <span className={classes.entryName}>エントリ名</span>
                <input
                  className={classes.entryName}
                  text="text"
                  placeholder="絞り込む"
                  ref={keywordRef}
                  onKeyPress={handleKeyPressKeyword}
                />
              </TableCell>
              <TableCell align="right" />
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredEntries
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((entry) => (
                <TableRow>
                  <TableCell>
                    <Typography
                      component={Link}
                      to={`/new-ui/entities/${entityId}/entries/${entry.id}/show`}
                    >
                      {entry.name}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <DeleteButton
                      onConfirmed={(e) => handleDelete(e, entry.id)}
                    >
                      削除
                    </DeleteButton>
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        rowsPerPageOptions={[100, 250, 1000]}
        component="div"
        count={filteredEntries.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onChangePage={handleChangePage}
        onChangeRowsPerPage={handleChangeRowsPerPage}
      />
    </Paper>
  );
}

EntryList.propTypes = {
  entityId: PropTypes.number.isRequired,
  entries: PropTypes.array.isRequired,
};
