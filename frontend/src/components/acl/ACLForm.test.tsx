/**
 */

import { act, render, screen } from "@testing-library/react";
import { FC } from "react";
import { useForm } from "react-hook-form";

import { Schema } from "./aclForm/ACLFormSchema";

import { TestWrapper } from "TestWrapper";
import { ACLForm } from "components/acl/ACLForm";
import i18n from "i18n/config";
import { ACLType } from "services/ACLUtil";

const Wrapper: FC = () => {
  const { control, watch } = useForm<Schema>({
    defaultValues: {
      isPublic: true,
      defaultPermission: ACLType.Nothing,
      roles: [],
    },
  });

  return <ACLForm control={control} watch={watch} />;
};

test("should render a component with essential props", function () {
  expect(() =>
    render(<Wrapper />, {
      wrapper: TestWrapper,
    }),
  ).not.toThrow();
});

test("renders in English", async () => {
  await act(async () => {
    await i18n.changeLanguage("en");
  });

  render(<Wrapper />, { wrapper: TestWrapper });

  expect(screen.getByText("Public restriction settings")).toBeInTheDocument();
  expect(screen.getByText("Everyone")).toBeInTheDocument();
});
