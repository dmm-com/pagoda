import { useCallback, useState } from "react";

export function useError(): (error: Error) => void {
  const [, setState] = useState();
  return useCallback((error: Error) => {
    setState(() => {
      throw error;
    });
  }, []);
}
