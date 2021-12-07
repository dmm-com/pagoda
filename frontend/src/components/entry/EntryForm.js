import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from "@material-ui/core";
import { makeStyles } from "@material-ui/core/styles";
import PropTypes from "prop-types";
import React, { useState } from "react";
import { useHistory } from "react-router-dom";
import { showEntryPath } from "../../Routes";

import {
  getAttrReferrals,
  getGroups,
  updateEntry,
} from "../../utils/AironeAPIClient";
import { DjangoContext } from "../../utils/DjangoContext";

import { EditAttributeValue } from "./EditAttributeValue";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

// FIXME handle attribute types
export function EntryForm({
  entityId,
  entryId,
  initName = "",
  initAttributes = {},
}) {
  const djangoContext = DjangoContext.getInstance();
  const classes = useStyles();
  const history = useHistory();

  console.log(`[onix/00] initAttributes`);
  console.log(initAttributes);

  /* FIXME attach checked flag to entry-like types
   */
  const changedInitAttr = Object.keys(initAttributes)
    .map((attrName) => {
      const attrValue = initAttributes[attrName];
      switch (attrValue.type) {
        case djangoContext.attrTypeValue.group:
        case djangoContext.attrTypeValue.object:
          return {
            name: attrName,
            value: {
              id: attrValue.id,
              type: attrValue.type,
              value: [
                {
                  ...attrValue.value,
                  checked: true,
                },
              ],
            },
          };

        case djangoContext.attrTypeValue.named_object:
          const name = Object.keys(attrValue.value)[0];
          const value = attrValue.value[name];

          return {
            name: attrName,
            value: {
              id: attrValue.id,
              type: attrValue.type,
              value: {
                [name]: [
                  {
                    id: value.id,
                    name: value.name,
                    checked: true,
                  },
                ],
              },
            },
          };

        case djangoContext.attrTypeValue.array_group:
        case djangoContext.attrTypeValue.array_object:
          return {
            name: attrName,
            value: {
              id: attrValue.id,
              type: attrValue.type,
              value: attrValue.value.map((val) => {
                return [
                  {
                    ...val,
                    checked: true,
                  },
                ];
              }),
            },
          };

        case djangoContext.attrTypeValue.array_named_object:
          return {
            name: attrName,
            value: {
              id: attrValue.id,
              type: attrValue.type,
              value: attrValue.value.map((val) => {
                const name = Object.keys(val)[0];
                const value = val[name];
                return {
                  [name]: [
                    {
                      ...value,
                      checked: true,
                    },
                  ],
                };
              }),
            },
          };

        default:
          return {
            name: attrName,
            value: attrValue,
          };
      }
    })
    .reduce((acc, elem) => {
      acc[elem.name] = elem.value;
      return acc;
    }, {});

  const [name, setName] = useState(initName);
  const [attributes, setAttributes] = useState(changedInitAttr);

  const handleChangeAttribute = (event, name, valueInfo) => {
    console.log("[onix/handleChangeAttribute(00)] name: " + name);
    console.log("[onix/handleChangeAttribute(00)] valueInfo: ");
    console.log(valueInfo);
    console.log(`[onix/handleChangeAttribute(00/before)] attributes`);
    console.log(attributes);

    switch (valueInfo.type) {
      case djangoContext.attrTypeValue.string:
        attributes[name].value = valueInfo.value;
        setAttributes({ ...attributes });
        break;

      case djangoContext.attrTypeValue.object:
      case djangoContext.attrTypeValue.group:
        attributes[name].value = attributes[name].value.map((x) => {
          return {
            id: x.id,
            name: x.name,
            checked: x.id == valueInfo.id && valueInfo.checked ? true : false,
          };
        });
        setAttributes({ ...attributes });
        break;

      case djangoContext.attrTypeValue.array_string:
        attributes[name].value[valueInfo.index] = valueInfo.value;
        setAttributes({ ...attributes });
        break;

      case djangoContext.attrTypeValue.array_object:
      case djangoContext.attrTypeValue.array_group:
        attributes[name].value[valueInfo.index] = attributes[name].value[
          valueInfo.index
        ].map((x) => {
          return {
            id: x.id,
            name: x.name,
            checked: x.id == valueInfo.id && valueInfo.checked ? true : false,
          };
        });
        setAttributes({ ...attributes });
        break;

      case djangoContext.attrTypeValue.named_object:
        if (event.target.type === "text") {
          attributes[name].value = {
            [valueInfo.key]: Object.values(attributes[name].value)[0],
          };
        }
        if (event.target.type === "radio") {
          const key = Object.keys(attributes[name].value)[0];
          attributes[name].value[key] = attributes[name].value[key].map((x) => {
            return {
              id: x.id,
              name: x.name,
              checked: x.id == valueInfo.id && valueInfo.checked ? true : false,
            };
          });
        }
        setAttributes({ ...attributes });
        break;

      case djangoContext.attrTypeValue.array_named_object:
        if (event.target.type === "text") {
          attributes[name].value[valueInfo.index] = {
            [valueInfo.key]: Object.values(
              attributes[name].value[valueInfo.index]
            )[0],
          };
        }
        if (event.target.type === "radio") {
          const key = Object.keys(attributes[name].value[valueInfo.index])[0];
          attributes[name].value[valueInfo.index][key] = attributes[name].value[
            valueInfo.index
          ][key].map((x) => {
            return {
              id: x.id,
              name: x.name,
              checked: x.id == valueInfo.id && valueInfo.checked ? true : false,
            };
          });
        }
        setAttributes({ ...attributes });
        break;

      case djangoContext.attrTypeValue.boolean:
        attributes[name].value = valueInfo.checked;
        setAttributes({ ...attributes });
        break;

      case djangoContext.attrTypeValue.date:
        attributes[name].value = valueInfo.value;
        setAttributes({ ...attributes });
        break;

      case djangoContext.attrTypeValue.text:
        attributes[name].value = valueInfo.value;
        setAttributes({ ...attributes });
        break;

      default:
        console.log("[onix/handleChangeAttribute/switch] valueInfo: ");
        console.log(valueInfo);
    }

    console.log(`[onix/handleChangeAttribute(00/after)] attributes`);
    console.log(attributes);
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

  const handleNarrowDownGroups = async (e, attrName, attrType) => {
    const resp = await getGroups();
    const refs = await resp.json();
    const userInputValue = e.target.value;

    function _getUpdatedValues(currentValue) {
      return refs
        .filter((r) => {
          return (
            r.name.includes(userInputValue) ||
            currentValue.find((x) => x.id === r.id && x.checked)
          );
        })
        .map((r) => {
          // return refs.map((r) => {
          return {
            id: r.id,
            name: r.name,
            checked: currentValue.find((x) => x.id == r.id)?.checked
              ? true
              : false,
          };
        });
    }

    switch (attrType) {
      case djangoContext.attrTypeValue.group:
        attributes[attrName].value = _getUpdatedValues(
          attributes[attrName].value
        );

        setAttributes({ ...attributes });
        break;

      case djangoContext.attrTypeValue.array_group:
        attributes[attrName].value = attributes[attrName].value.map((curr) => {
          return _getUpdatedValues(curr);
        });

        setAttributes({ ...attributes });
        break;
    }
  };

  const handleNarrowDownEntries = async (e, attrId, attrName, attrType) => {
    const resp = await getAttrReferrals(attrId);
    const refs = await resp.json();
    const userInputValue = e.target.value;

    function _getUpdatedValues(currentValue) {
      return refs.results
        .filter((r) => {
          return (
            r.name.includes(userInputValue) ||
            currentValue.find((x) => x.id === r.id && x.checked)
          );
        })
        .map((r) => {
          return {
            id: r.id,
            name: r.name,
            checked: currentValue.find((x) => x.id == r.id)?.checked
              ? true
              : false,
          };
        });
    }

    switch (attrType) {
      case djangoContext.attrTypeValue.object:
        attributes[attrName].value = _getUpdatedValues(
          attributes[attrName].value
        );

        setAttributes({ ...attributes });
        break;

      case djangoContext.attrTypeValue.array_object:
        attributes[attrName].value = attributes[attrName].value.map((curr) => {
          return _getUpdatedValues(curr);
        });

        setAttributes({ ...attributes });
        break;

      case djangoContext.attrTypeValue.named_object:
        let attrKey = Object.keys(attributes[attrName].value)[0];
        attributes[attrName].value[attrKey] = _getUpdatedValues(
          attributes[attrName].value[attrKey]
        );

        setAttributes({ ...attributes });
        break;

      case djangoContext.attrTypeValue.array_named_object:
        attributes[attrName].value = attributes[attrName].value.map((curr) => {
          let attrKey = Object.keys(curr)[0];
          return { attrKey: _getUpdatedValues(curr[attrKey]) };
        });

        setAttributes({ ...attributes });
        break;
    }
  };

  const handleSubmit = (event) => {
    const updatedAttr = Object.entries(attributes)
      // for temporary
      .filter(
        ([attrName, attrValue]) =>
          attrValue.type === djangoContext.attrTypeValue.object
      )
      .map(([attrName, attrValue]) => {
        console.log("handleSubmit");
        console.log(attrValue);
        switch (attrValue.type) {
          case djangoContext.attrTypeValue.string:
            return {
              entity_attr_id: attrValue.schema_id,
              id: String(attrValue.id),
              type: attrValue.type,
              value: [
                {
                  data: attrValue.value,
                },
              ],
              referral_key: [],
            };

          case djangoContext.attrTypeValue.object:
            return {
              entity_attr_id: "",
              id: String(attrValue.id),
              type: attrValue.type,
              value: [
                {
                  data: attrValue.value.filter((x) => x.checked)[0].id ?? "",
                  index: String(0),
                },
              ],
              referral_key: [],
            };
        }
      });

    console.log(`[onix/handleSubmit] entryId` + entryId);
    console.log(updatedAttr);

    // FIXME entryId is always undefined????
    if (entryId === undefined) {
      createEntry(entityId, name, attrs)
        .then((resp) => resp.json())
        .then((_) => history.push(entityEntriesPath(entityId)));
    } else {
      updateEntry(entryId, name, updatedAttr)
        .then((resp) => resp.json())
        .then((_) => history.push(showEntryPath(entryId)));
    }

    // TODO reload
    // event.preventDefault();
  };

  return (
    <div>
      {/* ^ FIXME form??? */}
      <button onClick={handleSubmit}>submit</button>
      <div className="row">
        <div className="col">
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
          {Object.keys(attributes).map((attributeName, index) => (
            <TableRow key={index}>
              <TableCell>{attributeName}</TableCell>
              <TableCell>
                <EditAttributeValue
                  attrName={attributeName}
                  attrInfo={attributes[attributeName]}
                  handleChangeAttribute={handleChangeAttribute}
                  handleNarrowDownEntries={handleNarrowDownEntries}
                  handleNarrowDownGroups={handleNarrowDownGroups}
                />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <strong>(*)</strong> は必須項目
    </div>
  );
}

EntryForm.propTypes = {
  entityId: PropTypes.number.isRequired,
  initName: PropTypes.string,
  initAttributes: PropTypes.object,
};
