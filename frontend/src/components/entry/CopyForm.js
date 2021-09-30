import Button from "@material-ui/core/Button";
import PropTypes from "prop-types";
import React, { useState } from "react";
import { useHistory } from "react-router-dom";

import { copyEntry } from "../../utils/AironeAPIClient";

export default function CopyForm({ entityId, entryId }) {
  const history = useHistory();

  const [entries, setEntries] = useState("");

  const handleSubmit = (event) => {
    copyEntry(entryId, entries).then((_) =>
      history.push(`/new-ui/entities/${entityId}/entries`)
    );
    event.preventDefault();
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="row">
        <div className="col">
          <div className="float-left">
            入力した各行毎に同じ属性値を持つ別エントリを作成
          </div>
          <div className="float-right">
            <Button type="submit" variant="contained">
              コピー
            </Button>
          </div>
        </div>
      </div>
      <div className="row">
        <div className="col-5">
          <textarea
            cols={40}
            rows={10}
            value={entries}
            onChange={(e) => setEntries(e.target.value)}
          />
        </div>
      </div>
    </form>
  );
}

CopyForm.propTypes = {
  entityId: PropTypes.string.isRequired,
  entryId: PropTypes.string.isRequired,
};
