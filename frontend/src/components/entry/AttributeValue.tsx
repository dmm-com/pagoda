import {
  EntryAttributeTypeTypeEnum,
  EntryAttributeValue,
  EntryAttributeValueGroup,
  EntryAttributeValueNamedObject,
  EntryAttributeValueObject,
  EntryAttributeValueRole,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { Box, Checkbox, Chip, Divider, List, ListItem } from "@mui/material";
import { styled } from "@mui/material/styles";
import { FC, ReactNode } from "react";

import { ExternalLinkConfirmDialog } from "./ExternalLinkConfirmDialog";

import { AironeLink } from "components/common";
import { entryDetailsPath, groupsPath, rolePath } from "routes/Routes";

const StyledBox = styled(Box)(() => ({
  display: "flex",
  gap: "20px",
}));

export const AttributeValueList = styled(List)(() => ({
  padding: "0",
}));

export const AttributeValueListItem = styled(ListItem)(({ theme }) => ({
  padding: "4px",
  "&:not(:last-child)": {
    borderBottom: `1px solid ${theme.palette.divider}`,
  },
}));

const URL_RE = /(https?:\/\/[^\s<>()]+[^\s<>().,;:"'\]])/g;

const renderTextWithLinks = (text: string): ReactNode[] => {
  const parts: ReactNode[] = [];
  let lastIndex = 0;

  for (const match of text.matchAll(URL_RE)) {
    const url = match[0];
    const index = match.index ?? 0;

    if (index > lastIndex) {
      parts.push(text.slice(lastIndex, index));
    }

    parts.push(
      <ExternalLinkConfirmDialog key={`${index}-${url}`} url={url}>
        {url}
      </ExternalLinkConfirmDialog>,
    );

    lastIndex = index + url.length;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts.length > 0 ? parts : [text];
};

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
      {attrValue?.split("\n").map((line, key) => (
        <Box key={key}>{renderTextWithLinks(line)}</Box>
      ))}
    </Box>
  );
};

const ElemNumber: FC<{ attrValue: number | null }> = ({ attrValue }) => {
  return <Box>{attrValue != null ? attrValue.toString() : ""}</Box>;
};

const ElemObject: FC<{
  attrValue: EntryAttributeValueObject | undefined;
}> = ({ attrValue }) => {
  return attrValue ? (
    <Box
      component={AironeLink}
      to={entryDetailsPath(attrValue.schema?.id ?? 0, attrValue.id)}
    >
      {attrValue.displayLabel ?? attrValue.name}
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
      <Chip
        label={attrValue.name || "\u00A0"}
        size="small"
        variant="outlined"
      />
      <Divider orientation="vertical" flexItem />
      {attrValue.object ? (
        <Box
          component={AironeLink}
          to={entryDetailsPath(
            attrValue.object.schema?.id ?? 0,
            attrValue.object.id ?? 0,
          )}
        >
          {attrValue.object.displayLabel ?? attrValue.object.name}
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

const ElemSelect: FC<{
  attrValue: { value: string; label: string } | null | undefined;
}> = ({ attrValue }) => {
  return attrValue ? (
    <Chip label={attrValue.label || " "} size="small" variant="outlined" />
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
        <AttributeValueList>
          <AttributeValueListItem>
            <ElemObject attrValue={attrInfo.value.asObject ?? undefined} />
          </AttributeValueListItem>
        </AttributeValueList>
      );

    case EntryAttributeTypeTypeEnum.STRING:
    case EntryAttributeTypeTypeEnum.TEXT:
    case EntryAttributeTypeTypeEnum.DATE:
    case EntryAttributeTypeTypeEnum.DATETIME:
      return (
        <AttributeValueList>
          <AttributeValueListItem>
            <ElemString attrValue={attrInfo.value.asString ?? ""} />
          </AttributeValueListItem>
        </AttributeValueList>
      );

    case EntryAttributeTypeTypeEnum.BOOLEAN:
      return (
        <AttributeValueList>
          <AttributeValueListItem>
            <ElemBool attrValue={attrInfo.value.asBoolean ?? false} />
          </AttributeValueListItem>
        </AttributeValueList>
      );

    case EntryAttributeTypeTypeEnum.NUMBER:
      return (
        <AttributeValueList>
          <AttributeValueListItem>
            <ElemNumber attrValue={attrInfo.value.asNumber ?? null} />
          </AttributeValueListItem>
        </AttributeValueList>
      );

    case EntryAttributeTypeTypeEnum.NAMED_OBJECT:
      return (
        <AttributeValueList>
          <AttributeValueListItem>
            <ElemNamedObject
              attrValue={
                attrInfo.value.asNamedObject ?? { name: "", object: null }
              }
            />
          </AttributeValueListItem>
        </AttributeValueList>
      );

    case EntryAttributeTypeTypeEnum.GROUP:
      return (
        <AttributeValueList>
          <AttributeValueListItem>
            <ElemGroup attrValue={attrInfo.value.asGroup ?? undefined} />
          </AttributeValueListItem>
        </AttributeValueList>
      );

    case EntryAttributeTypeTypeEnum.ROLE:
      return (
        <AttributeValueList>
          <AttributeValueListItem>
            <ElemRole attrValue={attrInfo.value.asRole ?? undefined} />
          </AttributeValueListItem>
        </AttributeValueList>
      );

    case EntryAttributeTypeTypeEnum.ARRAY_OBJECT:
      return (
        <AttributeValueList>
          {attrInfo.value?.asArrayObject?.map((info, n) => (
            <AttributeValueListItem key={n}>
              <ElemObject attrValue={info} />
            </AttributeValueListItem>
          ))}
        </AttributeValueList>
      );

    case EntryAttributeTypeTypeEnum.ARRAY_STRING:
      return (
        <AttributeValueList>
          {attrInfo.value?.asArrayString?.map((info, n) => (
            <AttributeValueListItem key={n}>
              <ElemString attrValue={info} />
            </AttributeValueListItem>
          ))}
        </AttributeValueList>
      );

    case EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT:
    case EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT_BOOLEAN:
      return (
        <AttributeValueList>
          {attrInfo.value?.asArrayNamedObject?.map((info, n) => (
            <AttributeValueListItem key={n}>
              <ElemNamedObject attrValue={info} />
            </AttributeValueListItem>
          ))}
        </AttributeValueList>
      );

    case EntryAttributeTypeTypeEnum.ARRAY_GROUP:
      return (
        <AttributeValueList>
          {attrInfo.value?.asArrayGroup?.map((info, n) => (
            <AttributeValueListItem key={n}>
              <ElemGroup attrValue={info} />
            </AttributeValueListItem>
          ))}
        </AttributeValueList>
      );

    case EntryAttributeTypeTypeEnum.ARRAY_ROLE:
      return (
        <AttributeValueList>
          {attrInfo.value?.asArrayRole?.map((info, n) => (
            <AttributeValueListItem key={n}>
              <ElemRole attrValue={info} />
            </AttributeValueListItem>
          ))}
        </AttributeValueList>
      );

    case EntryAttributeTypeTypeEnum.ARRAY_NUMBER:
      return (
        <AttributeValueList>
          {attrInfo.value?.asArrayNumber?.map((info, n) => (
            <AttributeValueListItem key={n}>
              <ElemNumber attrValue={info} />
            </AttributeValueListItem>
          ))}
        </AttributeValueList>
      );

    case EntryAttributeTypeTypeEnum.SELECT:
      return (
        <AttributeValueList>
          <AttributeValueListItem>
            <ElemSelect attrValue={attrInfo.value.asSelect ?? null} />
          </AttributeValueListItem>
        </AttributeValueList>
      );

    case EntryAttributeTypeTypeEnum.MULTI_SELECT:
      return (
        <AttributeValueList>
          {attrInfo.value?.asMultiSelect?.map((info, n) => (
            <AttributeValueListItem key={n}>
              <ElemSelect attrValue={info} />
            </AttributeValueListItem>
          ))}
        </AttributeValueList>
      );

    default:
      throw new Error(`unkwnon attribute type: ${attrInfo.type}`);
  }
};
