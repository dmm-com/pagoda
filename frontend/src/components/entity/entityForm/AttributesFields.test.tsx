/**
 */

import { zodResolver } from "@hookform/resolvers/zod";
import {
  act,
  fireEvent,
  render,
  renderHook,
  screen,
} from "@testing-library/react";
import { useForm } from "react-hook-form";

import { schema } from "../../entry/entryForm/EntryFormSchema";

import { AttributesFields, getReorderIndices } from "./AttributesFields";
import { Schema } from "./EntityFormSchema";

import { TestWrapper } from "TestWrapper";
import { AttributeTypes } from "services/Constants";

describe("getReorderIndices", () => {
  const ids = ["a", "b", "c", "d"];

  test("returns source and destination indices for a valid move", () => {
    expect(getReorderIndices(ids, "a", "c")).toEqual({
      oldIndex: 0,
      newIndex: 2,
    });
    expect(getReorderIndices(ids, "d", "a")).toEqual({
      oldIndex: 3,
      newIndex: 0,
    });
  });

  test("returns null when dropped onto itself (no-op)", () => {
    expect(getReorderIndices(ids, "b", "b")).toBeNull();
  });

  test("returns null when an id is unknown", () => {
    expect(getReorderIndices(ids, "a", "z")).toBeNull();
    expect(getReorderIndices(ids, "z", "a")).toBeNull();
  });
});

describe("AttributesFields", () => {
  const defaultValues: Schema = {
    name: "hoge",
    note: "fuga",
    itemNamePattern: "",
    itemNameType: "US",
    isToplevel: false,
    webhooks: [],
    isolationRules: [],
    deleteChainExcludeEntities: [],
    attrs: [],
  };

  const renderFields = (values: Schema = defaultValues) => {
    const {
      result: {
        current: { control, getValues, setValue },
      },
    } = renderHook(() =>
      useForm<Schema>({
        resolver: zodResolver(schema),
        mode: "onBlur",
        defaultValues: values,
      }),
    );

    render(
      <AttributesFields
        control={control}
        setValue={setValue}
        referralEntities={[]}
      />,
      { wrapper: TestWrapper },
    );

    return { getValues };
  };

  test("provides drag-and-drop reordering instead of up/down arrows", async () => {
    const { getValues } = renderFields();

    expect(screen.queryAllByPlaceholderText("属性名")).toHaveLength(0);

    // add first attribute (only the empty-state add button exists initially)
    await act(async () => {
      screen.getByRole("button").click();
    });

    expect(screen.queryAllByPlaceholderText("属性名")).toHaveLength(1);

    // a drag handle is rendered for reordering
    expect(screen.getAllByTestId("attr-drag-handle")).toHaveLength(1);

    // the legacy up/down arrow controls are gone
    expect(screen.queryByTestId("ArrowUpwardIcon")).toBeNull();
    expect(screen.queryByTestId("ArrowDownwardIcon")).toBeNull();

    // edit first attribute
    await act(async () => {
      fireEvent.change(screen.getByPlaceholderText("属性名"), {
        target: { value: "attr1" },
      });
    });

    expect(screen.getByPlaceholderText("属性名")).toHaveValue("attr1");
    expect(getValues("attrs.0.name")).toEqual("attr1");

    // add a second attribute via the row's add button
    await act(async () => {
      fireEvent.click(screen.getAllByTestId("AddIcon")[0]);
    });

    expect(screen.getAllByTestId("attr-drag-handle")).toHaveLength(2);

    // delete the first attribute via its delete button
    await act(async () => {
      fireEvent.click(screen.getAllByTestId("DeleteOutlineIcon")[0]);
    });

    expect(screen.getAllByTestId("attr-drag-handle")).toHaveLength(1);
  });

  test("disables the drag handle for a non-writable attribute", () => {
    renderFields({
      ...defaultValues,
      attrs: [
        {
          name: "readonly-attr",
          type: AttributeTypes.string.type,
          isMandatory: false,
          isDeleteInChain: false,
          isSummarized: false,
          isWritable: false,
          referral: [],
          note: "",
          nameOrder: "0",
          namePrefix: "",
          namePostfix: "",
          displayAttr: "",
        },
      ],
    });

    const handle = screen.getByTestId("attr-drag-handle");
    expect(handle).toBeDisabled();
  });
});
