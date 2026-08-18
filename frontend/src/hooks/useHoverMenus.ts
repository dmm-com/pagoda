import { MouseEvent as ReactMouseEvent, useEffect, useRef, useState } from "react";

type MenuKey = string | number;

const isPointOverElement = (
  x: number,
  y: number,
  el: HTMLElement | null,
): boolean => {
  if (!el) return false;
  const rect = el.getBoundingClientRect();
  return x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom;
};

export function useHoverMenus() {
  const [anchors, setAnchors] = useState<Record<MenuKey, HTMLElement | null>>(
    {},
  );
  const triggerRefs = useRef<Record<MenuKey, HTMLElement | null>>({});
  const paperRefs = useRef<Record<MenuKey, HTMLElement | null>>({});

  useEffect(() => {
    if (Object.values(anchors).every((v) => v == null)) {
      return;
    }

    const handleMouseMove = (e: globalThis.MouseEvent) => {
      Object.keys(anchors).forEach((key) => {
        if (anchors[key] == null) return;
        const inside =
          isPointOverElement(e.clientX, e.clientY, triggerRefs.current[key]) ||
          isPointOverElement(e.clientX, e.clientY, paperRefs.current[key]);
        if (!inside) {
          setAnchors((prev) => ({ ...prev, [key]: null }));
        }
      });
    };

    document.addEventListener("mousemove", handleMouseMove);
    return () => document.removeEventListener("mousemove", handleMouseMove);
  }, [anchors]);

  const getTriggerProps = (key: MenuKey) => ({
    ref: (el: HTMLElement | null) => {
      triggerRefs.current[key] = el;
    },
    onMouseEnter: (e: ReactMouseEvent<HTMLElement>) =>
      setAnchors((prev) => ({ ...prev, [key]: e.currentTarget })),
    onMouseLeave: () => setAnchors((prev) => ({ ...prev, [key]: null })),
  });

  const getMenuProps = (key: MenuKey) => ({
    anchorEl: anchors[key] ?? null,
    open: Boolean(anchors[key]),
    onClose: (event: object, reason: string) => {
      const { clientX, clientY } = event as { clientX: number; clientY: number };
      if (
        reason === "backdropClick" &&
        isPointOverElement(clientX, clientY, triggerRefs.current[key])
      ) {
        return;
      }
      setAnchors((prev) => ({ ...prev, [key]: null }));
    },
    slotProps: {
      paper: {
        ref: (el: HTMLElement | null) => {
          paperRefs.current[key] = el;
        },
      },
    },
    MenuListProps: {
      onMouseLeave: () => setAnchors((prev) => ({ ...prev, [key]: null })),
    },
  });

  return { getTriggerProps, getMenuProps };
}
