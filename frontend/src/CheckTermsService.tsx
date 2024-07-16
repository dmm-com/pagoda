import React, { FC } from "react";
import { ServerContext } from "services/ServerContext";
import { NonTermsServiceAgreement } from "./services/Exceptions";

function getCookieValue(key: string) {
  return ((document.cookie + ';').match(key + '=([^¥S;]*)') || [])[1];
}

export const CheckTermsService: FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const serverContext = ServerContext.getInstance();

  if (serverContext?.checkTermService && getCookieValue("AGREE_TERM_OF_SERVICE") !== "True" && serverContext.user !== undefined) {
    throw new NonTermsServiceAgreement();
  }

  return (<>{children}</>);
}