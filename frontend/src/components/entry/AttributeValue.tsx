import {
  EntryAttributeTypeTypeEnum,
  EntryAttributeValue,
  EntryAttributeValueGroup,
  EntryAttributeValueNamedObject,
  EntryAttributeValueObject,
  EntryAttributeValueRole,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { Box, Checkbox, Divider, List, ListItem } from "@mui/material";
import { styled } from "@mui/material/styles";
import * as React from "react";
import { FC } from "react";

import { AironeLink } from "components/common";
import { entryDetailsPath, groupsPath, rolePath } from "routes/Routes";

const StyledBox = styled(Box)(() => ({
  display: "flex",
  gap: "20px",
}));

const StyledList = styled(List)(() => ({
  padding: "0",
}));

const StyledListItem = styled(ListItem)(() => ({
  padding: "4px",
}));

const ElemBool: FC<{ attrValue: string | boolean }> = ({ attrValue }) => {
  const checkd =
    typeof attrValue === "string"
      ? attrValue.toLowerCase() === "true"
      : attrValue;
  return <Checkbox checked={checkd} disabled sx={{ p: "0px" }} />;
};

const ElemString: FC<{ attrValue: string }> = ({ attrValue }) => {
  return (
    <Box>
      {// Separate line breaks with tags
      attrValue?.split("\n").map((line, key) => <Box key={key}>{line}</Box>)}
    </Box>
  );
};

const ElemObject: FC<{
  attrValue: EntryAttributeValueObject | undefined;
}> = ({ attrValue }) => {
  return attrValue ? (
    <Box
      component={AironeLink}
      to={entryDetailsPath(attrValue.schema?.id ?? 0, attrValue.id)}
    >
      {attrValue.name}
    </Box>
  ) : (
    <Box />
  );
};

const ElemNamedObject: FC<{
  attrValue: EntryAttributeValueNamedObject;
}> = ({ attrValue }) => {
  return attrValue ? (
    <StyledBox>
      <Box>{attrValue.name}</Box>
      <Divider orientation="vertical" flexItem />
      {attrValue.object ? (
        <Box
          component={AironeLink}
          to={entryDetailsPath(
            attrValue.object.schema?.id ?? 0,
            attrValue.object.id ?? 0,
          )}
        >
          {attrValue.object.name}
        </Box>
      ) : (
        <Box />
      )}
    </StyledBox>
  ) : (
    <Box />
  );
};

const ElemGroup: FC<{ attrValue: EntryAttributeValueGroup | undefined }> = ({
  attrValue,
}) => {
  return attrValue ? (
    <Box component={AironeLink} to={groupsPath()}>
      {attrValue.name}
    </Box>
  ) : (
    <Box />
  );
};

const ElemRole: FC<{ attrValue: EntryAttributeValueRole | undefined }> = ({
  attrValue,
}) => {
  return attrValue ? (
    <Box component={AironeLink} to={rolePath(attrValue.id)}>
      {attrValue.name}
    </Box>
  ) : (
    <Box />
  );
};

interface Props {
  attrInfo: {
    type: number;
    value: EntryAttributeValue;
  };
}

export const AttributeValue: FC<Props> = ({ attrInfo }) => {
  switch (attrInfo.type) {
    case EntryAttributeTypeTypeEnum.OBJECT:
      return (
        <StyledList>
          <StyledListItem>
            <ElemObject attrValue={attrInfo.value.asObject ?? undefined} />
          </StyledListItem>
        </StyledList>
      );

    case EntryAttributeTypeTypeEnum.STRING:
    case EntryAttributeTypeTypeEnum.TEXT:
    case EntryAttributeTypeTypeEnum.DATE:
    case EntryAttributeTypeTypeEnum.DATETIME:
      return (
        <StyledList>
          <StyledListItem>
            <ElemString attrValue={attrInfo.value.asString ?? ""} />
          </StyledListItem>
        </StyledList>
      );

    case EntryAttributeTypeTypeEnum.BOOLEAN:
      return (
        <StyledList>
          <StyledListItem>
            <ElemBool attrValue={attrInfo.value.asBoolean ?? false} />
          </StyledListItem>
        </StyledList>
      );

    case EntryAttributeTypeTypeEnum.NAMED_OBJECT:
      return (
        <StyledList>
          <StyledListItem>
            <ElemNamedObject
              attrValue={
                attrInfo.value.asNamedObject ?? { name: "", object: null }
              }
            />
          </StyledListItem>
        </StyledList>
      );

    case EntryAttributeTypeTypeEnum.GROUP:
      return (
        <StyledList>
          <StyledListItem>
            <ElemGroup attrValue={attrInfo.value.asGroup ?? undefined} />
          </StyledListItem>
        </StyledList>
      );

    case EntryAttributeTypeTypeEnum.ROLE:
      return (
        <StyledList>
          <StyledListItem>
            <ElemRole attrValue={attrInfo.value.asRole ?? undefined} />
          </StyledListItem>
        </StyledList>
      );

    case EntryAttributeTypeTypeEnum.ARRAY_OBJECT:
      return (
        <StyledList>
          {attrInfo.value?.asArrayObject?.map((info, n) => (
            <StyledListItem key={n}>
              <ElemObject attrValue={info} />
            </StyledListItem>
          ))}
        </StyledList>
      );

    case EntryAttributeTypeTypeEnum.ARRAY_STRING:
      return (
        <StyledList>
          {attrInfo.value?.asArrayString?.map((info, n) => (
            <StyledListItem key={n}>
              <ElemString attrValue={info} />
            </StyledListItem>
          ))}
        </StyledList>
      );

    case EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT:
      return (
        <StyledList>
          {attrInfo.value?.asArrayNamedObject?.map((info, n) => (
            <StyledListItem key={n}>
              <ElemNamedObject attrValue={info} />
            </StyledListItem>
          ))}
        </StyledList>
      );

    case EntryAttributeTypeTypeEnum.ARRAY_GROUP:
      return (
        <StyledList>
          {attrInfo.value?.asArrayGroup?.map((info, n) => (
            <StyledListItem key={n}>
              <ElemGroup attrValue={info} />
            </StyledListItem>
          ))}
        </StyledList>
      );

    case EntryAttributeTypeTypeEnum.ARRAY_ROLE:
      return (
        <StyledList>
          {attrInfo.value?.asArrayRole?.map((info, n) => (
            <StyledListItem key={n}>
              <ElemRole attrValue={info} />
            </StyledListItem>
          ))}
        </StyledList>
      );

    default:
      throw new Error(`unkwnon attribute type: ${attrInfo.type}`);
  }
};
