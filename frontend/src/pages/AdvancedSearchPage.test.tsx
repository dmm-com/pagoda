/**
 * @jest-environment jsdom
 */

import {
  EntityAttr,
  EntryAttributeTypeTypeEnum,
  PaginatedEntityListList,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { act, render, screen, fireEvent } from "@testing-library/react";
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
    return HttpResponse.json(entities);
  }),

  http.get("http://localhost/entity/api/v2/attrs", () => {
    return HttpResponse.json(entityAttrs);
  })
);

beforeAll(() => server.listen());

afterEach(() => server.resetHandlers());

afterAll(() => server.close());

describe("AdvancedSearchPage", () => {
  test("should render the component", async () => {
    await act(async () => {
      render(
        <Router>
          <AdvancedSearchPage />
        </Router>
      );
    });

    const elemInputEntity = screen.getByPlaceholderText("エンティティを選択");

    elemInputEntity.click();

    //console.debug(screen.getAllByRole("option"));

    // NG pattern - that uses userEvent
    //userEvent.type(screen.getByRole("combobox"), "entity");

    // OK pattern1
    //fireEvent.change(screen.getByRole("combobox"), { target: { value: "entity" } });

    // write down text to the input field
    fireEvent.change(elemInputEntity, { target: { value: "entity" } });
    expect(elemInputEntity).toHaveValue("entity");

    // check expected values that are retrieved from API will be displaied.
    screen.debug();

    //expect(elemInputEntity).toHaveValue("entity");

    //console.debug(elemInputEntity);


    //const selectElement = screen.getByRole("combobox");

  });
});
