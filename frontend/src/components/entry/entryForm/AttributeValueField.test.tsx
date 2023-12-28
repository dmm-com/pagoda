/**
 * @jest-environment jsdom
 */

import { EntryAttributeTypeTypeEnum } from "@dmm-com/airone-apiclient-typescript-fetch";
import { zodResolver } from "@hookform/resolvers/zod";
import { act, render, renderHook, screen } from "@testing-library/react";
import React from "react";
import { useForm } from "react-hook-form";

import { TestWrapper } from "../../../TestWrapper";

import { AttributeValueField } from "./AttributeValueField";
import { schema, Schema } from "./EntryFormSchema";

describe("AttributeValue", () => {
  const defaultValues: Schema = {
    name: "entry",
    schema: {
      id: 1,
      name: "entity",
    },
    attrs: {
      // primitive types
      string: {
        type: EntryAttributeTypeTypeEnum.STRING,
        index: 0,
        isMandatory: false,
        schema: {
          id: 1,
          name: "string",
        },
        value: {
          asString: "value",
        },
      },
      text: {
        type: EntryAttributeTypeTypeEnum.TEXT,
        index: 1,
        isMandatory: false,
        schema: {
          id: 1,
          name: "text",
        },
        value: {
          asString: "value",
        },
      },
      date: {
        type: EntryAttributeTypeTypeEnum.DATE,
        index: 2,
        isMandatory: false,
        schema: {
          id: 1,
          name: "date",
        },
        value: {
          asString: "2020-01-01",
        },
      },
      boolean: {
        type: EntryAttributeTypeTypeEnum.BOOLEAN,
        index: 3,
        isMandatory: false,
        schema: {
          id: 1,
          name: "boolean",
        },
        value: {
          asBoolean: true,
        },
      },
      object: {
        type: EntryAttributeTypeTypeEnum.OBJECT,
        index: 4,
        isMandatory: false,
        schema: {
          id: 1,
          name: "object",
        },
        value: {
          asObject: {
            id: 100,
            name: "object1",
          },
        },
      },
      namedObject: {
        type: EntryAttributeTypeTypeEnum.NAMED_OBJECT,
        index: 5,
        isMandatory: false,
        schema: {
          id: 1,
          name: "named_object",
        },
        value: {
          asNamedObject: {
            name: "name1",
            object: {
              id: 100,
              name: "object1",
            },
          },
        },
      },
      group: {
        type: EntryAttributeTypeTypeEnum.GROUP,
        index: 6,
        isMandatory: false,
        schema: {
          id: 1,
          name: "group",
        },
        value: {
          asGroup: { id: 100, name: "group1" },
        },
      },
      role: {
        type: EntryAttributeTypeTypeEnum.ROLE,
        index: 7,
        isMandatory: false,
        schema: {
          id: 1,
          name: "role",
        },
        value: {
          asRole: { id: 100, name: "role1" },
        },
      },

      // array types
      arrayString: {
        type: EntryAttributeTypeTypeEnum.ARRAY_STRING,
        index: 8,
        isMandatory: false,
        schema: {
          id: 1,
          name: "array_string",
        },
        value: {
          asArrayString: [{ value: "hoge" }, { value: "fuga" }],
        },
      },
      arrayObject: {
        type: EntryAttributeTypeTypeEnum.ARRAY_OBJECT,
        index: 9,
        isMandatory: false,
        schema: {
          id: 1,
          name: "array_object",
        },
        value: {
          asArrayObject: [
            { id: 100, name: "object1" },
            { id: 200, name: "object2" },
          ],
        },
      },
      arrayNamedObject: {
        type: EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT,
        index: 10,
        isMandatory: false,
        schema: {
          id: 1,
          name: "array_named_object",
        },
        value: {
          asArrayNamedObject: [
            {
              name: "name1",
              object: {
                id: 100,
                name: "object1",
              },
              _boolean: false,
            },
            {
              name: "name2",
              object: {
                id: 200,
                name: "object2",
              },
              _boolean: false,
            },
          ],
        },
      },
      arrayGroup: {
        type: EntryAttributeTypeTypeEnum.ARRAY_GROUP,
        index: 11,
        isMandatory: false,
        schema: {
          id: 1,
          name: "array_group",
        },
        value: {
          asArrayGroup: [
            { id: 100, name: "group1" },
            { id: 200, name: "group2" },
          ],
        },
      },
      arrayRole: {
        type: EntryAttributeTypeTypeEnum.ARRAY_ROLE,
        index: 12,
        isMandatory: false,
        schema: {
          id: 1,
          name: "array_role",
        },
        value: {
          asArrayRole: [
            { id: 100, name: "role1" },
            { id: 200, name: "role2" },
          ],
        },
      },
    },
  };

  const cases: Array<{
    name: string;
    type: number;
    schemaId: number;
    fn: () => void;
  }> = [
    // primitive types
    {
      name: "string",
      type: EntryAttributeTypeTypeEnum.STRING,
      schemaId: 0,
      fn: () => {
        expect(screen.getByRole("textbox")).toBeInTheDocument();
      },
    },
    {
      name: "text",
      type: EntryAttributeTypeTypeEnum.TEXT,
      schemaId: 1,
      fn: () => {
        expect(screen.getByRole("textbox")).toBeInTheDocument();
      },
    },
    {
      name: "date",
      type: EntryAttributeTypeTypeEnum.DATE,
      schemaId: 2,
      fn: () => {
        expect(screen.getByRole("textbox")).toBeInTheDocument();
      },
    },
    {
      name: "boolean",
      type: EntryAttributeTypeTypeEnum.BOOLEAN,
      schemaId: 3,
      fn: () => {
        expect(screen.getByRole("checkbox")).toBeInTheDocument();
      },
    },
    {
      name: "object",
      type: EntryAttributeTypeTypeEnum.OBJECT,
      schemaId: 4,
      fn: () => {
        expect(screen.getByRole("combobox")).toBeInTheDocument();
      },
    },
    {
      name: "named-object",
      type: EntryAttributeTypeTypeEnum.NAMED_OBJECT,
      schemaId: 5,
      fn: () => {
        expect(screen.getByRole("textbox")).toBeInTheDocument();
        expect(screen.getByRole("combobox")).toBeInTheDocument();
      },
    },
    {
      name: "group",
      type: EntryAttributeTypeTypeEnum.GROUP,
      schemaId: 6,
      fn: () => {
        expect(screen.getByRole("combobox")).toBeInTheDocument();
      },
    },
    {
      name: "role",
      type: EntryAttributeTypeTypeEnum.ROLE,
      schemaId: 7,
      fn: () => {
        expect(screen.getByRole("combobox")).toBeInTheDocument();
      },
    },

    // TODO array types
  ];

  cases.forEach((c) => {
    test(`should show ${c.name} typed value form field`, async () => {
      const {
        result: {
          current: { control, setValue },
        },
      } = renderHook(() =>
        useForm<Schema>({
          resolver: zodResolver(schema),
          mode: "onBlur",
          defaultValues,
        })
      );

      await act(async () => {
        render(
          <AttributeValueField
            control={control}
            setValue={setValue}
            type={c.type}
            schemaId={c.schemaId}
          />,
          { wrapper: TestWrapper }
        );
      });

      c.fn();
    });
  });
});
