import { Box } from "@mui/material";
import React, { FC } from "react";
import { useAsync } from "react-use";

import { EntryHistory } from "../components/entry/EntryHistory";
import { useTypedParams } from "../hooks/useTypedParams";
import { getEntryHistory } from "../utils/AironeAPIClient";

export const ShowEntryHistoryPage: FC = () => {
  const { entryId } = useTypedParams<{ entryId: number }>();

  const entryHistory: any = useAsync(async () => {
    return await getEntryHistory(entryId);
  });

  return (
    <Box>
      {!entryHistory.loading && <EntryHistory histories={entryHistory.value} />}
    </Box>
  );
};
