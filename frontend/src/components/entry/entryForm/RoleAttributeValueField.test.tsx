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

import { TestWrapper } from "TestWrapper";

import "@testing-library/jest-dom";
import { RoleAttributeValueField } from "./RoleAttributeValueField";

describe("RoleAttributeValueField", () => {
  const defaultValues: Schema = {
    name: "entry",
    schema: {
      id: 1,
      name: "entity",
    },
    attrs: {
      role: {
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
        current: { control, setValue },
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

    // TODO check the initial value, then trigger the change event and check the new value

    // Open the select options
    act(() => {
      screen.getByRole("button", { name: "Open" }).click();
    });

    // Select "role2" element
    act(() => {
      within(screen.getByRole("presentation")).getByText("role2").click();
    });

    expect(screen.getByRole("combobox")).toHaveValue("role2");
  });
});
