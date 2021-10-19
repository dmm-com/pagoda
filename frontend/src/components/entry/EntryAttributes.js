import { Table, TableBody, TableCell, TableRow } from "@material-ui/core";
import PropTypes from "prop-types";
import React from "react";

import { DjangoContext } from "../../utils/DjangoContext";

function ElemString({ attrValue }) {
  return <div>{attrValue}</div>;
}

function ElemObject({ attrValue }) {
  return <a href={`/entry/show/${attrValue.id}`}>{attrValue.name}</a>;
}

function ElemNamedObject({ attrValue }) {
  const key = Object.keys(attrValue)[0];
  return (
    <div>
      <div>{key}</div>:{" "}
      <a href={`/entry/show/${attrValue[key].id}`}>{attrValue[key].name}</a>
    </div>
  );
}

function ElemGroup({ attrValue }) {
  return <a href={`/group`}>{attrValue.name}</a>;
}

function convertAttributeValue(attrName, attrInfo) {
  const djangoContext = DjangoContext.getInstance();

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
        {attributes.map((attr) => (
          <TableRow key={attr.name}>
            <TableCell>{attr.name}</TableCell>
            <TableCell>
              {convertAttributeValue(attr.name, attr.value)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

EntryAttributes.propTypes = {
  attributes: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      value: PropTypes.string.isRequired,
    })
  ).isRequired,
};
