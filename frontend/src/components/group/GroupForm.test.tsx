/**
 * @jest-environment jsdom
 */

import { Group } from "@dmm-com/airone-apiclient-typescript-fetch";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  act,
  fireEvent,
  render,
  renderHook,
  screen,
} from "@testing-library/react";
import { useForm } from "react-hook-form";

import { TestWrapper } from "../../TestWrapper";
import { schema } from "../entry/entryForm/EntryFormSchema";

import { GroupForm } from "./GroupForm";
import { Schema } from "./groupForm/GroupFormSchema";

describe("GroupForm", () => {
  const groups = [
    {
      id: 1,
      name: "group1",
      children: [
        {
          id: 1,
          name: "group1",
          children: [],
        },
        {
          id: 2,
          name: "group2",
          children: [],
        },
      ],
    },
    {
      id: 2,
      name: "group2",
      children: [],
    },
  ];

  const defaultValues: Group = {
    id: 1,
    name: "test",
    members: [],
  };

  test("should render a component with essential props", async () => {
    const {
      result: {
        current: { control, setValue },
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
      .spyOn(require("repository/AironeApiClient").aironeApiClient, "getUsers")
      .mockResolvedValue(Promise.resolve([]));
    jest
      .spyOn(
        require("repository/AironeApiClient").aironeApiClient,
        "getGroupTrees",
      )
      .mockResolvedValue(Promise.resolve(groups));
    /* eslint-enable */

    render(<GroupForm control={control} setValue={setValue} groupId={1} />, {
      wrapper: TestWrapper,
    });

    await act(async () => {
      fireEvent.change(screen.getByPlaceholderText("グループ名"), {
        target: { value: "group name" },
      });
    });

    expect(screen.getByPlaceholderText("グループ名")).toHaveValue("group name");
  });
});
