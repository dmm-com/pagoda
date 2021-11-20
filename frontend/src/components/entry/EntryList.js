import { TableCell, TableRow } from "@material-ui/core";
import Typography from "@material-ui/core/Typography";
import { makeStyles } from "@material-ui/core/styles";
import RestoreIcon from "@material-ui/icons/Restore";
import PropTypes from "prop-types";
import React, { useRef, useState } from "react";
import { Link, useHistory } from "react-router-dom";

import { showEntryPath } from "../../Routes";
import { deleteEntry, restoreEntry } from "../../utils/AironeAPIClient";
import { ConfirmableButton } from "../common/ConfirmableButton";
import { DeleteButton } from "../common/DeleteButton";
import { PaginatedTable } from "../common/PaginatedTable.tsx";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
  entryName: {
    margin: theme.spacing(1),
  },
}));

export function EntryList({ entries, restoreMode = false }) {
  const classes = useStyles();
  const history = useHistory();

  const keywordRef = useRef({ value: "" });
  const [keyword, setKeyword] = useState("");

  const handleKeyPressKeyword = (event) => {
    if (event.key === "Enter") {
      setKeyword(keywordRef.current.value);
    }
  };

  const handleDelete = (event, entryId) => {
    deleteEntry(entryId).then((_) => history.go(0));
  };

  const handleRestore = (event, entryId) => {
    restoreEntry(entryId).then((_) => history.go(0));
  };

  const filteredEntries = entries.filter((e) => {
    return e.name.indexOf(keyword) !== -1;
  });

  return (
    <PaginatedTable
      rows={filteredEntries}
      tableHeadRow={
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
      }
      tableBodyRowGenerator={(entry) => (
        <TableRow key={entry.id}>
          <TableCell>
            <Typography component={Link} to={showEntryPath(entry.id)}>
              {entry.name}
            </Typography>
          </TableCell>
          <TableCell align="right">
            {restoreMode ? (
              <ConfirmableButton
                variant="contained"
                color="primary"
                className={classes.button}
                startIcon={<RestoreIcon />}
                dialogTitle="本当に復旧しますか？"
                onClickYes={(e) => handleRestore(e, entry.id)}
              >
                Restore
              </ConfirmableButton>
            ) : (
              <DeleteButton handleDelete={(e) => handleDelete(e, entry.id)}>
                削除
              </DeleteButton>
            )}
          </TableCell>
        </TableRow>
      )}
      rowsPerPageOptions={[100, 250, 1000]}
    />
  );
}

EntryList.propTypes = {
  entityId: PropTypes.string.isRequired,
  entries: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      name: PropTypes.string.isRequired,
    })
  ).isRequired,
  restoreMode: PropTypes.bool,
};
