import { AdvancedSearchResult } from "@dmm-com/airone-apiclient-typescript-fetch";
import { useLayoutEffect, useRef } from "react";

/** Match joined values to the rendered border-box heights of their source array. */
export const useJoinedAttributeRowHeights = (
  results: AdvancedSearchResult,
  attrNames: string[],
  joinedAttrSources: Record<string, string>,
) => {
  const bodyRef = useRef<HTMLTableSectionElement>(null);

  useLayoutEffect(() => {
    const body = bodyRef.current;
    if (!body) return;

    const groups: { source: Element[]; target: HTMLElement[] }[] = [];
    for (const row of Array.from(body.rows)) {
      const cells = new Map(
        Array.from(row.cells).map((cell) => [
          cell.dataset.searchAttribute,
          cell,
        ]),
      );
      for (const list of Array.from(
        row.querySelectorAll<HTMLElement>("[data-source-attribute]"),
      )) {
        const sourceCell = cells.get(list.dataset.sourceAttribute);
        const sourceList = sourceCell?.querySelector(":scope > .MuiList-root");
        if (!sourceList) continue;
        groups.push({
          source: Array.from(sourceList.children),
          target: Array.from(list.children).filter(
            (child): child is HTMLElement => child instanceof HTMLElement,
          ),
        });
      }
    }

    const syncHeights = () => {
      // Read all source sizes before writing styles to avoid repeated layout.
      const measurements = groups.flatMap(({ source, target }) =>
        target.map((element, index) => ({
          element,
          height: source[index]?.getBoundingClientRect().height,
        })),
      );
      for (const { element, height } of measurements) {
        const nextHeight = height != null && height > 0 ? `${height}px` : "";
        if (element.style.height !== nextHeight) {
          element.style.height = nextHeight;
        }
      }
    };

    syncHeights();
    const observer =
      typeof ResizeObserver === "undefined"
        ? undefined
        : new ResizeObserver(syncHeights);
    for (const source of new Set(groups.flatMap((group) => group.source))) {
      observer?.observe(source, { box: "border-box" });
    }
    window.addEventListener("resize", syncHeights);

    return () => {
      observer?.disconnect();
      window.removeEventListener("resize", syncHeights);
      for (const { target } of groups) {
        for (const element of target) element.style.height = "";
      }
    };
  }, [results, attrNames, joinedAttrSources]);

  return bodyRef;
};
