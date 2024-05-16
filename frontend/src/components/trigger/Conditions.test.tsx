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

import { Conditions } from "./Conditions";
import { Schema } from "./TriggerFormSchema";

describe("Conditions", () => {
  const entity: EntityDetail = {
    id: 1,
    name: "entity1",
    isToplevel: false,
    attrs: [
      EntryAttributeTypeTypeEnum.STRING,
      EntryAttributeTypeTypeEnum.BOOLEAN,
      EntryAttributeTypeTypeEnum.OBJECT,
      EntryAttributeTypeTypeEnum.NAMED_OBJECT,
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
    conditions: [
      {
        id: 1,
        attr: {
          id: 1,
          name: "attr1",
          type: EntryAttributeTypeTypeEnum.STRING,
        },
        strCond: "str cond",
        refCond: null,
      },
      {
        id: 2,
        attr: {
          id: 2,
          name: "attr2",
          type: EntryAttributeTypeTypeEnum.BOOLEAN,
        },
        boolCond: true,
        strCond: null,
        refCond: null,
      },
      {
        id: 3,
        attr: {
          id: 3,
          name: "attr3",
          type: EntryAttributeTypeTypeEnum.OBJECT,
        },
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
        id: 4,
        attr: {
          id: 4,
          name: "attr4",
          type: EntryAttributeTypeTypeEnum.NAMED_OBJECT,
        },
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
    actions: [],
  };

  test("renders attribute based fields", () => {
    const Wrapper: FC = () => {
      const { control } = useForm<Schema>({
        defaultValues,
      });
      return <Conditions control={control} entity={entity} />;
    };

    render(<Wrapper />, {
      wrapper: TestWrapper,
    });

    expect(screen.queryAllByRole("row")).toHaveLength(4);

    const row0 = screen.queryAllByRole("row")[0];
    expect(within(row0).getByText("attr1")).toBeInTheDocument();
    expect(within(row0).getByDisplayValue("str cond")).toBeInTheDocument();

    const row1 = screen.queryAllByRole("row")[1];
    expect(within(row1).getByText("attr2")).toBeInTheDocument();
    expect(within(row1).getByRole("checkbox")).toBeChecked();

    const row2 = screen.queryAllByRole("row")[2];
    expect(within(row2).getByText("attr3")).toBeInTheDocument();
    expect(within(row2).getByDisplayValue("ref1")).toBeInTheDocument();

    const row3 = screen.queryAllByRole("row")[3];
    expect(within(row3).getByText("attr4")).toBeInTheDocument();
    expect(within(row3).getByDisplayValue("name")).toBeInTheDocument();
    expect(within(row3).getByDisplayValue("ref1")).toBeInTheDocument();
  });
});
