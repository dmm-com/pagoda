/**
 */

import {
  EntryAttributeType,
  EntryAttributeTypeTypeEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { act, render, screen, within } from "@testing-library/react";

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

  test("should show note icon only for attributes with a note", async () => {
    await act(async () => {
      render(
        <EntryAttributes
          attributes={attributes}
          attrNotes={{ 1: "description of string1" }}
        />,
        {
          wrapper: TestWrapper,
        },
      );
    });

    expect(screen.getByLabelText("string1の説明")).toBeInTheDocument();
    expect(screen.queryByLabelText("string2の説明")).not.toBeInTheDocument();
  });

  test("should not show note icons when attrNotes is not given", async () => {
    await act(async () => {
      render(<EntryAttributes attributes={attributes} />, {
        wrapper: TestWrapper,
      });
    });

    expect(screen.queryByLabelText("string1の説明")).not.toBeInTheDocument();
  });
});
