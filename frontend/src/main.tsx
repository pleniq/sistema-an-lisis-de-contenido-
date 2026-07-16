import React from "react";
import ReactDOM from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import App from "./App";
import GaleriaPage from "./pages/GaleriaPage";
import AnalisisPage from "./pages/AnalisisPage";
import ConfigPage from "./pages/ConfigPage";
import "./styles.css";

const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <GaleriaPage /> },
      { path: "analisis", element: <AnalisisPage /> },
      { path: "config", element: <ConfigPage /> },
    ],
  },
]);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode><RouterProvider router={router} /></React.StrictMode>
);
