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
      "0": {
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
      "1": {
        type: EntryAttributeTypeTypeEnum.ARRAY_GROUP,
        index: 1,
        isMandatory: false,
        schema: {
          id: 2,
          name: "array-group",
        },
        value: {
          asArrayGroup: [
            {
              id: 1,
              name: "group1",
            },
          ],
        },
      },
    },
  };

  const groups: PaginatedGroupList = {
    count: 0,
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
      }),
    );

    /* eslint-disable */
    jest
      .spyOn(
        require("../../../repository/AironeApiClient").aironeApiClient,
        "getGroups",
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
        { wrapper: TestWrapper },
      );
    });

    expect(screen.getByRole("combobox")).toHaveValue("group1");
    expect(getValues("attrs.0.value.asGroup")).toEqual({
      id: 1,
      name: "group1",
    });

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
      }),
    );

    /* eslint-disable */
    jest
      .spyOn(
        require("../../../repository/AironeApiClient").aironeApiClient,
        "getGroups",
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
        { wrapper: TestWrapper },
      );
    });

    expect(screen.getByRole("button", { name: "group1" })).toBeInTheDocument();
    expect(getValues("attrs.1.value.asArrayGroup")).toEqual([
      { id: 1, name: "group1" },
    ]);

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
