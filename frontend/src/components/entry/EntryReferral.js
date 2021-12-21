import { Box, Input, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import { Link } from "react-router-dom";

import { showEntryPath } from "../../Routes";

export default function EntryReferral({ referredEntries }) {
  return (
    <Box className="row" id="referred_objects">
      <Box className="col">
        <h5 id="referral_entry_count">
          (エントリ数：{referredEntries.length})
        </h5>
        <Input id="narrow_down_referral" text="text" placeholder="絞り込む" />
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
}

EntryReferral.propTypes = {
  referredEntries: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      name: PropTypes.string.isRequired,
      entity: PropTypes.string.isRequired,
    })
  ).isRequired,
};
