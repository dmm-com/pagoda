import { Checkbox, Box, List, ListItem } from "@mui/material";
import * as React from "react";
import { FC } from "react";

import { groupsPath, showEntryPath } from "../../Routes";
import { DjangoContext } from "../../utils/DjangoContext";

const ElemBool: FC<{ attrValue: boolean }> = ({ attrValue }) => {
  return <Checkbox checked={attrValue} disabled />;
};

const ElemString: FC<{ attrValue: string | boolean }> = ({ attrValue }) => {
  return <div>{attrValue}</div>;
};

const ElemObject: FC<{ attrValue: { id: number; name: string } }> = ({
  attrValue,
}) => {
  return <a href={showEntryPath(attrValue.id)}>{attrValue.name}</a>;
};

const ElemNamedObject: FC<{ attrValue: any }> = ({ attrValue }) => {
  console.log(`[onix/ElemNamedObject(00)]`);
  console.log(attrValue);

  const key = Object.keys(attrValue)[0];
  return (
    <Box>
      <Box>{key}</Box>:{" "}
      <a href={showEntryPath(attrValue[key].id)}>{attrValue[key].name}</a>
    </Box>
  );
};

const ElemGroup: FC<{ attrValue: { name: string } }> = ({ attrValue }) => {
  return <a href={groupsPath()}>{attrValue.name}</a>;
};

interface Props {
  attrName: string;
  attrInfo: {
    type: number;
    value: any;
  };
}

export const AttributeValue: FC<Props> = ({ attrName, attrInfo }) => {
  const djangoContext = DjangoContext.getInstance();

  switch (attrInfo.type) {
    case djangoContext.attrTypeValue.object:
      return <ElemObject attrValue={attrInfo.value} />;

    case djangoContext.attrTypeValue.string:
    case djangoContext.attrTypeValue.text:
    case djangoContext.attrTypeValue.date:
      return <ElemString attrValue={attrInfo.value} />;

    case djangoContext.attrTypeValue.boolean:
      return <ElemBool attrValue={attrInfo.value} />;

    case djangoContext.attrTypeValue.named_object:
      return <ElemNamedObject attrValue={attrInfo.value} />;

    case djangoContext.attrTypeValue.array_object:
      return (
        <List>
          {attrInfo.value.map((info, n) => (
            <ListItem key={n}>
              <ElemObject attrValue={info} />
            </ListItem>
          ))}
        </List>
      );

    case djangoContext.attrTypeValue.array_string:
      return (
        <List>
          {attrInfo.value.map((info, n) => (
            <ListItem key={n}>
              <ElemString attrValue={info} />
            </ListItem>
          ))}
        </List>
      );

    case djangoContext.attrTypeValue.array_named_object:
      return (
        <List>
          {attrInfo.value.map((info, n) => (
            <ListItem key={n}>
              <ElemNamedObject attrValue={info} />
            </ListItem>
          ))}
        </List>
      );

    case djangoContext.attrTypeValue.array_group:
      return (
        <List>
          {attrInfo.value.map((info, n) => (
            <ListItem key={n}>
              <ElemGroup attrValue={info} />
            </ListItem>
          ))}
        </List>
      );

    case djangoContext.attrTypeValue.group:
      return <ElemGroup attrValue={attrInfo.value} />;
  }
};
