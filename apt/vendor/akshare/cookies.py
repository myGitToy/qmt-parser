"""
--->2025.11.25 目前AKSHARE升级了反爬措施，cookie方法基本无效，模块暂时将不做更新，日常数据更新也暂停


使用浏览器获取 Eastmoney 站点 cookies（方法4：JS 渲染/反爬更严格时）。

优先级：
1) undetected-chromedriver（推荐）
2) Playwright（如可用）
3) Selenium WebDriver（需要本地驱动）

提供：
- fetch_eastmoney_cookies_browser: 返回 cookies 字典
- ensure_eastmoney_cookies_browser: 把 cookies 写入进程环境变量 EASTMONEY_COOKIES

注意：本模块不强制安装依赖，若运行时报 ImportError，请安装相应库并完成浏览器/驱动初始化：
  - Playwright: pip install playwright; playwright install
  - undetected-chromedriver: pip install undetected-chromedriver
  - Selenium: pip install selenium
  - webdriver-manager（推荐，自动解决ChromeDriver版本匹配问题）: pip install webdriver-manager
  
自动ChromeDriver管理（推荐）：
  安装 webdriver-manager 后，会自动下载与当前Chrome版本匹配的ChromeDriver，
  解决 "This version of ChromeDriver only supports Chrome version X" 错误。
"""

from __future__ import annotations
import requests
import os
import time
from typing import Dict, Optional, Literal, Tuple
from importlib import import_module
from datetime import datetime, timezone, timedelta
from dotenv import set_key, load_dotenv  # 确保python-dotenv已安装

# Cookie 使用计数器：使用环境变量存储，确保跨进程/模块一致性
_cookie_initial_count: int = 50  # 默认初始计数值，可通过环境变量配置
_COOKIE_COUNT_ENV_KEY = "EASTMONEY_COOKIE_USAGE_COUNT"

def _format_cookie_list_to_dict(cookie_list: list[dict]) -> Dict[str, str]:
    cookies: Dict[str, str] = {}
    for c in cookie_list:
        name = c.get("name")
        value = c.get("value")
        if name and value is not None:
            cookies[name] = value
    return cookies


def _get_cookie_initial_count() -> int:
    """从环境变量获取初始计数值，默认为50"""
    try:
        count = int(os.environ.get("EASTMONEY_COOKIE_INITIAL_COUNT", "50"))
        return max(1, count)  # 至少为1
    except (ValueError, TypeError):
        return 50


def _get_current_counter() -> int:
    """从环境变量获取当前计数器值"""
    try:
        return int(os.environ.get(_COOKIE_COUNT_ENV_KEY, "0"))
    except (ValueError, TypeError):
        return 0


def _set_counter(value: int) -> None:
    """设置计数器值到环境变量"""
    os.environ[_COOKIE_COUNT_ENV_KEY] = str(value)


def _reset_cookie_counter() -> None:
    """重置 cookie 使用计数器"""
    initial_count = _get_cookie_initial_count()
    _set_counter(initial_count)
    print(f"重置 cookie 计数器为: {initial_count}")


def _decrement_cookie_counter() -> int:
    """递减 cookie 使用计数器并返回当前值"""
    current = _get_current_counter()
    new_value = current - 1
    _set_counter(new_value)
    return new_value


def _should_force_refresh_by_counter() -> bool:
    """检查是否应该根据计数器强制刷新 cookie"""
    current_counter = _get_current_counter()
    
    # 如果计数器未初始化（第一次调用），初始化它
    if current_counter == 0:
        _reset_cookie_counter()
        return False  # 第一次调用不强制刷新
    
    if current_counter <= 0:
        print(f"Cookie 使用计数器已耗尽 ({current_counter})，强制重新获取")
        return True
    return False


def get_cookie_counter_status() -> dict:
    """
    获取当前 cookie 计数器状态信息
    
    返回:
        包含计数器状态的字典
    """
    return {
        "current_count": _get_current_counter(),
        "initial_count": _get_cookie_initial_count(),
        "env_key": _COOKIE_COUNT_ENV_KEY,
        "is_initialized": _get_current_counter() > 0
    }


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

        # 尝试使用 webdriver-manager 自动获取匹配的 ChromeDriver
        driver_path = None
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            driver_path = ChromeDriverManager().install()
            print(f"使用自动管理的 ChromeDriver: {driver_path}")
            driver = uc.Chrome(driver_executable_path=driver_path, options=options)
        except ImportError:
            print("webdriver-manager 未安装，使用默认 ChromeDriver 路径...")
            driver = uc.Chrome(options=options)
        except Exception as e:
            print(f"自动管理 ChromeDriver 失败: {e}，回退到默认方式...")
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

        # 尝试使用 webdriver-manager 自动获取匹配的 ChromeDriver
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            service = Service(ChromeDriverManager().install())
            print("使用自动管理的 ChromeDriver...")
            driver = getattr(webdriver_pkg, "Chrome")(service=service, options=options)
        except ImportError:
            print("webdriver-manager 未安装，使用默认 ChromeDriver 路径...")
            driver = getattr(webdriver_pkg, "Chrome")(options=options)
        except Exception as e:
            print(f"自动管理 ChromeDriver 失败: {e}，回退到默认方式...")
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
        backends_to_try = ["uc", "playwright", "selenium"]  # 将 uc (undetected-chromedriver) 设为首选
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
            continue
    
    # 全部失败
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

            # 写入更新时间，使用标准格式
            try:
                update_var = "EASTMONEY_COOKIES_UPDATE_TIME"
                update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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


def _check_cookie_expired(expiry_time_str: str, max_age_minutes: int = 5) -> bool:
    """
    检查cookie是否过期
    
    参数:
        expiry_time_str: 格式为"%Y-%m-%d %H:%M:%S"的时间字符串
        max_age_minutes: cookie的最大有效期（分钟）
        
    返回:
        True表示已过期，False表示未过期
    """
    try:
        # 解析更新时间
        update_time = datetime.strptime(expiry_time_str, "%Y-%m-%d %H:%M:%S")
        # 计算过期时间
        expiry_time = update_time + timedelta(minutes=max_age_minutes)
        # 检查是否过期
        return datetime.now() > expiry_time
    except Exception:
        # 解析失败，认为已过期
        return True


def _load_cookies_from_env() -> Tuple[str, str]:
    """
    从环境变量或.env文件加载cookie信息
    
    返回:
        (cookie字符串, 更新时间字符串)
    """
    # 优先从环境变量加载
    cookies = os.environ.get("EASTMONEY_COOKIES", "")
    update_time = os.environ.get("EASTMONEY_COOKIES_UPDATE_TIME", "")
    
    # 如果环境变量中没有，尝试从.env文件加载
    if not cookies or not update_time:
        try:
            # 获取当前文件的绝对路径
            current_file = os.path.abspath(__file__)
            # 获取apt目录
            apt_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
            # 获取项目根目录(apt的父目录)
            project_root = os.path.dirname(apt_dir)
            # 构造.env文件的完整路径
            env_file_path = os.path.join(project_root, '.env')
            
            # 加载.env文件
            if os.path.exists(env_file_path):
                load_dotenv(env_file_path)
                cookies = os.environ.get("EASTMONEY_COOKIES", "")
                update_time = os.environ.get("EASTMONEY_COOKIES_UPDATE_TIME", "")
        except Exception as e:
            print(f"加载.env文件失败: {e}")
    
    return cookies, update_time


def get_em_cookie(
    force_refresh: bool = False, 
    save_to_env_file: bool = True,
    method: Literal["auto", "browser", "request"] = "auto",
    backend: Literal["auto", "uc", "playwright", "selenium"] = "auto",
    stock_code: str = "sh601026",
    max_age_minutes: int = 1
) -> str:
    """
    统一的 Eastmoney cookie 获取函数，支持多种获取方式和保存选项。
    新增功能：cookie 使用计数器，每次调用递减，计数器耗尽时强制刷新。
    
    参数:
        force_refresh: 是否强制刷新 cookie，不使用环境变量中的缓存
        save_to_env_file: 是否将获取的 cookie 保存到 .env 文件 (保留但不使用)
        method: 获取方式，"auto"=优先浏览器，"browser"=仅浏览器，"request"=仅请求
        backend: 浏览器后端选择，仅当 method 为 "auto" 或 "browser" 时有效
        stock_code: 股票代码，用于构造访问 URL
        max_age_minutes: cookie的最大有效期（分钟）
        
    返回:
        获取的 cookie 字符串
        
    注意：
        - 首次调用时会设置计数器为默认值（可通过环境变量 EASTMONEY_COOKIE_INITIAL_COUNT 配置，默认50）
        - 每次调用都会递减计数器，计数器 <= 0 时强制重新获取 cookie
        - 强制刷新 cookie 时会重置计数器
        - 计数器存储在环境变量中，确保跨进程/跨模块调用时状态一致
    """
    
    # 检查计数器是否需要强制刷新
    counter_force_refresh = _should_force_refresh_by_counter()
    
    # 递减计数器（仅在非强制刷新时）
    if not force_refresh and not counter_force_refresh:
        current_count = _decrement_cookie_counter()
        print(f"Cookie 计数器递减至: {current_count}")
    
    # 合并强制刷新条件
    effective_force_refresh = force_refresh or counter_force_refresh
    
    # 第1步: 从环境变量或.env文件加载cookie
    cookies, update_time = _load_cookies_from_env()
    
    # 如果没有强制刷新，且有cookie和更新时间，检查是否过期
    if not effective_force_refresh and cookies and update_time:
        # 检查cookie是否过期
        if not _check_cookie_expired(update_time, max_age_minutes):
            print(f"使用缓存的cookie，更新时间: {update_time}")
            return cookies
        else:
            print(f"Cookie已过期，更新时间: {update_time}，最大有效期: {max_age_minutes}分钟")
    
    # 第2步: 如果需要刷新cookie或cookie已过期，重新获取
    cookies = ""
    
    if method == "request" or method == "auto":
        # 尝试简单请求方式
        try:
            print("尝试使用简单请求方式获取 cookie...")
            cookies = ensure_eastmoney_cookies(force_refresh=True)
            if cookies:
                print("简单请求方式获取 cookie 成功")
            elif method == "request":
                print("简单请求方式获取 cookie 失败")
        except Exception as e:
            print(f"简单请求方式获取 cookie 异常: {e}")
            if method == "request":
                raise
    
    # 如果简单请求失败且允许浏览器方式，则尝试浏览器方式
    if not cookies and (method == "browser" or method == "auto"):
        try:
            print("尝试使用浏览器方式获取 cookie...")
            cookies = ensure_eastmoney_cookies_from_stock_page(
                force_refresh=True,
                stock_code=stock_code,
                backend=backend
            )
            if cookies:
                print("浏览器方式获取 cookie 成功")
            else:
                print("浏览器方式获取 cookie 失败")
        except Exception as e:
            print(f"浏览器方式获取 cookie 异常: {e}")
            if method == "browser":
                raise
    
    # 如果未获取到 cookie，返回空字符串
    if not cookies:
        print("所有方式均未获取到有效 cookie")
        return ""
    
    # 第3步: 成功获取 cookie 后重置计数器
    _reset_cookie_counter()
    
    # 第4步: 将获取的 cookie 保存到环境变量
    os.environ["EASTMONEY_COOKIES"] = cookies
    
    # 保存更新时间
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.environ["EASTMONEY_COOKIES_UPDATE_TIME"] = current_time
    
    # 如需保存到文件(保留此功能但不再主动使用)
    if save_to_env_file:
        save_cookies_to_env_file(cookies, current_time)
    
    return cookies


def save_cookies_to_env_file(cookies: str, update_time: str) -> None:
    """
    将cookie保存到.env文件
    
    注意：此函数保留但不再主动使用，为了未来可能的升级
    
    参数:
        cookies: cookie字符串
        update_time: 更新时间
    """
    # 获取当前文件的绝对路径
    current_file = os.path.abspath(__file__)
    
    # 获取apt目录
    apt_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    
    # 获取项目根目录(apt的父目录)
    project_root = os.path.dirname(apt_dir)
    
    # 构造.env文件的完整路径
    env_file_path = os.path.join(project_root, '.env')
    
    print(f"获取到项目根目录: {project_root}")
    print(f"使用项目根目录.env文件: {env_file_path}")
    
    # 尝试写入.env文件
    try:
        # 使用set_key更新环境变量
        set_key(env_file_path, "EASTMONEY_COOKIES", cookies)
        set_key(env_file_path, "EASTMONEY_COOKIES_UPDATE_TIME", update_time)
        print(f"已通过dotenv.set_key()更新 {env_file_path} 文件 - 更新时间: {update_time}")
    except Exception as e:
        print(f"写入 {env_file_path} 文件失败: {e}")
        print("尝试写入临时备份文件...")
        
        # 尝试在当前目录创建备用.env文件
        try:
            current_dir = os.path.dirname(current_file)
            backup_env_path = os.path.join(current_dir, '.env.backup')
            
            with open(backup_env_path, 'w', encoding='utf-8') as f:
                f.write(f"# Backup .env file created at {update_time}\n")
                f.write(f"EASTMONEY_COOKIES=\"{cookies}\"\n")
                f.write(f"EASTMONEY_COOKIES_UPDATE_TIME=\"{update_time}\"\n")
            print(f"已创建备用文件: {backup_env_path}")
        except Exception as e2:
            print(f"创建备用文件也失败: {e2}")
            print("cookies已保存在环境变量中，但未能写入任何文件。")
    
    return cookies


if __name__ == "__main__":
    # 测试: 首先尝试从环境变量获取cookie
    cookies, update_time = _load_cookies_from_env()
    print(f"从环境变量加载的cookie: {cookies[:50] + '...' if len(cookies) > 50 else cookies}")
    print(f"从环境变量加载的更新时间: {update_time}")
    
    # 检查cookie是否过期
    if update_time:
        is_expired = _check_cookie_expired(update_time, max_age_minutes=5)
        print(f"Cookie过期状态: {'已过期' if is_expired else '有效'}")
    
    # 使用新的统一函数获取cookie (不强制刷新，仅当过期时才获取新cookie)
    print("\n调用get_em_cookie获取cookie:")
    cookies = get_em_cookie(
        force_refresh=False,  # 不强制刷新，仅当过期时刷新
        save_to_env_file=False,  # 不保存到.env文件
        method="auto",  # 自动选择方法
        backend="uc",  # 优先使用 undetected-chromedriver
        max_age_minutes=5  # 5分钟有效期
    )
    
    if cookies:
        print("获取到的cookie:", cookies[:50] + "..." if len(cookies) > 50 else cookies)
        print("当前环境变量中的cookie:", os.environ.get("EASTMONEY_COOKIES", "")[:50] + "...")
        print("当前环境变量中的更新时间:", os.environ.get("EASTMONEY_COOKIES_UPDATE_TIME", ""))
        print("Cookie 获取成功!")
    else:
        print("未获取到有效 cookie")
