import Typography from "@material-ui/core/Typography";
import { Link } from "react-router-dom";
import React from "react";
import PropTypes from "prop-types";

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
              component={Link}
              to={`/new-ui/entities/${entityId}/entries/${entry.id}/show`}
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
  entityId: PropTypes.number.isRequired,
  referredEntries: PropTypes.array.isRequired,
};
