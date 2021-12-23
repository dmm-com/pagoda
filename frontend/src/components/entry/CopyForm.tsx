import { Box, Button } from "@mui/material";
import React, { FC, useState } from "react";
import { useHistory } from "react-router-dom";

import { entityEntriesPath } from "../../Routes";
import { copyEntry } from "../../utils/AironeAPIClient";

interface Props {
  entityId: number;
  entryId: number;
}

export const CopyForm: FC<Props> = ({ entityId, entryId }) => {
  const history = useHistory();

  const [entries, setEntries] = useState("");

  const handleSubmit = async (event) => {
    await copyEntry(entryId, entries);
    history.push(entityEntriesPath(entityId));

    event.preventDefault();
  };

  return (
    <form onSubmit={handleSubmit}>
      <Box className="row">
        <Box className="col">
          <Box className="float-left">
            入力した各行毎に同じ属性値を持つ別エントリを作成
          </Box>
          <Box className="float-right">
            <Button type="submit" variant="contained">
              コピー
            </Button>
          </Box>
        </Box>
      </Box>
      <Box className="row">
        <Box className="col-5">
          <textarea
            cols={40}
            rows={10}
            value={entries}
            onChange={(e) => setEntries(e.target.value)}
          />
        </Box>
      </Box>
    </form>
  );
};
