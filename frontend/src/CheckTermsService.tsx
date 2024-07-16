import React, { FC } from "react";
import { ServerContext } from "services/ServerContext";

export const CheckTermsService: FC<{ children: React.ReactNode }> = ({
  children,
}) => {

  const serverContext = ServerContext.getInstance();
  console.log(serverContext);
  console.log(document.cookie);

  return (
    <>hoge
    </>
  )
}