/**
 * App 主组件
 */

import { ConfigProvider } from "antd";
import { RouterProvider } from "react-router-dom";
import router from "./router";
import { darkTheme } from "./theme/darkTheme";

function App() {
    return (
        <ConfigProvider theme={darkTheme}>
            <RouterProvider router={router} />
        </ConfigProvider>
    );
}

export default App;
