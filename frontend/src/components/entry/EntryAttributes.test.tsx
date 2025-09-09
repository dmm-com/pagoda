/**
 * @jest-environment jsdom
 */

import { act, render, screen, within } from "@testing-library/react";

import {
  EntryAttributeType,
  EntryAttributeTypeTypeEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { TestWrapper } from "TestWrapper";
import { EntryAttributes } from "components/entry/EntryAttributes";

describe("EntryAttributes", () => {
  const attributes: Array<EntryAttributeType> = [
    // readable
    {
      id: 1,
      type: EntryAttributeTypeTypeEnum.STRING,
      isMandatory: false,
      isReadable: true,
      schema: {
        id: 1,
        name: "string1",
      },
      value: {
        asString: "value1",
      },
    },

    // non-readable
    {
      id: 2,
      type: EntryAttributeTypeTypeEnum.STRING,
      isMandatory: false,
      isReadable: false,
      schema: {
        id: 2,
        name: "string2",
      },
      value: {
        asString: "value2",
      },
    },
  ];

  test("should render readable attributes", async () => {
    await act(async () => {
      render(<EntryAttributes attributes={attributes} />, {
        wrapper: TestWrapper,
      });
    });

    // 0 is header, 1 is body
    const bodyRowGroup = screen.getAllByRole("rowgroup")[1];
    expect(within(bodyRowGroup).queryAllByRole("row")).toHaveLength(2);
    expect(within(bodyRowGroup).queryByText("value1")).toBeInTheDocument();
    expect(within(bodyRowGroup).queryByText("value2")).not.toBeInTheDocument();
  });
});
