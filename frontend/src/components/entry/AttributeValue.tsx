import { Checkbox, Box, List, ListItem } from "@mui/material";
import PropTypes from "prop-types";
import * as React from "react";

import { groupsPath, showEntryPath } from "../../Routes";
import { DjangoContext } from "../../utils/DjangoContext";

function ElemBool({ attrValue }) {
  return <Checkbox checked={attrValue} disabled />;
}

ElemBool.propTypes = {
  attrValue: PropTypes.bool.isRequired,
};

function ElemString({ attrValue }) {
  return <div>{attrValue}</div>;
}

ElemString.propTypes = {
  attrValue: PropTypes.oneOfType([PropTypes.bool, PropTypes.string]).isRequired,
};

function ElemObject({ attrValue }) {
  return <a href={showEntryPath(attrValue.id)}>{attrValue.name}</a>;
}

ElemObject.propTypes = {
  attrValue: PropTypes.shape({
    id: PropTypes.number.isRequired,
    name: PropTypes.string.isRequired,
  }).isRequired,
};

function ElemNamedObject({ attrValue }) {
  console.log(`[onix/ElemNamedObject(00)]`);
  console.log(attrValue);

  const key = Object.keys(attrValue)[0];
  return (
    <Box>
      <Box>{key}</Box>:{" "}
      <a href={showEntryPath(attrValue[key].id)}>{attrValue[key].name}</a>
    </Box>
  );
}

ElemNamedObject.propTypes = {
  attrValue: PropTypes.object.isRequired,
};

function ElemGroup({ attrValue }) {
  return <a href={groupsPath()}>{attrValue.name}</a>;
}

ElemGroup.propTypes = {
  attrValue: PropTypes.shape({
    name: PropTypes.string.isRequired,
  }).isRequired,
};

export function AttributeValue({ attrName, attrInfo }) {
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
}

AttributeValue.propTypes = {
  attrName: PropTypes.string.isRequired,
  attrInfo: PropTypes.shape({
    type: PropTypes.number.isRequired,
    value: PropTypes.any.isRequired,
  }).isRequired,
};
