/**
 * @jest-environment jsdom
 */

import {
  EntryAttributeTypeTypeEnum,
  PaginatedGroupList,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  act,
  screen,
  render,
  renderHook,
  within,
} from "@testing-library/react";
import React from "react";
import { useForm } from "react-hook-form";

import { schema, Schema } from "./EntryFormSchema";
import { GroupAttributeValueField } from "./GroupAttributeValueField";

import { TestWrapper } from "TestWrapper";

import "@testing-library/jest-dom";

describe("GroupAttributeValueField", () => {
  const defaultValues: Schema = {
    name: "entry",
    schema: {
      id: 1,
      name: "entity",
    },
    attrs: {
      group: {
        type: EntryAttributeTypeTypeEnum.GROUP,
        index: 0,
        isMandatory: false,
        schema: {
          id: 1,
          name: "group",
        },
        value: {
          asGroup: { id: 1, name: "group1" },
        },
      },
      arrayGroup: {
        type: EntryAttributeTypeTypeEnum.ARRAY_GROUP,
        index: 1,
        isMandatory: false,
        schema: {
          id: 2,
          name: "array-group",
        },
        value: {
          asArrayGroup: [],
        },
      },
    },
  };

  const groups: PaginatedGroupList = {
    results: [
      {
        id: 1,
        name: "group1",
        members: [],
      },
      {
        id: 2,
        name: "group2",
        members: [],
      },
    ],
  };

  test("should provide group value editor", async () => {
    const {
      result: {
        current: { control, setValue, getValues },
      },
    } = renderHook(() =>
      useForm<Schema>({
        resolver: zodResolver(schema),
        mode: "onBlur",
        defaultValues,
      })
    );

    /* eslint-disable */
    jest
      .spyOn(
        require("../../../repository/AironeApiClientV2").aironeApiClientV2,
        "getGroups"
      )
      .mockResolvedValue(Promise.resolve(groups));
    /* eslint-enable */

    await act(async () => {
      render(
        <GroupAttributeValueField
          attrId={0}
          control={control}
          setValue={setValue}
        />,
        { wrapper: TestWrapper }
      );
    });

    // TODO check the initial value, then trigger the change event and check the new value

    // Open the select options
    act(() => {
      screen.getByRole("button", { name: "Open" }).click();
    });
    // Select "group2" element
    act(() => {
      within(screen.getByRole("presentation")).getByText("group2").click();
    });

    expect(screen.getByRole("combobox")).toHaveValue("group2");

    expect(getValues("attrs.0.value.asGroup")).toEqual({
      id: 2,
      name: "group2",
    });
  });

  test("should provide array-group value editor", async () => {
    const {
      result: {
        current: { control, setValue, getValues },
      },
    } = renderHook(() =>
      useForm<Schema>({
        resolver: zodResolver(schema),
        mode: "onBlur",
        defaultValues,
      })
    );

    /* eslint-disable */
    jest
      .spyOn(
        require("../../../repository/AironeApiClientV2").aironeApiClientV2,
        "getGroups"
      )
      .mockResolvedValue(Promise.resolve(groups));
    /* eslint-enable */

    await act(async () => {
      render(
        <GroupAttributeValueField
          attrId={1}
          control={control}
          setValue={setValue}
          multiple
        />,
        { wrapper: TestWrapper }
      );
    });

    // Open the select options
    act(() => {
      screen.getByRole("button", { name: "Open" }).click();
    });
    // Select "group1" element
    act(() => {
      within(screen.getByRole("presentation")).getByText("group1").click();
    });
    // Open the select options
    act(() => {
      screen.getByRole("button", { name: "Open" }).click();
    });
    // Select "group2" element
    act(() => {
      within(screen.getByRole("presentation")).getByText("group2").click();
    });

    expect(screen.getByRole("button", { name: "group1" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "group2" })).toBeInTheDocument();

    expect(getValues("attrs.1.value.asArrayGroup")).toEqual([
      { id: 1, name: "group1" },
      { id: 2, name: "group2" },
    ]);
  });
});
