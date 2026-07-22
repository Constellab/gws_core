import { createElement, useContext } from "react";
import { MantineProvider } from "@mantine/core";

import { ColorModeContext } from "$/utils/context";

export default function MemoizedMantineProvider({ children }) {
  const { resolvedColorMode } = useContext(ColorModeContext);

  return createElement(
    MantineProvider,
    {
      forceColorScheme: resolvedColorMode,
    },
    children
  );
}
