/**
 * @jest-environment jsdom
 */

import {
  initializeEntryInfo,
  isSubmittable,
} from "./Edit";
import { DjangoContext } from "services/DjangoContext";

Object.defineProperty(window, "django_context", {
  value: {
    user: {
      isSuperuser: true,
    },
  },
  writable: false,
});
const djangoContext = DjangoContext.getInstance();

test("initializeEntryInfo should return expect value", () => {
  const entity = {
    id: 1,
    name: "TestEntity",
    note: "hoge",
    status: 0,
    isToplevel: true,
    attrs: [{
      id: 2,
      index: 0,
      name: "attr",
      type: djangoContext.attrTypeValue.string,
      isMandatory: true,
      isDeleteInChain: true,
    }],
    webhooks: [],
    isPublic: true,
  }
  expect(initializeEntryInfo(entity)).toStrictEqual({
    "name": "",
    "attrs": {
      "attr": {
        "id": 2,
        "isMandatory": true,
        "schema":  {
          "id": 2,
          "name": "attr",
        },
        "type": 2,
        "value":  {
          "asArrayGroup":  [],
          "asArrayNamedObject":  [
             {
              "": null,
            },
          ],
          "asArrayObject":  [],
          "asArrayRole":  [],
          "asArrayString":  [
            "",
          ],
          "asBoolean": false,
          "asGroup": null,
          "asNamedObject":  {
            "": null,
          },
          "asObject": null,
          "asRole": null,
          "asString": "",
        },
      },
    },
  })
})

test("isSubmittable() returns false when entryInfo is null", () => {
  expect(isSubmittable(null)).toStrictEqual(false);
});

test("isSubmittable() returns true when entryInfo is changed", () => {
  // TBD
});

test("isSubmittable() returns true when entryInfo is not changed", () => {
  // TBD
});

test("convertAttrsFormatCtoS() returns expected value", () => {
  // TBD
});
