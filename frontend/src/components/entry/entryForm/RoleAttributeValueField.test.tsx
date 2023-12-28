/**
 * @jest-environment jsdom
 */

import {
  EntryAttributeTypeTypeEnum,
  Role,
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
import { RoleAttributeValueField } from "./RoleAttributeValueField";

import { TestWrapper } from "TestWrapper";

import "@testing-library/jest-dom";

describe("RoleAttributeValueField", () => {
  const defaultValues: Schema = {
    name: "entry",
    schema: {
      id: 1,
      name: "entity",
    },
    attrs: {
      "0": {
        type: EntryAttributeTypeTypeEnum.ROLE,
        index: 0,
        isMandatory: false,
        schema: {
          id: 1,
          name: "role",
        },
        value: {
          asRole: { id: 1, name: "role1" },
        },
      },
      "1": {
        type: EntryAttributeTypeTypeEnum.ARRAY_ROLE,
        index: 1,
        isMandatory: false,
        schema: {
          id: 2,
          name: "array-role",
        },
        value: {
          asArrayRole: [
            {
              id: 1,
              name: "role1",
            },
          ],
        },
      },
    },
  };

  const roles: Role[] = [
    {
      id: 1,
      name: "role1",
      description: "role1",
      users: [],
      groups: [],
      adminUsers: [],
      adminGroups: [],
      isEditable: true,
    },
    {
      id: 2,
      name: "role2",
      description: "role2",
      users: [],
      groups: [],
      adminUsers: [],
      adminGroups: [],
      isEditable: true,
    },
  ];

  test("should provide role value editor", async () => {
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
        "getRoles"
      )
      .mockResolvedValue(Promise.resolve(roles));
    /* eslint-enable */

    await act(async () => {
      render(
        <RoleAttributeValueField
          attrId={0}
          control={control}
          setValue={setValue}
        />,
        { wrapper: TestWrapper }
      );
    });

    expect(screen.getByRole("combobox")).toHaveValue("role1");
    expect(getValues("attrs.0.value.asRole")).toEqual({ id: 1, name: "role1" });

    // Open the select options
    act(() => {
      screen.getByRole("button", { name: "Open" }).click();
    });
    // Select "role2" element
    act(() => {
      within(screen.getByRole("presentation")).getByText("role2").click();
    });

    expect(screen.getByRole("combobox")).toHaveValue("role2");
    expect(getValues("attrs.0.value.asRole")).toEqual({ id: 2, name: "role2" });
  });

  test("should provide array-role value editor", async () => {
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
        "getRoles"
      )
      .mockResolvedValue(Promise.resolve(roles));
    /* eslint-enable */

    await act(async () => {
      render(
        <RoleAttributeValueField
          attrId={1}
          control={control}
          setValue={setValue}
          multiple
        />,
        { wrapper: TestWrapper }
      );
    });

    expect(screen.getByRole("button", { name: "role1" })).toBeInTheDocument();
    expect(getValues("attrs.1.value.asArrayRole")).toEqual([
      { id: 1, name: "role1" },
    ]);

    // Open the select options
    act(() => {
      screen.getByRole("button", { name: "Open" }).click();
    });
    // Select "role2" element
    act(() => {
      within(screen.getByRole("presentation")).getByText("role2").click();
    });

    expect(screen.getByRole("button", { name: "role1" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "role2" })).toBeInTheDocument();

    expect(getValues("attrs.1.value.asArrayRole")).toEqual([
      { id: 1, name: "role1" },
      { id: 2, name: "role2" },
    ]);
  });
});
