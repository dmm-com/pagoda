/**
 * @jest-environment jsdom
 */

import { Entity } from "@dmm-com/airone-apiclient-typescript-fetch";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { FC } from "react";
import { useForm } from "react-hook-form";

import {
  AttributeTypes,
  BaseAttributeTypes,
} from "../../../services/Constants";

import { Schema } from "./EntityFormSchema";
import { IsolationRulesFields } from "./IsolationRulesFields";

import { TestWrapper } from "TestWrapper";

jest.mock("components/entry/entryForm/ReferralsAutocomplete", () => ({
  ReferralsAutocomplete: jest.fn(() => (
    <div data-testid="referrals-autocomplete" />
  )),
}));

const attrs: Schema["attrs"] = [
  {
    id: 1,
    name: "String attribute",
    type: BaseAttributeTypes.string,
    isMandatory: false,
    isDeleteInChain: false,
    isSummarized: false,
    isWritable: true,
    referral: [],
    note: "",
    nameOrder: "0",
    namePrefix: "",
    namePostfix: "",
    displayAttr: "",
  },
  {
    id: 2,
    name: "Boolean attribute",
    type: BaseAttributeTypes.bool,
    isMandatory: false,
    isDeleteInChain: false,
    isSummarized: false,
    isWritable: true,
    referral: [],
    note: "",
    nameOrder: "0",
    namePrefix: "",
    namePostfix: "",
    displayAttr: "",
  },
  {
    id: 3,
    name: "Object attribute",
    type: BaseAttributeTypes.object,
    isMandatory: false,
    isDeleteInChain: false,
    isSummarized: false,
    isWritable: true,
    referral: [{ id: 10, name: "Referral" }],
    note: "",
    nameOrder: "0",
    namePrefix: "",
    namePostfix: "",
    displayAttr: "",
  },
  {
    id: 4,
    name: "Named object attribute",
    type: BaseAttributeTypes.object | BaseAttributeTypes.named,
    isMandatory: false,
    isDeleteInChain: false,
    isSummarized: false,
    isWritable: true,
    referral: [{ id: 10, name: "Referral" }],
    note: "",
    nameOrder: "0",
    namePrefix: "",
    namePostfix: "",
    displayAttr: "",
  },
  {
    id: 5,
    name: "Unsupported number attribute",
    type: AttributeTypes.number.type,
    isMandatory: false,
    isDeleteInChain: false,
    isSummarized: false,
    isWritable: true,
    referral: [],
    note: "",
    nameOrder: "0",
    namePrefix: "",
    namePostfix: "",
    displayAttr: "",
  },
];

const createValues = (withRule = true): Schema => ({
  name: "Entity",
  note: "",
  itemNamePattern: "",
  itemNameType: "US",
  isToplevel: false,
  deleteChainExcludeEntities: [],
  attrs,
  webhooks: [],
  isolationRules: withRule
    ? [
        {
          conditions: [
            {
              attr: { id: 1, name: "String attribute", type: 0 },
              strCond: "initial",
              refCond: null,
              boolCond: false,
              isUnmatch: false,
            },
          ],
          action: { isPreventAll: false, preventFrom: null },
        },
      ]
    : [],
});

const referralEntities = [{ id: 10, name: "Referral" }] as Entity[];

const Harness: FC<{
  withRule?: boolean;
  values?: Schema;
  onForm?: (form: ReturnType<typeof useForm<Schema>>) => void;
}> = ({ withRule = true, values, onForm }) => {
  const form = useForm<Schema>({
    defaultValues: values ?? createValues(withRule),
  });
  onForm?.(form);
  return (
    <>
      <IsolationRulesFields
        control={form.control}
        referralEntities={referralEntities}
      />
      <output data-testid="rules">
        {JSON.stringify(form.watch("isolationRules"))}
      </output>
    </>
  );
};

const attributeSelect = (): HTMLElement => screen.getAllByRole("combobox")[1];

const selectAttribute = (name: string) => {
  fireEvent.mouseDown(attributeSelect());
  fireEvent.click(screen.getByRole("option", { name }));
};

describe("IsolationRulesFields", () => {
  test("adds the first rule and then its first condition", () => {
    render(<Harness withRule={false} />, { wrapper: TestWrapper });

    fireEvent.click(screen.getByTestId("AddIcon"));
    expect(screen.getAllByTestId("AddIcon")).toHaveLength(2);
    expect(screen.getByTestId("rules")).toHaveTextContent('"conditions":[]');

    fireEvent.click(screen.getAllByTestId("AddIcon")[0]);
    expect(screen.getByPlaceholderText("値")).toBeDisabled();
    expect(screen.getByTestId("rules")).toHaveTextContent('"isUnmatch":false');
  });

  test("filters unsupported attributes and renders boolean values", () => {
    const values = createValues();
    values.isolationRules[0].conditions[0].attr.id = 2;
    values.isolationRules[0].conditions[0].boolCond = true;
    let form: ReturnType<typeof useForm<Schema>> | undefined;
    render(<Harness values={values} onForm={(value) => (form = value)} />, {
      wrapper: TestWrapper,
    });

    expect(screen.getAllByRole("checkbox").at(-1)).toBeChecked();
    fireEvent.mouseDown(attributeSelect());
    const listbox = screen.getByRole("listbox");
    expect(
      within(listbox).queryByText("Unsupported number attribute"),
    ).not.toBeInTheDocument();
    fireEvent.click(within(listbox).getByText("String attribute"));
    const valueInput = screen.getByRole("textbox");
    fireEvent.change(valueInput, { target: { value: "updated" } });
    expect(form?.getValues("isolationRules.0.conditions.0.strCond")).toBe(
      "updated",
    );
  });

  test("renders referral inputs for object and named-object conditions", () => {
    render(<Harness />, { wrapper: TestWrapper });

    selectAttribute("Object attribute");
    expect(screen.getByTestId("referrals-autocomplete")).toBeInTheDocument();

    selectAttribute("Named object attribute");
    expect(screen.getByPlaceholderText("名前")).toBeInTheDocument();
    expect(screen.getByTestId("referrals-autocomplete")).toBeInTheDocument();
  });

  test("applies prevent-all and NOT states and removes rows", () => {
    const values = createValues();
    values.isolationRules[0].conditions[0].isUnmatch = true;
    values.isolationRules[0].action.isPreventAll = true;
    let form: ReturnType<typeof useForm<Schema>> | undefined;
    render(<Harness values={values} onForm={(value) => (form = value)} />, {
      wrapper: TestWrapper,
    });

    expect(screen.getAllByRole("checkbox")[0]).toBeChecked();
    expect(screen.getAllByRole("checkbox")[1]).toBeChecked();
    expect(screen.getAllByRole("combobox")[0]).toBeDisabled();

    fireEvent.click(screen.getAllByTestId("DeleteOutlineIcon")[0]);
    expect(screen.getByTestId("rules")).toHaveTextContent('"conditions":[]');
    fireEvent.click(screen.getByTestId("DeleteOutlineIcon"));
    expect(form?.getValues("isolationRules")).toEqual([]);
  });
});
