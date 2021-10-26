import {
  ListItem,
  Table,
  TableBody,
  TableCell,
  TableRow,
} from "@material-ui/core";
import List from "@material-ui/core/List";
import PropTypes from "prop-types";
import React from "react";

import { groupsPath, showEntryPath } from "../../Routes";
import { DjangoContext } from "../../utils/DjangoContext";

function ElemString({ attrValue }) {
  return <div>{attrValue}</div>;
}

function ElemObject({ attrValue }) {
  return <a href={showEntryPath(attrValue.id)}>{attrValue.name}</a>;
}

function ElemNamedObject({ attrValue }) {
  const key = Object.keys(attrValue)[0];
  return (
    <div>
      <div>{key}</div>:{" "}
      <a href={showEntryPath(attrValue[key].id)}>{attrValue[key].name}</a>
    </div>
  );
}

function ElemGroup({ attrValue }) {
  return <a href={groupsPath()}>{attrValue.name}</a>;
}

function convertAttributeValue(attrName, attrInfo) {
  const djangoContext = DjangoContext.getInstance();

  if (attrInfo.value === null) {
  }

  switch (attrInfo.type) {
    case djangoContext.attrTypeValue.object:
      return <ElemObject attrValue={attrInfo.value} />;

    case djangoContext.attrTypeValue.string:
    case djangoContext.attrTypeValue.text:
    case djangoContext.attrTypeValue.boolean:
    case djangoContext.attrTypeValue.date:
      return <ElemString attrValue={attrInfo.value} />;

    case djangoContext.attrTypeValue.named_object:
      return <ElemNamedObject attrValue={attrInfo.value} />;

    case djangoContext.attrTypeValue.array_object:
      return (
        <List>
          {attrInfo.value.map((info, n) => {
            return (
              <ListItem key={n}>
                <ElemObject attrValue={info} />
              </ListItem>
            );
          })}
        </List>
      );

    case djangoContext.attrTypeValue.array_string:
      return (
        <List>
          {attrInfo.value.map((info, n) => {
            return (
              <ListItem key={n}>
                <ElemString attrValue={info} />
              </ListItem>
            );
          })}
        </List>
      );

    case djangoContext.attrTypeValue.array_named_object:
      return (
        <List>
          {attrInfo.value.map((info, n) => {
            return (
              <ListItem key={n}>
                <ElemNamedObject attrValue={info} />
              </ListItem>
            );
          })}
        </List>
      );

    case djangoContext.attrTypeValue.array_group:
      return (
        <List>
          {attrInfo.value.map((info, n) => {
            return (
              <ListItem key={n}>
                <ElemGroup attrValue={info} />
              </ListItem>
            );
          })}
        </List>
      );

    case djangoContext.attrTypeValue.group:
      return <ElemGroup attrValue={attrInfo.value} />;
  }
}

export default function EntryAttributes({ attributes }) {
  return (
    <Table>
      <TableBody>
        {Object.keys(attributes).map((attrname) => (
          <TableRow key={attrname}>
            <TableCell>{attrname}</TableCell>
            <TableCell>
              {convertAttributeValue(attrname, attributes[attrname])}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

EntryAttributes.propTypes = {
  attributes: PropTypes.object.isRequired,
};
