import { useEffect } from "react";

interface PageTitleOptions {
  prefix?: string;
}

export const usePageTitle = (title?: string, options?: PageTitleOptions) => {
  useEffect(() => {
    const originalTitle = document.title;
    const prefix = options?.prefix;

    if (title) {
      document.title = prefix ? `${prefix} - ${title}` : title;
    } else {
      document.title = originalTitle;
    }

    return () => {
      document.title = originalTitle;
    };
  }, [title, options?.prefix]);
};
