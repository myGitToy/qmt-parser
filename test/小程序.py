import webbrowser

# 微信小程序的网页 URL
url = "#小程序://FancyFancy/VeZXdFGLpujBETy"

# 指定使用 Chrome 浏览器
chrome_path = 'C:\Program Files\Google\Chrome\Application\chrome.exe %s'
webbrowser.get(chrome_path).open(url)