/**
 * @jest-environment jsdom
 */

import {
  EntryAttributeTypeTypeEnum,
  GetEntryAttrReferral,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  act,
  screen,
  render,
  renderHook,
  within,
  fireEvent,
} from "@testing-library/react";
import React from "react";
import { useForm } from "react-hook-form";

import { schema, Schema } from "./EntryFormSchema";
import {
  ArrayNamedObjectAttributeValueField,
  NamedObjectAttributeValueField,
  ObjectAttributeValueField,
} from "./ObjectAttributeValueField";

import { TestWrapper } from "TestWrapper";

import "@testing-library/jest-dom";

describe("ObjectAttributeValueField", () => {
  const defaultValues: Schema = {
    name: "entry",
    schema: {
      id: 1,
      name: "entity",
    },
    attrs: {
      "0": {
        type: EntryAttributeTypeTypeEnum.OBJECT,
        index: 0,
        isMandatory: false,
        schema: {
          id: 1,
          name: "object",
        },
        value: {
          asObject: { id: 1, name: "entry1" },
        },
      },
      "1": {
        type: EntryAttributeTypeTypeEnum.ARRAY_OBJECT,
        index: 1,
        isMandatory: false,
        schema: {
          id: 2,
          name: "array-object",
        },
        value: {
          asArrayObject: [
            {
              id: 1,
              name: "entry1",
            },
          ],
        },
      },
      "2": {
        type: EntryAttributeTypeTypeEnum.NAMED_OBJECT,
        index: 2,
        isMandatory: false,
        schema: {
          id: 3,
          name: "named-object",
        },
        value: {
          asNamedObject: {
            name: "initial name",
            object: {
              id: 1,
              name: "entry1",
            },
          },
        },
      },
      "3": {
        type: EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT,
        index: 3,
        isMandatory: false,
        schema: {
          id: 4,
          name: "array-named-object",
        },
        value: {
          asArrayNamedObject: [],
        },
      },
    },
  };

  const entries: GetEntryAttrReferral[] = [
    {
      id: 1,
      name: "entry1",
    },
    {
      id: 2,
      name: "entry2",
    },
  ];

  test("should provide object value editor", async () => {
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
        require("../../../repository/AironeApiClientV2").aironeApiClientV2,
        "getEntryAttrReferrals",
      )
      .mockResolvedValue(Promise.resolve(entries));
    /* eslint-enable */

    await act(async () => {
      render(
        <ObjectAttributeValueField
          attrId={0}
          control={control}
          setValue={setValue}
        />,
        { wrapper: TestWrapper },
      );
    });

    expect(screen.getByRole("combobox")).toHaveValue("entry1");
    expect(getValues("attrs.0.value.asObject")).toEqual({
      id: 1,
      name: "entry1",
    });

    // Open the select options
    act(() => {
      screen.getByRole("button", { name: "Open" }).click();
    });
    // Select "role2" element
    act(() => {
      within(screen.getByRole("presentation")).getByText("entry2").click();
    });

    expect(screen.getByRole("combobox")).toHaveValue("entry2");
    expect(getValues("attrs.0.value.asObject")).toEqual({
      id: 2,
      name: "entry2",
      _boolean: false,
    });
  });

  // TODO test array-object
  // TODO current how to handle RHF state can be wrong, AutoComplete with multiple=true doesn't work with the empty initial value
  test("should provide array-object value editor", async () => {
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
        require("../../../repository/AironeApiClientV2").aironeApiClientV2,
        "getEntryAttrReferrals",
      )
      .mockResolvedValue(Promise.resolve(entries));
    /* eslint-enable */

    await act(async () => {
      render(
        <ObjectAttributeValueField
          attrId={1}
          control={control}
          setValue={setValue}
          multiple
        />,
        { wrapper: TestWrapper },
      );
    });

    expect(screen.getByRole("button", { name: "entry1" })).toBeInTheDocument();
    expect(getValues("attrs.1.value.asArrayObject")).toEqual([
      {
        id: 1,
        name: "entry1",
      },
    ]);

    // Open the select options
    act(() => {
      screen.getByRole("button", { name: "Open" }).click();
    });
    // Select "role2" element
    act(() => {
      within(screen.getByRole("presentation")).getByText("entry2").click();
    });

    expect(screen.getByRole("button", { name: "entry1" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "entry2" })).toBeInTheDocument();
    expect(getValues("attrs.1.value.asArrayObject")).toEqual([
      {
        id: 1,
        name: "entry1",
        _boolean: false,
      },
      {
        id: 2,
        name: "entry2",
        _boolean: false,
      },
    ]);
  });

  test("should provide named-object value editor", async () => {
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
        require("../../../repository/AironeApiClientV2").aironeApiClientV2,
        "getEntryAttrReferrals",
      )
      .mockResolvedValue(Promise.resolve(entries));
    /* eslint-enable */

    await act(async () => {
      render(
        <NamedObjectAttributeValueField
          attrId={2}
          control={control}
          setValue={setValue}
        />,
        { wrapper: TestWrapper },
      );
    });

    expect(screen.getByRole("textbox")).toHaveValue("initial name");
    expect(screen.getByRole("combobox")).toHaveValue("entry1");
    expect(getValues("attrs.2.value.asNamedObject")).toEqual({
      name: "initial name",
      object: { id: 1, name: "entry1" },
    });

    // Edit name
    act(() => {
      fireEvent.change(screen.getByRole("textbox"), {
        target: { value: "new name" },
      });
    });
    // Open the select options
    act(() => {
      screen.getByRole("button", { name: "Open" }).click();
    });
    // Select "role1" element
    act(() => {
      within(screen.getByRole("presentation")).getByText("entry2").click();
    });

    expect(screen.getByRole("textbox")).toHaveValue("new name");
    expect(screen.getByRole("combobox")).toHaveValue("entry2");
    expect(getValues("attrs.2.value.asNamedObject")).toEqual({
      name: "new name",
      object: { id: 2, name: "entry2", _boolean: false },
    });
  });

  test("should provide array-named-object value editor", async () => {
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
        require("../../../repository/AironeApiClientV2").aironeApiClientV2,
        "getEntryAttrReferrals",
      )
      .mockResolvedValue(Promise.resolve(entries));
    /* eslint-enable */

    await act(async () => {
      render(
        <ArrayNamedObjectAttributeValueField
          attrId={3}
          control={control}
          setValue={setValue}
        />,
        { wrapper: TestWrapper },
      );
    });

    // At least 1 element appears even if the initial value is empty
    expect(screen.getAllByRole("textbox")).toHaveLength(1);
    expect(screen.getAllByRole("textbox")[0]).toHaveValue("");
    expect(screen.getAllByRole("combobox")[0]).toHaveValue("");

    // Edit the first element
    act(() => {
      fireEvent.change(screen.getAllByRole("textbox")[0], {
        target: { value: "new name" },
      });
    });
    act(() => {
      screen.getAllByRole("button", { name: "Open" })[0].click();
    });
    act(() => {
      within(screen.getAllByRole("presentation")[0])
        .getByText("entry1")
        .click();
    });
    expect(screen.getAllByRole("textbox")[0]).toHaveValue("new name");
    expect(screen.getAllByRole("combobox")[0]).toHaveValue("entry1");
    expect(getValues("attrs.3.value.asArrayNamedObject")).toEqual([
      {
        name: "new name",
        object: { id: 1, name: "entry1", _boolean: false },
        _boolean: false,
      },
    ]);

    // add second element
    act(() => {
      // now there is 1 element, and each element has 4 buttons (open-options, delete, add)
      // click the add button of the first element
      screen.getAllByRole("button")[2].click();
    });
    expect(screen.getAllByRole("textbox")).toHaveLength(2);
    expect(screen.getAllByRole("textbox")[0]).toHaveValue("new name");
    expect(screen.getAllByRole("combobox")[0]).toHaveValue("entry1");
    expect(screen.getAllByRole("textbox")[1]).toHaveValue("");
    expect(screen.getAllByRole("combobox")[1]).toHaveValue("");
    expect(getValues("attrs.3.value.asArrayNamedObject")).toEqual([
      {
        name: "new name",
        object: { id: 1, name: "entry1", _boolean: false },
        _boolean: false,
      },
      {
        name: "",
        object: null,
        _boolean: false,
      },
    ]);

    // delete first element
    act(() => {
      // now there is 1 element, and each element has 4 buttons (open-options, delete, add)
      // click the add button of the first element
      screen.getAllByRole("button")[1].click();
    });
    expect(screen.getAllByRole("textbox")).toHaveLength(1);
    expect(screen.getAllByRole("textbox")[0]).toHaveValue("");
    expect(screen.getAllByRole("combobox")[0]).toHaveValue("");
    expect(getValues("attrs.3.value.asArrayNamedObject")).toEqual([
      {
        name: "",
        object: null,
        _boolean: false,
      },
    ]);
  });
});
