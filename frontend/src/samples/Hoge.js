import React, { useState } from "react";
import { sendRequest } from "./APIClient";

export function Hoge({ value }) {
  const [data, setData] = useState(value);

  const handleSubmit = () => {
    sendRequest(data);
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className={'form-title'}>
        <b>input title</b>
      </div>
      <textarea
        className={'in-hoge'}
        value={data}
        onChange={(e) => setData(e.target.value)}
      />
    </form>
  );
}
