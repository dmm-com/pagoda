import Typography from "@material-ui/core/Typography";
import React, { FC } from "react";
import { Link } from "react-router-dom";

import { showEntryPath } from "../../Routes";

interface Props {
  referredEntries: {
    id: number;
    name: string;
    entity: string;
  }[];
}

export const EntryReferral: FC<Props> = ({ referredEntries }) => {
  return (
    <div className="row" id="referred_objects">
      <div className="col">
        <h5 id="referral_entry_count">
          (エントリ数：{referredEntries.length})
        </h5>
        <input id="narrow_down_referral" placeholder="絞り込む" />
        <div className="list-group" id="referral_entries">
          {referredEntries.map((entry) => (
            <Typography
              key={entry.id}
              component={Link}
              to={showEntryPath(entry.id)}
            >
              {entry.name} ({entry.entity})
            </Typography>
          ))}
        </div>
      </div>
    </div>
  );
};
