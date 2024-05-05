/**
 * @jest-environment jsdom
 */

import {
  EntityDetail,
  EntryAttributeTypeTypeEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { render, screen, within } from "@testing-library/react";
import React, { FC } from "react";
import { useForm } from "react-hook-form";

import { TestWrapper } from "../../TestWrapper";

import { ActionForm } from "./ActionForm";
import { Schema } from "./TriggerFormSchema";

describe("ActionForm", () => {
  const entity: EntityDetail = {
    id: 1,
    name: "entity1",
    isToplevel: false,
    attrs: [
      EntryAttributeTypeTypeEnum.STRING,
      EntryAttributeTypeTypeEnum.ARRAY_STRING,
      EntryAttributeTypeTypeEnum.BOOLEAN,
      EntryAttributeTypeTypeEnum.OBJECT,
      EntryAttributeTypeTypeEnum.ARRAY_OBJECT,
      EntryAttributeTypeTypeEnum.NAMED_OBJECT,
      EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT,
    ].map((type, index) => ({
      id: index + 1,
      name: `attr${index + 1}`,
      type,
      index,
      note: "",
      isWritable: true,
      isMandatory: false,
      isDeleteInChain: false,
      referral: [],
    })),
    webhooks: [],
    hasOngoingChanges: false,
  };

  const defaultValues: Schema = {
    id: 1,
    entity: {
      id: 1,
      name: "entity1",
      isPublic: true,
    },
    conditions: [],
    actions: [
      // string-like
      {
        id: 1,
        attr: {
          id: 1,
          name: "attr1",
          type: EntryAttributeTypeTypeEnum.STRING,
        },
        values: [
          {
            id: 1,
            strCond: "str cond",
            refCond: null,
          },
        ],
      },
      {
        id: 2,
        attr: {
          id: 2,
          name: "attr2",
          type: EntryAttributeTypeTypeEnum.ARRAY_STRING,
        },
        values: [
          {
            id: 1,
            strCond: "str cond 1",
            refCond: null,
          },
          {
            id: 2,
            strCond: "str cond 2",
            refCond: null,
          },
        ],
      },

      // boolean
      {
        id: 3,
        attr: {
          id: 3,
          name: "attr3",
          type: EntryAttributeTypeTypeEnum.BOOLEAN,
        },
        values: [
          {
            id: 1,
            strCond: null,
            refCond: null,
            boolCond: true,
          },
        ],
      },

      // object-like
      {
        id: 4,
        attr: {
          id: 4,
          name: "attr4",
          type: EntryAttributeTypeTypeEnum.OBJECT,
        },
        values: [
          {
            id: 1,
            strCond: null,
            refCond: {
              id: 101,
              name: "ref1",
              schema: {
                id: 101,
                name: "ref1",
              },
            },
          },
        ],
      },
      {
        id: 5,
        attr: {
          id: 5,
          name: "attr5",
          type: EntryAttributeTypeTypeEnum.ARRAY_OBJECT,
        },
        values: [
          {
            id: 1,
            strCond: null,
            refCond: {
              id: 101,
              name: "ref1",
              schema: {
                id: 101,
                name: "ref1",
              },
            },
          },
          {
            id: 2,
            strCond: null,
            refCond: {
              id: 102,
              name: "ref2",
              schema: {
                id: 102,
                name: "ref2",
              },
            },
          },
        ],
      },

      // named-object-like
      {
        id: 6,
        attr: {
          id: 6,
          name: "attr6",
          type: EntryAttributeTypeTypeEnum.NAMED_OBJECT,
        },
        values: [
          {
            id: 1,
            strCond: "name",
            refCond: {
              id: 101,
              name: "ref1",
              schema: {
                id: 101,
                name: "ref1",
              },
            },
          },
        ],
      },
      {
        id: 7,
        attr: {
          id: 7,
          name: "attr7",
          type: EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT,
        },
        values: [
          {
            id: 1,
            strCond: "name1",
            refCond: {
              id: 101,
              name: "ref1",
              schema: {
                id: 101,
                name: "ref1",
              },
            },
          },
          {
            id: 2,
            strCond: "name2",
            refCond: {
              id: 102,
              name: "ref2",
              schema: {
                id: 102,
                name: "ref2",
              },
            },
          },
        ],
      },
    ],
  };

  test("renders attribute based fields", () => {
    const resetActionValues = jest.fn();
    const Wrapper: FC = () => {
      const { control } = useForm<Schema>({
        defaultValues,
      });
      return (
        <ActionForm
          control={control}
          entity={entity}
          resetActionValues={resetActionValues}
        />
      );
    };

    render(<Wrapper />, {
      wrapper: TestWrapper,
    });

    expect(screen.queryAllByRole("row")).toHaveLength(7);

    // string
    const row0 = screen.queryAllByRole("row")[0];
    expect(within(row0).getByText("attr1")).toBeInTheDocument();
    expect(within(row0).getByDisplayValue("str cond")).toBeInTheDocument();

    // array-string
    const row1 = screen.queryAllByRole("row")[1];
    expect(within(row1).getByText("attr2")).toBeInTheDocument();
    expect(within(row1).getByDisplayValue("str cond 1")).toBeInTheDocument();
    expect(within(row1).getByDisplayValue("str cond 2")).toBeInTheDocument();

    // boolean
    const row2 = screen.queryAllByRole("row")[2];
    expect(within(row2).getByText("attr3")).toBeInTheDocument();
    expect(within(row2).getByRole("checkbox")).toBeChecked();

    // object
    const row3 = screen.queryAllByRole("row")[3];
    expect(within(row3).getByText("attr4")).toBeInTheDocument();
    expect(within(row3).getByDisplayValue("ref1")).toBeInTheDocument();

    // array-object
    const row4 = screen.queryAllByRole("row")[4];
    expect(within(row4).getByText("attr5")).toBeInTheDocument();
    expect(within(row4).getByDisplayValue("ref1")).toBeInTheDocument();
    expect(within(row4).getByDisplayValue("ref2")).toBeInTheDocument();

    // named-object
    const row5 = screen.queryAllByRole("row")[5];
    expect(within(row5).getByText("attr6")).toBeInTheDocument();
    expect(within(row5).getByDisplayValue("name")).toBeInTheDocument();
    expect(within(row5).getByDisplayValue("ref1")).toBeInTheDocument();

    // array-named-object
    const row6 = screen.queryAllByRole("row")[6];
    expect(within(row6).getByText("attr7")).toBeInTheDocument();
    expect(within(row6).getByDisplayValue("name1")).toBeInTheDocument();
    expect(within(row6).getByDisplayValue("ref1")).toBeInTheDocument();
    expect(within(row6).getByDisplayValue("name2")).toBeInTheDocument();
    expect(within(row6).getByDisplayValue("ref2")).toBeInTheDocument();
  });
});
