#!/usr/bin/env python3
import sys
import os
from playwright.sync_api import sync_playwright

def render_html_to_image(html_path: str, output_path: str):
    """将固定尺寸的HTML渲染为图片"""
    # 获取绝对路径
    abs_html_path = f"file://{os.path.abspath(html_path)}"
    
    with sync_playwright() as p:
        # 启动无头浏览器
        browser = p.chromium.launch(headless=True)
        # 严格设定视口大小为 3:4 (1080x1440)
        page = browser.new_page(viewport={"width": 1080, "height": 1440})
        
        # 跳转并等待网络空闲（确保Google字体和CSS加载完毕）
        page.goto(abs_html_path, wait_until="networkidle")
        
        # 定位到 .card-page 容器并截图
        element = page.locator('.card-page').first
        element.screenshot(path=output_path)
        
        browser.close()
        print(f"[成功] 图片已生成: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("使用方法: python html-to-image.py <输入HTML路径> <输出图片路径>")
        sys.exit(1)
        
    render_html_to_image(sys.argv[1], sys.argv[2])