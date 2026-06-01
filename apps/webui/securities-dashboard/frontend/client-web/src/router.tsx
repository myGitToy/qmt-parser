/**
 * 路由配置
 */

import { createBrowserRouter, Navigate } from "react-router-dom";
import { MainLayout } from "./components/layout/MainLayout";
import { Dashboard } from "./pages/dashboard/Dashboard";

export const router = createBrowserRouter([
    {
        path: "/",
        element: <MainLayout />,
        children: [
            {
                index: true,
                element: <Dashboard />,
            },
            {
                path: "market",
                element: <Dashboard />,
            },
            {
                path: "portfolio",
                lazy: () => import("./pages/portfolio/Portfolio"),
            },
            {
                path: "analysis",
                lazy: () => import("./pages/analysis/Analysis"),
            },
        ],
    },
]);
