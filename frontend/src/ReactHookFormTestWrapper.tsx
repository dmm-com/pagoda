import React from "react";
import { useForm } from "react-hook-form";
import { FieldValues, UseFormReturn } from "react-hook-form/dist/types";
import { DefaultValues } from "react-hook-form/dist/types/form";

interface Props<
  TFieldValues extends FieldValues = FieldValues,
  TContext = any
> {
  defaultValues: DefaultValues<TFieldValues>;
  render: (props: UseFormReturn<TFieldValues, TContext>) => React.ReactNode;
}

export const ReactHookFormTestWrapper = <
  TFieldValues extends FieldValues = FieldValues,
  TContext = any
>({
  defaultValues,
  render,
}: Props<TFieldValues, TContext>) => {
  const props = useForm<TFieldValues, TContext>({
    defaultValues,
  });

  return <>{render(props)}</>;
};
