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

import { aironeApiClient } from "../../../repository/AironeApiClient";

import { schema, Schema } from "./EntryFormSchema";
import { RoleAttributeValueField } from "./RoleAttributeValueField";

import { TestWrapper } from "TestWrapper";

import "@testing-library/jest-dom";

// ✅ Mock the aironeApiClient module
jest.mock("../../../repository/AironeApiClient", () => ({
  aironeApiClient: {
    searchRoles: jest.fn(),
  },
}));

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
    // ✅ Set up mock return value for searchRoles
    (aironeApiClient.searchRoles as jest.Mock).mockResolvedValue(roles);

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

    // ✅ Render the field component
    await act(async () => {
      render(
        <RoleAttributeValueField
          attrId={0}
          control={control}
          setValue={setValue}
        />,
        { wrapper: TestWrapper },
      );
    });

    // ✅ Initial value should be "role1"
    expect(screen.getByRole("combobox")).toHaveValue("role1");
    expect(getValues("attrs.0.value.asRole")).toEqual({ id: 1, name: "role1" });

    // ✅ Open dropdown and select "role2"
    act(() => {
      screen.getByRole("button", { name: "Open" }).click();
    });
    act(() => {
      within(screen.getByRole("presentation")).getByText("role2").click();
    });

    // ✅ After selection, value should be updated to "role2"
    expect(screen.getByRole("combobox")).toHaveValue("role2");
    expect(getValues("attrs.0.value.asRole")).toEqual({ id: 2, name: "role2" });
  });

  test("should provide array-role value editor", async () => {
    // ✅ Set up mock return value for searchRoles
    (aironeApiClient.searchRoles as jest.Mock).mockResolvedValue(roles);

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

    // ✅ Render the field component in multiple (array) mode
    await act(async () => {
      render(
        <RoleAttributeValueField
          attrId={1}
          control={control}
          setValue={setValue}
          multiple
        />,
        { wrapper: TestWrapper },
      );
    });

    // ✅ Initial selected role should be "role1"
    expect(screen.getByRole("button", { name: "role1" })).toBeInTheDocument();
    expect(getValues("attrs.1.value.asArrayRole")).toEqual([
      { id: 1, name: "role1" },
    ]);

    // ✅ Open dropdown and select "role2"
    act(() => {
      screen.getByRole("button", { name: "Open" }).click();
    });
    act(() => {
      within(screen.getByRole("presentation")).getByText("role2").click();
    });

    // ✅ Both "role1" and "role2" should now be selected
    expect(screen.getByRole("button", { name: "role1" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "role2" })).toBeInTheDocument();

    expect(getValues("attrs.1.value.asArrayRole")).toEqual([
      { id: 1, name: "role1" },
      { id: 2, name: "role2" },
    ]);
  });
});
