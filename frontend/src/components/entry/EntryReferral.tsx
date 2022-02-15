import { Box, Input, Typography } from "@mui/material";
import React, { FC } from "react";
import { Link } from "react-router-dom";

import { showEntryPath } from "Routes";

interface Props {
  referredEntries: {
    id: number;
    name: string;
    entity: string;
  }[];
}

export const EntryReferral: FC<Props> = ({ referredEntries }) => {
  return (
    <Box className="row" id="referred_objects">
      <Box className="col">
        <Typography sx={{ fontSize: "16px" }}>
          関連づけられたエントリ(計{referredEntries.length})
        </Typography>
        <Input id="narrow_down_referral" placeholder="絞り込む" />
        <Box className="list-group" id="referral_entries">
          {referredEntries.map((entry) => (
            <Typography
              key={entry.id}
              component={Link}
              to={showEntryPath(entry.id)}
            >
              {entry.name} ({entry.entity})
            </Typography>
          ))}
        </Box>
      </Box>
    </Box>
  );
};
