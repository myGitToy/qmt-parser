/**
 * API 客户端配置
 * 参考 HMU 项目的 client.ts
 */

import axios, { AxiosError } from "axios";

// 创建 axios 实例
const client = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || "/api/v1",
    timeout: 30000,
    headers: {
        "Content-Type": "application/json",
    },
});

// 请求拦截器
client.interceptors.request.use(
    (config) => {
        // 可以在这里添加认证 token
        // const token = localStorage.getItem("token");
        // if (token) {
        //     config.headers.Authorization = `Bearer ${token}`;
        // }

        return config;
    },
    (error: AxiosError) => {
        return Promise.reject(error);
    }
);

// 响应拦截器
client.interceptors.response.use(
    (response) => {
        return response.data;
    },
    (error: AxiosError<any>) => {
        // 统一错误处理，返回详细的错误信息
        let errorMessage = "请求失败";
        let errorDetail: any = {
            status: null,
            message: "",
            type: "",
        };

        if (error.response) {
            // 服务器返回了错误响应
            errorDetail.status = error.response.status;
            const data = error.response.data;

            if (typeof data === "string") {
                errorDetail.message = data;
            } else if (data?.detail) {
                errorDetail.message = data.detail;
            } else if (data?.message) {
                errorDetail.message = data.message;
            } else {
                errorDetail.message = JSON.stringify(data);
            }

            // 根据状态码和错误消息生成用户友好的提示
            switch (error.response.status) {
                case 400:
                    errorDetail.type = "INVALID_REQUEST";
                    errorMessage = `请求参数错误: ${errorDetail.message}`;
                    break;
                case 404:
                    errorDetail.type = "NOT_FOUND";
                    errorMessage = `未找到数据: ${errorDetail.message}`;
                    break;
                case 500:
                    errorDetail.type = "SERVER_ERROR";
                    // 检查是否是数据源配置错误
                    if (errorDetail.message.includes("Tushare") ||
                        errorDetail.message.includes("token") ||
                        errorDetail.message.includes("认证")) {
                        errorMessage = "数据源配置错误：请检查 Tushare Token 是否正确配置";
                    } else {
                        errorMessage = `服务器错误: ${errorDetail.message}`;
                    }
                    break;
                case 503:
                    errorDetail.type = "SERVICE_UNAVAILABLE";
                    errorMessage = "服务暂时不可用，请稍后重试";
                    break;
                default:
                    errorDetail.type = "UNKNOWN_ERROR";
                    errorMessage = `请求失败 (${error.response.status}): ${errorDetail.message}`;
            }
        } else if (error.request) {
            // 请求已发送但没有收到响应
            errorDetail.type = "NETWORK_ERROR";
            errorMessage = "网络错误：无法连接到服务器，请检查后端服务是否启动";
            errorDetail.message = "后端服务可能未启动或端口配置错误";
        } else {
            // 请求配置错误
            errorDetail.type = "CONFIG_ERROR";
            errorMessage = `请求配置错误: ${error.message}`;
            errorDetail.message = error.message;
        }

        // 将详细错误信息附加到 error 对象上
        (error as any).userMessage = errorMessage;
        (error as any).errorDetail = errorDetail;

        // 同时在控制台输出完整错误信息（便于调试）
        console.error("API 请求失败:", {
            url: error.config?.url,
            status: errorDetail.status,
            type: errorDetail.type,
            message: errorDetail.message,
            userMessage: errorMessage,
        });

        return Promise.reject(error);
    }
);

export default client;
