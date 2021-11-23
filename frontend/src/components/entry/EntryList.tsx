import { TableCell, TableRow } from "@material-ui/core";
import Typography from "@material-ui/core/Typography";
import { makeStyles } from "@material-ui/core/styles";
import RestoreIcon from "@material-ui/icons/Restore";
import React, { FC, useState } from "react";
import { Link, useHistory } from "react-router-dom";

import { showEntryPath } from "../../Routes";
import { deleteEntry, restoreEntry } from "../../utils/AironeAPIClient";
import { ConfirmableButton } from "../common/ConfirmableButton";
import { DeleteButton } from "../common/DeleteButton";
import { PaginatedTable } from "../common/PaginatedTable";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
  entryName: {
    margin: theme.spacing(1),
  },
}));

interface Props {
  entityId: string;
  entries: {
    id: number;
    name: string;
  }[];
  restoreMode: boolean;
}

export const EntryList: FC<Props> = ({ entries, restoreMode }) => {
  const classes = useStyles();
  const history = useHistory();

  const [keyword, setKeyword] = useState("");
  const [filterKeyword, setFilterKeyword] = useState("");

  const handleKeyPressKeyword = (event) => {
    if (event.key === "Enter") {
      setFilterKeyword(keyword);
    }
  };

  const handleDelete = (event, entryId) => {
    deleteEntry(entryId).then((_) => history.go(0));
  };

  const handleRestore = (event, entryId) => {
    restoreEntry(entryId).then((_) => history.go(0));
  };

  const filteredEntries = entries.filter((e) => {
    return e.name.indexOf(filterKeyword) !== -1;
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
              value={keyword}
              placeholder="絞り込む"
              onChange={(e) => setKeyword(e.target.value)}
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
};
