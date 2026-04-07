import { Entity } from "@dmm-com/airone-apiclient-typescript-fetch";
import { Box } from "@mui/material";
import { styled } from "@mui/material/styles";
import { FC } from "react";
import { Control } from "react-hook-form";
import { UseFormSetValue } from "react-hook-form/dist/types/form";

import { ServerContext } from "../../services/ServerContext";

import { AttributesFields } from "./entityForm/AttributesFields";
import { BasicFields } from "./entityForm/BasicFields";
import { Schema } from "./entityForm/EntityFormSchema";
import { IsolationRulesFields } from "./entityForm/IsolationRulesFields";
import { WebhookFields } from "./entityForm/WebhookFields";

const StyledBox = styled(Box)(({ theme }) => ({
  width: theme.breakpoints.values.lg,
  margin: "0 auto",
  marginBottom: "60px",
  display: "flex",
  flexDirection: "column",
  gap: "60px",
}));

interface Props {
  control: Control<Schema>;
  setValue: UseFormSetValue<Schema>;
  referralEntities?: Entity[];
}

export const EntityForm: FC<Props> = ({
  control,
  setValue,
  referralEntities,
}) => {
  const serverContext = ServerContext.getInstance();

  return (
    <StyledBox>
      <BasicFields control={control} />

      <AttributesFields
        control={control}
        setValue={setValue}
        referralEntities={referralEntities ?? []}
      />

      <IsolationRulesFields
        control={control}
        referralEntities={referralEntities ?? []}
      />

      {(serverContext?.flags.webhook ?? true) && (
        <WebhookFields control={control} />
      )}
    </StyledBox>
  );
};
