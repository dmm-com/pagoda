/**
 * @jest-environment jsdom
 */

import { PaginatedEntityListList } from "@dmm-com/airone-apiclient-typescript-fetch";
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { setupServer } from "msw/node";
import React from "react";
import { BrowserRouter as Router } from "react-router";

import { AdvancedSearchPage } from "./AdvancedSearchPage";

const entities: PaginatedEntityListList = {
  count: 2,
  next: null,
  previous: null,
  results: [
    {
      id: 1,
      name: "entity1",
      isToplevel: false,
    },
    {
      id: 2,
      name: "entity2",
      isToplevel: false,
    },
  ],
};

const entityAttrs: Array<string> = ["str", "obj"];

const server = setupServer(
  http.get("http://localhost/entity/api/v2/", () => {
    return HttpResponse.json(entities);
  }),

  http.get("http://localhost/entity/api/v2/attrs", () => {
    return HttpResponse.json(entityAttrs);
  }),
);

beforeAll(() => server.listen());

afterEach(() => server.resetHandlers());

beforeEach(async () => {
  await act(async () => {
    render(
      <Router>
        <AdvancedSearchPage />
      </Router>,
    );
  });
});

afterAll(() => server.close());

describe("AdvancedSearchPage", () => {
  test("no entity is shown by specifying wrong hint", async () => {
    const elemInputEntity = screen.getByPlaceholderText("モデルを選択");

    // set wrong hint that there is no entity that have "hoge"
    fireEvent.change(elemInputEntity, { target: { value: "hoge" } });
    expect(screen.getByText("No options")).toBeInTheDocument();

    const options = screen.queryAllByRole("option");
    expect(options).toHaveLength(0);
  });

  test("part of entities are shown by specifying hint", async () => {
    const elemInputEntity = screen.getByPlaceholderText("モデルを選択");

    // write down text to the input field
    fireEvent.change(elemInputEntity, { target: { value: "2" } });
    expect(elemInputEntity).toHaveValue("2");

    // check expected values that are retrieved from API will be displaied.
    const options = screen.getAllByRole("option");
    expect(options).toHaveLength(1);
    expect(options[0]).toHaveTextContent("entity2");
  });

  test("all entities are shown", async () => {
    await act(async () => {
      fireEvent.click(screen.getAllByRole("button", { name: "Open" })[0]);
    });

    const options = screen.getAllByRole("option");
    expect(options).toHaveLength(2);
    expect(options[0]).toHaveTextContent("entity1");
    expect(options[1]).toHaveTextContent("entity2");
  });

  test("show all attributes that are related to the entity", async () => {
    const elemInputEntity = screen.getByPlaceholderText("モデルを選択");

    // write down text to the input field
    fireEvent.change(elemInputEntity, { target: { value: "2" } });
    expect(elemInputEntity).toHaveValue("2");

    // make an event to click selected option
    const optionsEntity = screen.getAllByRole("option");
    fireEvent.click(optionsEntity[0]);

    if (elemInputEntity.parentNode instanceof HTMLElement) {
      const selectedEntity = within(elemInputEntity.parentNode).getAllByRole(
        "button",
      );
      // right 1 is ArrowDropDownIcon.
      expect(selectedEntity).toHaveLength(1 + 1);
      expect(selectedEntity[0]).toHaveTextContent("entity2");
    } else {
      throw new Error("Parent node not found");
    }

    await act(async () => {
      fireEvent.keyDown(elemInputEntity, { key: "Escape" });
    });

    await act(async () => {
      fireEvent.click(screen.getAllByRole("button", { name: "Open" })[1]);
    });

    const options = screen.getAllByRole("option");

    expect(options).toHaveLength(3);
    expect(options[0]).toHaveTextContent("すべて選択");
    expect(options[1]).toHaveTextContent("str");
    expect(options[2]).toHaveTextContent("obj");

    fireEvent.click(options[1]);

    const elemInputEntityAttr =
      await screen.findByPlaceholderText("属性を選択");

    if (elemInputEntityAttr.parentNode instanceof HTMLElement) {
      const selectedEntity = within(
        elemInputEntityAttr.parentNode,
      ).getAllByRole("button");
      // right 1 is ArrowDropDownIcon.
      expect(selectedEntity).toHaveLength(1 + 1);
      expect(selectedEntity[0]).toHaveTextContent("str");
    } else {
      throw new Error("Parent node not found");
    }
  });

  test("select 'Select All' in entity attr element", async () => {
    const elemInputEntity = screen.getByPlaceholderText("モデルを選択");
    await act(async () => {
      fireEvent.change(elemInputEntity, { target: { value: "2" } });
    });

    const optionsEntity = screen.getAllByRole("option");
    await act(async () => {
      fireEvent.click(optionsEntity[0]);
      fireEvent.keyDown(elemInputEntity, { key: "Escape" });
    });

    await act(async () => {
      fireEvent.click(screen.getAllByRole("button", { name: "Open" })[1]);
    });

    const options = screen.getAllByRole("option");

    expect(options).toHaveLength(3);
    expect(options[0]).toHaveTextContent("すべて選択");
    expect(options[1]).toHaveTextContent("str");
    expect(options[2]).toHaveTextContent("obj");

    await act(async () => {
      fireEvent.click(options[0]);
    });

    const elemInputEntityAttr =
      await screen.findByPlaceholderText("属性を選択");

    if (elemInputEntityAttr.parentNode instanceof HTMLElement) {
      const selectedEntity = within(
        elemInputEntityAttr.parentNode,
      ).getAllByRole("button");
      // right 1 is ArrowDropDownIcon.
      expect(selectedEntity).toHaveLength(2 + 1);
      expect(selectedEntity[0]).toHaveTextContent("str");
      expect(selectedEntity[1]).toHaveTextContent("obj");
    } else {
      throw new Error("Parent node not found");
    }
  });

  test("show part of attributes by specifying hint attrs", async () => {
    const elemInputEntity = screen.getByPlaceholderText("モデルを選択");
    fireEvent.change(elemInputEntity, { target: { value: "2" } });

    const optionsEntity = screen.getAllByRole("option");
    fireEvent.click(optionsEntity[0]);
    fireEvent.keyDown(elemInputEntity, { key: "Escape" });

    const elemInputEntityAttr =
      await screen.findByPlaceholderText("属性を選択");

    await act(async () => {
      fireEvent.change(elemInputEntityAttr, { target: { value: "str" } });
    });

    const options = screen.getAllByRole("option");

    expect(options).toHaveLength(2);
    expect(options[0]).toHaveTextContent("すべて選択");
    expect(options[1]).toHaveTextContent("str");
  });

  test("show no attribute by specifying wrong hint", async () => {
    const elemInputEntity = screen.getByPlaceholderText("モデルを選択");
    fireEvent.change(elemInputEntity, { target: { value: "2" } });

    const optionsEntity = screen.getAllByRole("option");
    fireEvent.click(optionsEntity[0]);
    fireEvent.keyDown(elemInputEntity, { key: "Escape" });

    const elemInputEntityAttr =
      await screen.findByPlaceholderText("属性を選択");

    await act(async () => {
      fireEvent.change(elemInputEntityAttr, { target: { value: "hoge" } });
    });

    const options = screen.getAllByRole("option");

    expect(options).toHaveLength(1);
    expect(options[0]).toHaveTextContent("すべて選択");
  });

  test("submit search button", async () => {
    const elemInputEntity = screen.getByPlaceholderText("モデルを選択");
    fireEvent.change(elemInputEntity, { target: { value: "2" } });

    const optionsEntity = screen.getAllByRole("option");
    await act(async () => {
      fireEvent.click(optionsEntity[0]);
      fireEvent.keyDown(elemInputEntity, { key: "Escape" });
    });

    const elemInputEntityAttr =
      await screen.findByPlaceholderText("属性を選択");

    await act(async () => {
      fireEvent.change(elemInputEntityAttr, { target: { value: "str" } });
    });

    const optionsEntityAttr = screen.getAllByRole("option");
    await act(async () => {
      fireEvent.click(optionsEntityAttr[0]);
      fireEvent.keyDown(elemInputEntityAttr, { key: "Escape" });
    });

    const elemSubmitButton = screen.getByText("検索");
    // check href attribute of the button
    // URL decode the href string
    const parameter = decodeURI(elemSubmitButton.getAttribute("href") ?? "");
    expect(parameter).toBe(
      "/ui/advanced_search_result" +
        "?entity=2" +
        "&is_all_entities=false" +
        "&has_referral=false" +
        '&attrinfo=[{"name"%3A"str"%2C"filterKey"%3A0%2C"keyword"%3A""}]',
    );
  });
});
