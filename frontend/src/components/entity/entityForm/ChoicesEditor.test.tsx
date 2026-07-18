/**
 * @jest-environment jsdom
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { FC } from "react";
import { useForm } from "react-hook-form";

import { ChoicesEditor } from "./ChoicesEditor";
import { Schema } from "./EntityFormSchema";

import { TestWrapper } from "TestWrapper";

const Harness: FC<{ disabled?: boolean }> = ({ disabled = false }) => {
  const form = useForm<Schema>({
    defaultValues: {
      attrs: [
        {
          choices: [
            { value: "used", label: "Used choice" },
            { value: "free", label: "Free choice" },
          ],
          choicesInUse: ["used"],
        },
      ],
    } as Schema,
  });
  return (
    <>
      <ChoicesEditor control={form.control} index={0} disabled={disabled} />
      <output data-testid="choices">
        {JSON.stringify(form.watch("attrs.0.choices"))}
      </output>
    </>
  );
};

describe("ChoicesEditor", () => {
  test("renders existing choices and protects choices already in use", () => {
    render(<Harness />, { wrapper: TestWrapper });

    expect(screen.getByDisplayValue("Used choice")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Free choice")).toBeInTheDocument();
    const deleteButtons = screen.getAllByRole("button", {
      name: "delete-choice",
    });
    expect(deleteButtons[0]).toBeDisabled();
    expect(deleteButtons[1]).toBeEnabled();
  });

  test("renames and removes an unused choice without losing stable values", () => {
    render(<Harness />, { wrapper: TestWrapper });

    fireEvent.change(screen.getByDisplayValue("Free choice"), {
      target: { value: "Renamed choice" },
    });
    fireEvent.click(
      screen.getAllByRole("button", { name: "delete-choice" })[1],
    );

    expect(screen.getByTestId("choices")).toHaveTextContent(
      '[{"value":"used","label":"Used choice"}]',
    );
  });

  test("adds a draft choice without inventing a backend value", () => {
    render(<Harness />, { wrapper: TestWrapper });

    fireEvent.click(screen.getByRole("button", { name: "選択肢を追加" }));

    expect(screen.getAllByPlaceholderText("選択肢の表示名")).toHaveLength(3);
    expect(screen.getByTestId("choices")).toHaveTextContent('{"label":""}');
  });

  test("disables all editing actions", () => {
    render(<Harness disabled />, { wrapper: TestWrapper });

    expect(screen.getByDisplayValue("Used choice")).toBeDisabled();
    expect(screen.getByDisplayValue("Free choice")).toBeDisabled();
    expect(screen.getByRole("button", { name: "選択肢を追加" })).toBeDisabled();
    expect(screen.getAllByRole("button", { name: "delete-choice" })).toEqual(
      expect.arrayContaining([expect.objectContaining({ disabled: true })]),
    );
  });
});
