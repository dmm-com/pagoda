import { z } from "zod";

// see https://github.com/colinhacks/zod/issues/372#issuecomment-826380330
export const schemaForType =
  <T>() =>
  <S extends z.ZodType<T, any, any>>(arg: S) => {
    return arg;
  };
