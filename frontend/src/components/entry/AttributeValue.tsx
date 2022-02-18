import { Checkbox, Box, List, ListItem } from "@mui/material";
import * as React from "react";
import { FC } from "react";
import { Link } from "react-router-dom";

import { groupsPath, entryDetailsPath } from "Routes";
import { DjangoContext } from "utils/DjangoContext";

const ElemBool: FC<{ attrValue: boolean }> = ({ attrValue }) => {
  return <Checkbox checked={attrValue} disabled sx={{ p: "0px" }} />;
};

const ElemString: FC<{ attrValue: string }> = ({ attrValue }) => {
  return (
    <Box>
      {
        // Separate line breaks with tags
        attrValue.split("\n").map((line, key) => (
          <Box key={key}>{line}</Box>
        ))
      }
    </Box>
  );
};

const ElemObject: FC<{ attrValue: { id: number; name: string } }> = ({
  attrValue,
}) => {
  return (
    <Box component={Link} to={entryDetailsPath(attrValue.id)}>
      {attrValue.name}
    </Box>
  );
};

const ElemNamedObject: FC<{ attrValue: any }> = ({ attrValue }) => {
  const key = Object.keys(attrValue)[0];
  return (
    <Box display="flex">
      <Box>{key}: </Box>
      <Box component={Link} to={entryDetailsPath(attrValue[key].id)}>
        {attrValue[key].name}
      </Box>
    </Box>
  );
};

const ElemGroup: FC<{ attrValue: { name: string } }> = ({ attrValue }) => {
  return (
    <Box component={Link} to={groupsPath}>
      {attrValue.name}
    </Box>
  );
};

interface Props {
  attrInfo: {
    type: number;
    value: any;
  };
}

export const AttributeValue: FC<Props> = ({ attrInfo }) => {
  const djangoContext = DjangoContext.getInstance();

  switch (attrInfo.type) {
    case djangoContext.attrTypeValue.object:
      return (
        <List>
          <ListItem>
            <ElemObject attrValue={attrInfo.value} />
          </ListItem>
        </List>
      );

    case djangoContext.attrTypeValue.string:
    case djangoContext.attrTypeValue.text:
    case djangoContext.attrTypeValue.date:
      return (
        <List>
          <ListItem>
            <ElemString attrValue={attrInfo.value} />
          </ListItem>
        </List>
      );

    case djangoContext.attrTypeValue.boolean:
      return (
        <List>
          <ListItem>
            <ElemBool attrValue={attrInfo.value} />
          </ListItem>
        </List>
      );

    case djangoContext.attrTypeValue.named_object:
      return (
        <List>
          <ListItem>
            <ElemNamedObject attrValue={attrInfo.value} />
          </ListItem>
        </List>
      );

    case djangoContext.attrTypeValue.group:
      return (
        <List>
          <ListItem>
            <ElemGroup attrValue={attrInfo.value} />
          </ListItem>
        </List>
      );

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
  }
};
