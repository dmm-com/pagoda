import Card from "@material-ui/core/Card";
import Checkbox from "@material-ui/core/Checkbox";
import Input from "@material-ui/core/Input";
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
import ListItemIcon from "@material-ui/core/ListItemIcon";
import ListItemText from "@material-ui/core/ListItemText";
import PropTypes from "prop-types";
import React from "react";

import { DjangoContext } from "../../utils/DjangoContext";

function handleNarrowDownEntries(event) {
  console.log('[onix/handleNarrowDownEntries(00)]');
};

function handleNarrowDownGroups(event) {
  console.log('[onix/handleNarrowDownGroups(00)]');
};

function ElemString({ attrValue, handleChange }) {
  return (
    <Input
      type="text"
      name={''}
      value={attrValue}
      onChange={handleChange}
    />
  );
}

function ElemBool({ attrValue, handleChange }) {
  return <Checkbox name={'hoge'} checked={attrValue} onChange={handleChange} />;
}

function ElemObject({ attrValue, handleChange }) {
  //  return <a href={showEntryPath(attrValue.id)}>{attrValue.name}</a>;
  return (
    <Card variant="outlined">
      <List>
        <>
          <ListItem key="1" dense button divider>
            <ListItemIcon>
              <Checkbox name={'hoge'} edge="start" tabIndex={-1} disableRipple onChange={handleChange} />
            </ListItemIcon>
            <ListItemText primary={attrValue.name} />
          </ListItem>
        </>
      </List>
      <Input text="text" placeholder="エントリ名で絞り込む" onChange={handleNarrowDownEntries}/>
    </Card>
  );
}

function ElemNamedObject({ attrValue, handleChange }) {
  return (
    <>
      <Input name={'hoge'} type="text" value={attrValue.key} onChange={handleChange}/>
      <ElemObject attrValue={attrValue} handleChange={handleChange}></ElemObject>
    </>
  );
}

function ElemGroup({ attrValue, handleChange }) {
  //  return <a href={groupsPath()}>{attrValue.name}</a>;
  return (
    <Card variant="outlined">
      <List>
        <>
          <ListItem key="1" dense button divider>
            <ListItemIcon>
              <Checkbox name={'hoge'} edge="start" tabIndex={-1} disableRipple />
            </ListItemIcon>
            <ListItemText primary={attrValue.name} />
          </ListItem>
        </>
      </List>
      <Input text="text" placeholder="グループ名で絞り込む" onChange={handleNarrowDownGroups}/>
    </Card>
  );
}

export function EditAttributeValue({
  attrName,
  attrInfo,
  handleChangeAttribute,
}) {
  const djangoContext = DjangoContext.getInstance();

  switch (attrInfo.type) {
    case djangoContext.attrTypeValue.object:
      return (
        <ElemObject
          attrValue={attrInfo.value}
          handleChange={handleChangeAttribute}
        />
      );

    case djangoContext.attrTypeValue.boolean:
      return (
        <ElemBool
          attrValue={attrInfo.value}
          handleChange={handleChangeAttribute}
        />
      );

    case djangoContext.attrTypeValue.string:
    case djangoContext.attrTypeValue.text:
    case djangoContext.attrTypeValue.date:
      return (
        <ElemString
          attrValue={attrInfo.value}
          handleChange={handleChangeAttribute}
        />
      );

    case djangoContext.attrTypeValue.named_object:
      return (
        <ElemNamedObject
          attrValue={attrInfo.value}
          handleChange={handleChangeAttribute}
        />
      );

    case djangoContext.attrTypeValue.array_object:
      return (
        <List>
          {attrInfo.value.map((info, n) => {
            return (
              <ListItem key={n}>
                <ElemObject
                  attrValue={info}
                  handleChange={handleChangeAttribute}
                />
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
                <ElemString
                  attrValue={info}
                  handleChange={handleChangeAttribute}
                />
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
                <ElemNamedObject
                  attrValue={info}
                  handleChange={handleChangeAttribute}
                />
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
                <ElemGroup
                  attrValue={info}
                  handleChange={handleChangeAttribute}
                />
              </ListItem>
            );
          })}
        </List>
      );

    case djangoContext.attrTypeValue.group:
      return (
        <ElemGroup
          attrValue={attrInfo.value}
          handleChange={handleChangeAttribute}
        />
      );
  }
}

EditAttributeValue.propTypes = {
  attrName: PropTypes.string.isRequired,
  attrInfo: PropTypes.object.isRequired,
};
