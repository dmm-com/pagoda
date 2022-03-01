import { Box, Button } from "@mui/material";
import React, { FC, useState } from "react";
import { useHistory } from "react-router-dom";

import { entryDetailsPath } from "Routes";
import { copyEntry } from "utils/AironeAPIClient";

interface Props {
  entityId: number;
  entryId: number;
}

export const CopyForm: FC<Props> = ({ entityId, entryId }) => {
  const history = useHistory();

  const [entries, setEntries] = useState<string>("");

  const handleCopy = async () => {
    await copyEntry(entryId, entries);
    history.replace(entryDetailsPath(entityId, entryId));
  };

  return (
    <Box>
      <Box>
        <Box>
          <Box>入力した各行毎に同じ属性値を持つ別エントリを作成</Box>
          <Box>
            <Button type="submit" variant="contained" onClick={handleCopy}>
              コピー
            </Button>
          </Box>
        </Box>
      </Box>
      <Box>
        <Box>
          <textarea
            cols={40}
            rows={10}
            value={entries}
            onChange={(e) => setEntries(e.target.value)}
          />
        </Box>
      </Box>
    </Box>
  );
};
