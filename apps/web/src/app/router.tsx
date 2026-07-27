import { createBrowserRouter } from "react-router";
import { RouterProvider } from "react-router/dom";

import { App } from "@/app/App";

const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
