import AddIcon from "@mui/icons-material/Add";
import RestoreIcon from "@mui/icons-material/Restore";
import SearchIcon from "@mui/icons-material/Search";
import {
  Box,
  Fab,
  Input,
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

import { newEntryPath, showEntryPath } from "../../Routes";
import { deleteEntry, restoreEntry } from "../../utils/AironeAPIClient";
import { ConfirmableButton } from "../common/ConfirmableButton";
import { DeleteButton } from "../common/DeleteButton";
import { PaginatedTable } from "../common/PaginatedTable";

const useStyles = makeStyles<Theme>((theme) => ({
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

export const EntryList: FC<Props> = ({ entityId, entries, restoreMode }) => {
  const classes = useStyles();
  const history = useHistory();

  const [keyword, setKeyword] = useState("");
  const [filterKeyword, setFilterKeyword] = useState("");

  const handleKeyPressKeyword = (event) => {
    if (event.key === "Enter") {
      setFilterKeyword(keyword);
    }
  };

  const handleDelete = async (entryId: number) => {
    await deleteEntry(entryId);
    history.go(0);
  };

  const handleRestore = async (entryId: number) => {
    await restoreEntry(entryId);
    history.go(0);
  };

  const filteredEntries = entries.filter((e) => {
    return e.name.indexOf(filterKeyword) !== -1;
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
            placeholder="エントリを絞り込む"
            sx={{
              background: "#0000000B",
            }}
            fullWidth={true}
            value={keyword}
            onChange={(e) => {
              setKeyword(e.target.value);

              /* Reset page number to prevent vanishing entities from display
               * when user move other page */
              //setPage(1);
            }}
          />
        </Box>
        <Fab
          color="secondary"
          aria-label="add"
          variant="extended"
          component={Link}
          to={newEntryPath(entityId)}
        >
          <AddIcon />
          新規エントリを作成
        </Fab>
      </Box>
      <PaginatedTable
        rows={filteredEntries}
        tableHeadRow={
          <TableRow>
            <TableCell>
              <span className={classes.entryName}>エントリ名</span>
              <Input
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
                  onClickYes={() => handleRestore(entry.id)}
                >
                  Restore
                </ConfirmableButton>
              ) : (
                <DeleteButton handleDelete={() => handleDelete(entry.id)}>
                  削除
                </DeleteButton>
              )}
            </TableCell>
          </TableRow>
        )}
        rowsPerPageOptions={[100, 250, 1000]}
      />
    </Box>
  );
};
