/**
 * @jest-environment jsdom
 */

import { EntryAttributeTypeTypeEnum } from "@dmm-com/airone-apiclient-typescript-fetch";
import { render, screen, within } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "../../TestWrapper";

import { AttributeValue } from "components/entry/AttributeValue";

describe("AttributeValue", () => {
  test("should show string typed value", async () => {
    const attrInfo = {
      type: EntryAttributeTypeTypeEnum.STRING,
      value: { asString: "hoge" },
    };
    render(<AttributeValue attrInfo={attrInfo} />, { wrapper: TestWrapper });

    expect(screen.getAllByRole("listitem")).toHaveLength(1);
    expect(
      within(screen.getByRole("listitem")).getByText("hoge")
    ).toBeVisible();
  });

  test("should show text typed value", async () => {
    const attrInfo = {
      type: EntryAttributeTypeTypeEnum.TEXT,
      value: { asString: "hoge" },
    };
    render(<AttributeValue attrInfo={attrInfo} />, { wrapper: TestWrapper });

    expect(screen.getAllByRole("listitem")).toHaveLength(1);
    expect(
      within(screen.getByRole("listitem")).getByText("hoge")
    ).toBeVisible();
  });

  test("should show date typed value", async () => {
    const attrInfo = {
      type: EntryAttributeTypeTypeEnum.DATE,
      value: { asString: "2020-01-01" },
    };
    render(<AttributeValue attrInfo={attrInfo} />, { wrapper: TestWrapper });

    expect(screen.getAllByRole("listitem")).toHaveLength(1);
    expect(
      within(screen.getByRole("listitem")).getByText("2020-01-01")
    ).toBeVisible();
  });

  test("should show boolean typed value", async () => {
    const attrInfo = {
      type: EntryAttributeTypeTypeEnum.BOOLEAN,
      value: { asBoolean: true },
    };
    render(<AttributeValue attrInfo={attrInfo} />, { wrapper: TestWrapper });

    expect(screen.getAllByRole("listitem")).toHaveLength(1);
    expect(
      within(screen.getByRole("listitem")).getByRole("checkbox")
    ).toBeChecked();
  });

  test("should show object typed value", async () => {
    const attrInfo = {
      type: EntryAttributeTypeTypeEnum.OBJECT,
      value: {
        asObject: {
          id: 100,
          name: "object1",
          schema: { id: 1, name: "referred" },
        },
      },
    };
    render(<AttributeValue attrInfo={attrInfo} />, { wrapper: TestWrapper });

    expect(screen.getAllByRole("listitem")).toHaveLength(1);
    expect(
      within(screen.getByRole("listitem")).getByRole("link")
    ).toHaveTextContent("object1");
  });

  test("should show named-object typed value", async () => {
    const attrInfo = {
      type: EntryAttributeTypeTypeEnum.NAMED_OBJECT,
      value: {
        asNamedObject: {
          name: "name1",
          object: {
            id: 100,
            name: "object1",
            schema: { id: 1, name: "referred" },
          },
        },
      },
    };
    render(<AttributeValue attrInfo={attrInfo} />, { wrapper: TestWrapper });

    expect(screen.getAllByRole("listitem")).toHaveLength(1);
    expect(
      within(screen.getByRole("listitem")).getByText("name1")
    ).toBeVisible();
    expect(
      within(screen.getByRole("listitem")).getByRole("link")
    ).toHaveTextContent("object1");
  });

  test("should show group typed value", async () => {
    const attrInfo = {
      type: EntryAttributeTypeTypeEnum.GROUP,
      value: {
        asGroup: { id: 100, name: "group1" },
      },
    };
    render(<AttributeValue attrInfo={attrInfo} />, { wrapper: TestWrapper });

    expect(screen.getAllByRole("listitem")).toHaveLength(1);
    expect(
      within(screen.getByRole("listitem")).getByRole("link")
    ).toHaveTextContent("group1");
  });

  test("should show role typed value", async () => {
    const attrInfo = {
      type: EntryAttributeTypeTypeEnum.ROLE,
      value: {
        asRole: { id: 100, name: "role1" },
      },
    };
    render(<AttributeValue attrInfo={attrInfo} />, { wrapper: TestWrapper });

    expect(screen.getAllByRole("listitem")).toHaveLength(1);
    expect(
      within(screen.getByRole("listitem")).getByRole("link")
    ).toHaveTextContent("role1");
  });

  test("should show array-string typed value", async () => {
    const attrInfo = {
      type: EntryAttributeTypeTypeEnum.ARRAY_STRING,
      value: { asArrayString: ["hoge", "fuga"] },
    };
    render(<AttributeValue attrInfo={attrInfo} />, { wrapper: TestWrapper });

    expect(screen.getAllByRole("listitem")).toHaveLength(2);
    expect(
      within(screen.getAllByRole("listitem")[0]).getByText("hoge")
    ).toBeVisible();
    expect(
      within(screen.getAllByRole("listitem")[1]).getByText("fuga")
    ).toBeVisible();
  });

  test("should show array-object typed value", async () => {
    const attrInfo = {
      type: EntryAttributeTypeTypeEnum.ARRAY_OBJECT,
      value: {
        asArrayObject: [
          { id: 100, name: "object1", schema: { id: 1, name: "referred" } },
          { id: 200, name: "object2", schema: { id: 1, name: "referred" } },
        ],
      },
    };
    render(<AttributeValue attrInfo={attrInfo} />, { wrapper: TestWrapper });

    expect(screen.getAllByRole("listitem")).toHaveLength(2);
    expect(
      within(screen.getAllByRole("listitem")[0]).getByRole("link")
    ).toHaveTextContent("object1");
    expect(
      within(screen.getAllByRole("listitem")[1]).getByRole("link")
    ).toHaveTextContent("object2");
  });

  test("should show array-named-object typed value", async () => {
    const attrInfo = {
      type: EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT,
      value: {
        asArrayNamedObject: [
          {
            name: "name1",
            object: {
              id: 100,
              name: "object1",
              schema: { id: 1, name: "referred" },
            },
            _boolean: false,
          },
          {
            name: "name2",
            object: {
              id: 200,
              name: "object2",
              schema: { id: 1, name: "referred" },
            },
            _boolean: false,
          },
        ],
      },
    };
    render(<AttributeValue attrInfo={attrInfo} />, { wrapper: TestWrapper });

    expect(screen.getAllByRole("listitem")).toHaveLength(2);
    expect(
      within(screen.getAllByRole("listitem")[0]).getByText("name1")
    ).toBeVisible();
    expect(
      within(screen.getAllByRole("listitem")[0]).getByRole("link")
    ).toHaveTextContent("object1");
    expect(
      within(screen.getAllByRole("listitem")[1]).getByText("name2")
    ).toBeVisible();
    expect(
      within(screen.getAllByRole("listitem")[1]).getByRole("link")
    ).toHaveTextContent("object2");
  });

  test("should show array-group typed value", async () => {
    const attrInfo = {
      type: EntryAttributeTypeTypeEnum.ARRAY_GROUP,
      value: {
        asArrayGroup: [
          { id: 100, name: "group1" },
          { id: 200, name: "group2" },
        ],
      },
    };
    render(<AttributeValue attrInfo={attrInfo} />, { wrapper: TestWrapper });

    expect(screen.getAllByRole("listitem")).toHaveLength(2);
    expect(
      within(screen.getAllByRole("listitem")[0]).getByRole("link")
    ).toHaveTextContent("group1");
    expect(
      within(screen.getAllByRole("listitem")[1]).getByRole("link")
    ).toHaveTextContent("group2");
  });

  test("should show array-role typed value", async () => {
    const attrInfo = {
      type: EntryAttributeTypeTypeEnum.ARRAY_ROLE,
      value: {
        asArrayRole: [
          { id: 100, name: "role1" },
          { id: 200, name: "role2" },
        ],
      },
    };
    render(<AttributeValue attrInfo={attrInfo} />, { wrapper: TestWrapper });

    expect(screen.getAllByRole("listitem")).toHaveLength(2);
    expect(
      within(screen.getAllByRole("listitem")[0]).getByRole("link")
    ).toHaveTextContent("role1");
    expect(
      within(screen.getAllByRole("listitem")[1]).getByRole("link")
    ).toHaveTextContent("role2");
  });
});
