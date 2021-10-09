import Typography from "@material-ui/core/Typography";
import PropTypes from "prop-types";
import React from "react";
import { Link } from "react-router-dom";

import { showEntryPath } from "../../Routes";

export default function EntryReferral({ entityId, referredEntries }) {
  return (
    <div className="row" id="referred_objects">
      <div className="col">
        <h5 id="referral_entry_count">
          (エントリ数：{referredEntries.length})
        </h5>
        <input id="narrow_down_referral" text="text" placeholder="絞り込む" />
        <div className="list-group" id="referral_entries">
          {referredEntries.map((entry) => (
            <Typography
              key={entry.id}
              component={Link}
              to={showEntryPath(entityId, entry.id)}
            >
              {entry.name} ({entry.entity})
            </Typography>
          ))}
        </div>
      </div>
    </div>
  );
}

EntryReferral.propTypes = {
  entityId: PropTypes.string.isRequired,
  referredEntries: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      name: PropTypes.string.isRequired,
      entity: PropTypes.string.isRequired,
    })
  ).isRequired,
};
