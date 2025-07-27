# 不要使用 import csv，因为会导致循环导入
import importlib.util
import sys
from datetime import datetime, timedelta

# 直接从标准库导入csv模块
spec = importlib.util.find_spec('csv', sys.path[1:])
csv_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(csv_module)

data = [
    ["NAME", "ID", "SIZE", "MODIFIED"],
    ["qwen2.5:14b", "7cdf5a0187d5", "9.0 GB", "5 days ago"],
    ["phi4:latest", "ac896e5b8b34", "9.1 GB", "5 days ago"],
    ["gemma3:27b", "30ddded7fba6", "17 GB", "5 days ago"],
    ["linux6200/bge-reranker-v2-m3:latest", "abf5c6d8bc56", "1.2 GB", "2 weeks ago"],
    ["qwq:32b", "cc1091b0e276", "19 GB", "2 weeks ago"],
    ["bge-m3:latest", "790764642607", "1.2 GB", "6 weeks ago"],
    ["bge-large:latest", "b3d71c928059", "670 MB", "6 weeks ago"],
    ["huihui_ai/deepseek-r1-abliterated:32b", "fb53b3296912", "19 GB", "6 weeks ago"],
    ["deepseek-r1:32b", "38056bbcbb2d", "19 GB", "7 weeks ago"],
    ["glm4:latest", "5b699761eca5", "5.5 GB", "8 months ago"],
    ["qwen2:latest", "e0d4e1163c58", "4.4 GB", "8 months ago"],
    ["qwen2:7b", "e0d4e1163c58", "4.4 GB", "8 months ago"],
    ["llama3:latest", "365c0bd3c000", "4.7 GB", "8 months ago"]
]

def convert_to_date(modified_str):
    if "days ago" in modified_str:
        days = int(modified_str.split()[0])
        return (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    elif "weeks ago" in modified_str:
        weeks = int(modified_str.split()[0])
        return (datetime.now() - timedelta(weeks=weeks)).strftime('%Y-%m-%d')
    elif "months ago" in modified_str:
        months = int(modified_str.split()[0])
        return (datetime.now() - timedelta(days=months*30)).strftime('%Y-%m-%d')
    else:
        return modified_str

with open('output.csv', 'w', newline='', encoding='utf-8') as csvfile:
    csvwriter = csv_module.writer(csvfile)
    for row in data:
        if row[0] != "NAME":
            row[3] = convert_to_date(row[3])
        csvwriter.writerow(row)