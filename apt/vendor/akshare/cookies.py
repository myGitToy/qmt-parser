"""
使用浏览器获取 Eastmoney 站点 cookies（方法4：JS 渲染/反爬更严格时）。

优先级：
1) Playwright（推荐）
2) undetected-chromedriver（如可用）
3) Selenium WebDriver（需要本地驱动）

提供：
- fetch_eastmoney_cookies_browser: 返回 cookies 字典
- ensure_eastmoney_cookies_browser: 把 cookies 写入进程环境变量 EASTMONEY_COOKIES

注意：本模块不强制安装依赖，若运行时报 ImportError，请安装相应库并完成浏览器/驱动初始化：
  - Playwright: pip install playwright; playwright install
  - undetected-chromedriver: pip install undetected-chromedriver
  - Selenium: pip install selenium; 并安装 ChromeDriver 或对应浏览器驱动
"""

from __future__ import annotations
import requests
import os
from typing import Dict, Optional, Literal
from importlib import import_module
from datetime import datetime, timezone


def _format_cookie_list_to_dict(cookie_list: list[dict]) -> Dict[str, str]:
    cookies: Dict[str, str] = {}
    for c in cookie_list:
        name = c.get("name")
        value = c.get("value")
        if name and value is not None:
            cookies[name] = value
    return cookies


def fetch_eastmoney_cookies_browser(
    url: str = "https://quote.eastmoney.com/sh601026.html",
    backend: Literal["auto", "playwright", "uc", "selenium"] = "auto",
    headless: bool = True,
    wait_until: str = "domcontentloaded",
    timeout_ms: int = 60000,
) -> Dict[str, str]:
    """
    通过有头/无头浏览器访问 Eastmoney 页面并提取 cookies。

    参数：
        url: 访问地址
        backend: 选择后端，默认 auto（按优先级自动选择）
        headless: 是否无头
        wait_until: playwright 的等待策略（networkidle/load/domcontentloaded）
        timeout_ms: 页面加载等待超时（毫秒）
    返回：
        cookies 字典
    """

    last_error: Optional[Exception] = None

    def try_playwright() -> Dict[str, str]:
        print("尝试使用 Playwright 获取 cookies...")
        # 动态导入，避免静态依赖报错
        _pl = import_module("playwright.sync_api")
        sync_playwright = getattr(_pl, "sync_playwright")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(
                locale="zh-CN",
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/119.0.0.0 Safari/537.36"
                ),
            )
            page = context.new_page()
            print(f"正在访问: {url}")
            page.goto(url, wait_until=wait_until, timeout=timeout_ms)
            # 等待页面基本加载完成，然后获取 cookies
            print("等待页面加载...")
            page.wait_for_timeout(2000)  # 等待2秒让JS设置cookies
            cookies_list = context.cookies()
            print(f"获取到 {len(cookies_list)} 个 cookies")
            browser.close()
        return _format_cookie_list_to_dict(cookies_list)

    def try_uc() -> Dict[str, str]:
        print("尝试使用 undetected-chromedriver 获取 cookies...")
        uc = import_module("undetected_chromedriver")
        options = uc.ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--lang=zh-CN")

        driver = uc.Chrome(options=options)
        try:
            print(f"正在访问: {url}")
            driver.get(url)
            # 等一会儿让页面/JS 初始化
            import time
            print("等待页面加载...")
            time.sleep(3.0)  # 增加等待时间
            cookies_list = driver.get_cookies()
            print(f"获取到 {len(cookies_list)} 个 cookies")
            return _format_cookie_list_to_dict(cookies_list)
        finally:
            driver.quit()

    def try_selenium() -> Dict[str, str]:
        webdriver_pkg = import_module("selenium.webdriver")
        chrome_options_mod = import_module("selenium.webdriver.chrome.options")
        Options = getattr(chrome_options_mod, "Options")

        options = Options()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--lang=zh-CN")

        # 实例化 Chrome 驱动
        driver = getattr(webdriver_pkg, "Chrome")(options=options)
        try:
            driver.get(url)
            import time
            time.sleep(3.0)  # 增加等待时间
            cookies_list = driver.get_cookies()
            return _format_cookie_list_to_dict(cookies_list)
        finally:
            driver.quit()

        # backend 选择逻辑
        backends_to_try: list[str]
        if backend == "auto":
            backends_to_try = ["playwright", "uc", "selenium"]
        else:
            backends_to_try = [backend]

    for be in backends_to_try:
        try:
            print(f"尝试后端: {be}")
            if be == "playwright":
                result = try_playwright()
                print(f"Playwright 返回了 {len(result) if result else 0} 个 cookies")
                return result
            if be == "uc":
                result = try_uc()
                print(f"UC 返回了 {len(result) if result else 0} 个 cookies")
                return result
            if be == "selenium":
                result = try_selenium()
                print(f"Selenium 返回了 {len(result) if result else 0} 个 cookies")
                return result
        except Exception as e:  # 记录错误，继续尝试下一个后端
            print(f"后端 {be} 失败: {e}")
            last_error = e
            continue        # 全部失败
        if last_error:
            raise RuntimeError(
                "无法通过浏览器后端获取 Eastmoney cookies，请安装并初始化 playwright/selenium/undetected-chromedriver 后重试。"
            ) from last_error
        raise RuntimeError("未能获取 Eastmoney cookies（未知原因）")


def ensure_eastmoney_cookies(
    env_var: str = "EASTMONEY_COOKIES",
    force_refresh: bool = False,
    timeout: int = 10,
) -> str:
    """
    用简单请求方式确保环境变量 EASTMONEY_COOKIES 存在；若没有或强制刷新则获取并写入。
    返回 cookies 字符串（k1=v1; k2=v2）。
    """
    if not force_refresh:
        exist = os.environ.get(env_var)
        if exist:
            return exist

    # 使用 requests 获取 cookies
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        # 从响应中提取 cookies
        cookies_dict = response.cookies.get_dict()
        if cookies_dict:
            cookies_str = "; ".join(f"{k}={v}" for k, v in cookies_dict.items())
            os.environ[env_var] = cookies_str
            return cookies_str
        else:
            # 如果没有 cookies，尝试从响应头中获取 Set-Cookie
            set_cookie_header = response.headers.get('Set-Cookie')
            if set_cookie_header:
                cookies_list = []
                # 处理多个 Set-Cookie 头（可能用逗号分隔）
                for cookie_header in set_cookie_header.split(','):
                    cookie_header = cookie_header.strip()
                    # 简单解析 Set-Cookie 头
                    if ';' in cookie_header:
                        cookie_part = cookie_header.split(';')[0]
                        if '=' in cookie_part:
                            cookies_list.append(cookie_part.strip())
                if cookies_list:
                    cookies_str = "; ".join(cookies_list)
                    os.environ[env_var] = cookies_str
                    return cookies_str

    except Exception as e:
        print(f"获取 Eastmoney cookies 失败: {e}")

    # 如果获取失败，返回空字符串
    return ""


def ensure_eastmoney_cookies_from_stock_page(
    env_var: str = "EASTMONEY_COOKIES",
    force_refresh: bool = False,
    stock_code: str = "sh601026",
    backend: Literal["auto", "playwright", "uc", "selenium"] = "auto",
) -> str:
    """
    强制访问股票页面 https://quote.eastmoney.com/{stock_code}.html 来获取 cookies。
    这可以模拟真实的用户访问行为，更容易获取到有效的 cookies。

    参数：
        env_var: 环境变量名
        force_refresh: 是否强制刷新
        stock_code: 股票代码，如 "sh601026"
        backend: 浏览器后端

    返回：
        cookies 字符串（k1=v1; k2=v2）
    """
    if not force_refresh:
        exist = os.environ.get(env_var)
        if exist:
            return exist

    # 构造股票页面URL
    url = f"https://quote.eastmoney.com/{stock_code}.html"

    try:
        cookie_dict = fetch_eastmoney_cookies_browser(
            url=url,
            backend=backend,
            headless=True,
            wait_until="networkidle",
            timeout_ms=30000
        )

        if cookie_dict:
            cookies_str = "; ".join(f"{k}={v}" for k, v in cookie_dict.items())
            # 写入进程环境变量，并尝试通过 os.putenv 让子进程也能看到
            os.environ[env_var] = cookies_str
            try:
                os.putenv(env_var, cookies_str)
            except Exception:
                # putenv 在某些环境下可能失败，忽略错误
                pass

            # 写入更新时间，使用 UTC ISO 格式
            try:
                update_var = "EASTMONEY_COOKIES_UPDATE_DATE"
                update_time = datetime.now(timezone.utc).isoformat()
                os.environ[update_var] = update_time
                try:
                    os.putenv(update_var, update_time)
                except Exception:
                    pass
            except Exception:
                # 如果时间写入失败，忽略
                pass

            return cookies_str

    except Exception as e:
        print(f"通过股票页面获取 Eastmoney cookies 失败: {e}")

    # 如果获取失败，返回空字符串
    return ""


def ensure_eastmoney_cookies_browser(
    env_var: str = "EASTMONEY_COOKIES",
    force_refresh: bool = False,
    backend: Literal["auto", "playwright", "uc", "selenium"] = "auto",
) -> str:
    """
    用浏览器方式确保环境变量 EASTMONEY_COOKIES 存在；若没有或强制刷新则获取并写入。
    返回 cookies 字符串（k1=v1; k2=v2）。
    """
    if not force_refresh:
        exist = os.environ.get(env_var)
        if exist:
            return exist

    cookie_dict = fetch_eastmoney_cookies_browser(backend=backend)
    cookies_str = "; ".join(f"{k}={v}" for k, v in cookie_dict.items())
    os.environ[env_var] = cookies_str
    return cookies_str


if __name__ == "__main__":
    # 测试简单请求方式
    s = ensure_eastmoney_cookies(force_refresh=True)
    print("EASTMONEY_COOKIES=", s)
    
    # 如果简单方式失败，尝试浏览器方式
    if not s:
        print("简单请求失败，尝试浏览器方式...")
        try:
            s = ensure_eastmoney_cookies_browser(force_refresh=True)
            print("EASTMONEY_COOKIES=", s)
        except Exception as e:
            print(f"浏览器方式也失败: {e}")
