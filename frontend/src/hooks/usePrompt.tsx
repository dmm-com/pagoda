import { useEffect } from "react";
import { useBlocker } from "react-router";

export const usePrompt = (when: boolean, message: string) => {
  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) =>
      when && currentLocation.pathname !== nextLocation.pathname,
  );

  useEffect(() => {
    if (blocker.state === "blocked") {
      if (window.confirm(message)) {
        // eslint-disable-next-line react-you-might-not-need-an-effect/no-pass-data-to-parent -- react-router's useBlocker API requires responding to state changes via effect
        blocker.proceed();
      } else {
        // eslint-disable-next-line react-you-might-not-need-an-effect/no-pass-data-to-parent -- react-router's useBlocker API requires responding to state changes via effect
        blocker.reset();
      }
    }
  }, [blocker, message]);
};
