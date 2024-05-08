/**
 * @jest-environment jsdom
 */

import {
  EntityAttr,
  EntryAttributeTypeTypeEnum,
  PaginatedEntityListList,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { setupServer } from "msw/node";
import React from "react";
import { BrowserRouter as Router } from "react-router-dom";

import { AdvancedSearchPage } from "./AdvancedSearchPage";
import { debug } from "webpack";

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

const entityAttrs: Array<string> = [
  "str",
  "obj",
];

const server = setupServer(
  http.get("http://localhost/entity/api/v2/", () => {
    console.log("http://localhost/entity/api/v2/");
    return HttpResponse.json(entities);
  }),

  http.get("http://localhost/entity/api/v2/attrs", () => {
    console.log("http://localhost/entity/api/v2/attrs");
    return HttpResponse.json(entityAttrs);
  })
);

beforeAll(() => server.listen());

afterEach(() => server.resetHandlers());

beforeEach(async () => {
  await act(async () => {
    render(
      <Router>
        <AdvancedSearchPage />
      </Router>
    );
  });
});

afterAll(() => server.close());

describe("AdvancedSearchPage", () => {
  test("no entity is shown by specifying wrong hint", async () => {
    const elemInputEntity = screen.getByPlaceholderText("エンティティを選択");

    // set wrong hint that there is no entity that have "hoge"
    fireEvent.change(elemInputEntity, { target: { value: "hoge" } });
    expect(screen.getByText("No options")).toBeInTheDocument();

    const options = screen.queryAllByRole("option");
    expect(options).toHaveLength(0);
  });

  test("part of entities are shown by specifying hint", async () => {
    const elemInputEntity = screen.getByPlaceholderText("エンティティを選択");

    // write down text to the input field
    fireEvent.change(elemInputEntity, { target: { value: "2" } });
    expect(elemInputEntity).toHaveValue("2");

    // check expected values that are retrieved from API will be displaied.
    const options = screen.getAllByRole("option");
    expect(options).toHaveLength(1);
    expect(options[0]).toHaveTextContent("entity2");
  });

  test("all entities are shown", async () => {
    const elemInputEntity = screen.getByPlaceholderText("エンティティを選択");

    if (elemInputEntity.parentNode) {
      fireEvent.click(elemInputEntity.parentNode);
    } else {
      throw new Error("Parent node not found");
    }

    const options = screen.getAllByRole("option");
    expect(options).toHaveLength(2);
    expect(options[0]).toHaveTextContent("entity1");
    expect(options[1]).toHaveTextContent("entity2");
  });

  test("show all attributes that are related to the entity", async () => {
    const elemInputEntity = screen.getByPlaceholderText("エンティティを選択");

    // write down text to the input field
    fireEvent.change(elemInputEntity, { target: { value: "2" } });
    expect(elemInputEntity).toHaveValue("2");

    // make an event to click selected option
    const optionsEntity = screen.getAllByRole("option");
    fireEvent.click(optionsEntity[0]);

    // Question:
    // After sending request to get attributes from server,
    // you have to implement processing for waiting Promise (until .loading == false).
    //
    // Answer:
    // You should use findBy() method that wait until loading == false.
    const elemInputEntityAttr = await screen.findByPlaceholderText("属性を選択");

    // This is a thip to close options of Entities that are shown above.
    // make an event to press Escape key using fireEvent
    // fireEvent.click(document.body);   // this doesn't work :(
    fireEvent.keyDown(elemInputEntity, { key: "Escape" });

    if (elemInputEntityAttr.parentNode) {
      fireEvent.click(elemInputEntityAttr.parentNode);
    } else {
      throw new Error("Parent node not found");
    }

    const options = screen.getAllByRole("option");

    expect(options).toHaveLength(3);
    expect(options[0]).toHaveTextContent("すべて選択");
    expect(options[1]).toHaveTextContent("str");
    expect(options[2]).toHaveTextContent("obj");
  });

  test("show part of attributes by specifying hint attrs", async () => {
    // TBD
  });

  test("show no attribute by specifying wrong hint", async () => {
    // TBD
  });
});
