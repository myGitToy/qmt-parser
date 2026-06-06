/**
 * 路由配置
 */

import { createBrowserRouter } from "react-router-dom";
import { MainLayout } from "./components/layout/MainLayout";
import { Dashboard } from "./pages/dashboard/Dashboard";
import { MarketTest } from "./pages/MarketTest";

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
                path: "test",
                element: <MarketTest />,
            },
            {
                path: "portfolio",
                lazy: () => import("./pages/portfolio/Portfolio"),
            },
            {
                path: "analysis",
                lazy: () => import("./pages/analysis/Analysis"),
            },
            {
                path: "qmt",
                lazy: () => import("./pages/qmt/QmtDataExplorer").then(m => ({ Component: m.QmtDataExplorer })),
            },
        ],
    },
]);
