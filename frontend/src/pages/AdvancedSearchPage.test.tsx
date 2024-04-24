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

const entityAttrs: Array<EntityAttr> = [
  {
    id: 3,
    name: "str",
    type: EntryAttributeTypeTypeEnum.STRING,
  },
  {
    id: 4,
    name: "obj",
    type: EntryAttributeTypeTypeEnum.OBJECT,
    //referral: [2],
  },
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

afterAll(() => server.close());

describe("AdvancedSearchPage", () => {
  test("selected entity test", async () => {
    await act(async () => {
      render(
        <Router>
          <AdvancedSearchPage />
        </Router>
      );
    });

    const elemInputEntity = screen.getByPlaceholderText("エンティティを選択");

    if (elemInputEntity.parentNode) {
      fireEvent.click(elemInputEntity.parentNode);
    } else {
      throw new Error("Parent node not found");
    }

    let options = screen.getAllByRole("option");
    expect(options).toHaveLength(2);
    expect(options[0]).toHaveTextContent("entity1");
    expect(options[1]).toHaveTextContent("entity2");

    // write down text to the input field
    fireEvent.change(elemInputEntity, { target: { value: "2" } });
    expect(elemInputEntity).toHaveValue("2");

    // check expected values that are retrieved from API will be displaied.
    options = screen.getAllByRole("option");
    expect(options).toHaveLength(1);
    expect(options[0]).toHaveTextContent("entity2");

    fireEvent.change(elemInputEntity, { target: { value: "hoge" } });
    expect(screen.getByText("No options")).toBeInTheDocument();

    options = screen.queryAllByRole("option");
    expect(options).toHaveLength(0);

    //screen.debug();

    const elemInputEntityAttr = screen.getByPlaceholderText("属性を選択");

    if (elemInputEntityAttr.parentNode) {
      fireEvent.click(elemInputEntityAttr.parentNode);
    } else {
      throw new Error("Parent node not found");
    }

    options = screen.getAllByRole("option");
    expect(options).toHaveLength(2);
    expect(options[0]).toHaveTextContent("str");
    expect(options[1]).toHaveTextContent("obj");
  });
});
