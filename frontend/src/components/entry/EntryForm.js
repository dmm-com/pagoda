import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from "@material-ui/core";
import Button from "@material-ui/core/Button";
import { makeStyles } from "@material-ui/core/styles";
import PropTypes from "prop-types";
import React, { useState } from "react";
import { useHistory } from "react-router-dom";

import { entityEntriesPath } from "../../Routes";
import { createEntry } from "../../utils/AironeAPIClient";

import { EditAttributeValue } from "./EditAttributeValue";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

// FIXME handle attribute types
export function EntryForm({ entityId, entryId, initName = "", initAttributes = {} }) {
  const classes = useStyles();
  const history = useHistory();

  const [name, setName] = useState(initName);
  const [attributes, setAttributes] = useState(
    Object.keys(initAttributes).map((attrname) => {
      return {
        name: attrname,
        value: initAttributes[attrname].value,
        type: initAttributes[attrname].type,
      };
    })
  );

  const handleChangeAttribute = (event) => {
    console.log('[onix/handleChangeAttribute] event.target.hoge: ' + event.target.hoge);
    console.log('[onix/handleChangeAttribute] event.target.name: ' + event.target.name);
    console.log('[onix/handleChangeAttribute] input value: ' + event.target.value);

    /*
    attributes[event.target.name] = event.target.value;
    const updated = attributes.map((attribute) => {
      if (attribute.name === event.target.name) {
        attribute.value = event.target.value;
      }
      return attribute;
    });
    setAttributes(updated);
    */
  };

  const handleSubmit = (event) => {
    const attrs = attributes.map((attribute) => {
      return {
        id: "4",
        type: "2",
        value: [{ data: attribute.name }],
      };
    });

    console.log(attrs);

    if (entryId === undefined) {
      /*
      createEntry(entityId, name, attrs)
        .then((resp) => resp.json())
        .then((_) => history.push(entityEntriesPath(entityId)));
      */
    } else {
      /*
      updateEntry(entryId, name, attrs)
        .then((resp) => resp.json())
        .then((_) => history.push(entityEntriesPath(entityId)));
      */
    }

    event.preventDefault();
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="row">
        <div className="col">
          <div className="float-right">
            <Button
              className={classes.button}
              type="submit"
              variant="contained"
              color="secondary"
            >
              保存
            </Button>
          </div>
          <Table className="table table-bordered">
            <TableBody>
              <TableRow>
                <TableCell>エントリ名</TableCell>
                <TableCell>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </div>
      <Table className="table table-bordered">
        <TableHead>
          <TableRow>
            <TableCell>属性</TableCell>
            <TableCell>属性値</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {attributes.map((attribute, index) => (
            <TableRow key={index}>
              <TableCell>{attribute.name}</TableCell>
              <TableCell>
                <EditAttributeValue
                  attrName={attribute.name}
                  attrInfo={attribute}
                  handleChangeAttribute={handleChangeAttribute}
                />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <strong>(*)</strong> は必須項目
    </form>
  );
}

EntryForm.propTypes = {
  entityId: PropTypes.number.isRequired,
  initName: PropTypes.string,
  initAttributes: PropTypes.object,
};
