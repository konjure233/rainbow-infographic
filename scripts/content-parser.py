#!/usr/bin/env python3
"""
彩虹渐变信息图内容解析器
用于帮助分析用户输入的文字内容，提取关键信息用于信息图生成
"""

import re
import json
from typing import List, Dict, Any, Tuple


class ContentParser:
    """内容解析器，用于从用户输入中提取结构化信息"""
    
    def __init__(self, text: str):
        """
        初始化解析器
        Args:
            text: 用户输入的文本内容
        """
        self.text = text.strip()
        self.lines = [line.strip() for line in self.text.split('\n') if line.strip()]
        
    def extract_title(self) -> str:
        """从文本中提取标题"""
        # 如果第一行看起来像标题（较短，有标点结尾）
        if self.lines and len(self.lines[0]) < 100:
            title = self.lines[0]
            # 去掉常见的标点结尾
            title = re.sub(r'[:：。.?!？!]$', '', title)
            return title
        
        # 如果没有明确的标题，生成一个
        words = self.text[:50].split()
        if len(words) > 3:
            return ' '.join(words[:3]) + '...'
        return "信息图内容摘要"
    
    def extract_key_points(self) -> List[Dict[str, str]]:
        """提取关键要点"""
        points = []
        
        # 查找编号列表（如1. 2. 3.）
        numbered_pattern = r'^(\d+)[\.、]?\s*(.+)$'
        
        # 查找项目符号列表（如- * •）
        bullet_pattern = r'^[-*•]\s*(.+)$'
        
        for line in self.lines:
            # 跳过太长的行（可能是段落）
            if len(line) > 200:
                continue
                
            # 尝试匹配编号列表
            numbered_match = re.match(numbered_pattern, line)
            if numbered_match:
                point_text = numbered_match.group(2)
                if len(point_text) > 10:  # 太短的可能不是真正的要点
                    points.append({
                        'text': point_text,
                        'type': 'numbered'
                    })
                continue
            
            # 尝试匹配项目符号列表
            bullet_match = re.match(bullet_pattern, line)
            if bullet_match:
                point_text = bullet_match.group(1)
                if len(point_text) > 10:
                    points.append({
                        'text': point_text,
                        'type': 'bullet'
                    })
                continue
        
        # 如果没有找到列表格式，尝试从段落中提取关键句
        if not points:
            sentences = re.split(r'[。.?!？!]', self.text)
            for sentence in sentences:
                sentence = sentence.strip()
                if 20 <= len(sentence) <= 100:  # 合理的句子长度
                    points.append({
                        'text': sentence,
                        'type': 'sentence'
                    })
                if len(points) >= 8:  # 最多提取4-6个要点
                    break
        
        return points
    
    def extract_numbers(self) -> List[Dict[str, Any]]:
        """提取数字和百分比"""
        numbers = []
        
        # 查找数字和百分比
        number_patterns = [
            (r'(\d+(?:\.\d+)?)%', 'percent'),  # 百分比
            (r'(\d+(?:\.\d+)?)(?:万|百万|千万|亿|十亿|万亿)', 'number_with_unit'),  # 带单位数字
            (r'(\d+(?:\.\d+)?)(?=\s*(?:倍|倍率|次))', 'times'),  # 倍数
            (r'\+?(\d+(?:\.\d+)?)%', 'growth'),  # 增长百分比
            (r'(\d+(?:\.\d+)?)', 'number'),  # 纯数字
        ]
        
        for pattern, num_type in number_patterns:
            matches = re.finditer(pattern, self.text)
            for match in matches:
                value = match.group(1)
                context = self.get_context(match.start(), match.end())
                
                # 评估数字的重要性
                importance = self.evaluate_number_importance(value, num_type, context)
                
                numbers.append({
                    'value': value,
                    'type': num_type,
                    'context': context,
                    'importance': importance,
                    'position': match.start()
                })
        
        # 按重要性排序
        numbers.sort(key=lambda x: x['importance'], reverse=True)
        return numbers[:5]  # 返回最重要的5个数字
    
    def extract_concept(self) -> str:
        """提取核心概念（一句话概括）"""
        # 尝试找总结性语句
        summary_keywords = ['总结来说', '总而言之', '总的来说', '核心是', '关键在于']
        
        for keyword in summary_keywords:
            if keyword in self.text:
                start = self.text.find(keyword)
                # 提取关键字后的内容直到句号
                end = self.text.find('。', start)
                if end == -1:
                    end = self.text.find('.', start)
                if end != -1:
                    concept = self.text[start:end+1]
                    return concept
        
        # 如果没有总结句，使用第一段或前几句话
        if self.lines:
            first_line = self.lines[0]
            if len(first_line) > 100:
                # 取前100个字符加省略号
                return first_line[:100] + '...'
            return first_line
        
        return "内容概要"
    
    def extract_tags(self) -> List[str]:
        """提取可能的英文标签"""
        tags = []
        
        # 常见的英文标签映射
        tag_mapping = {
            # 科技相关
            'AI': ['人工智能', 'AI', '大模型'],
            'TECH': ['技术', '科技', '创新'],
            'DATA': ['数据', '分析', '统计'],
            'CLOUD': ['云', '云计算', '云端'],
            'SECURITY': ['安全', '防护', '加密'],
            
            # 商业相关
            'MARKET': ['市场', '商业', '行业'],
            'GROWTH': ['增长', '发展', '提升'],
            'INVESTMENT': ['投资', '融资', '资金'],
            'STRATEGY': ['战略', '策略', '规划'],
            'REVENUE': ['收入', '营收', '利润'],
            
            # 产品相关
            'FEATURE': ['功能', '特性', '特点'],
            'PERFORMANCE': ['性能', '表现', '效率'],
            'SPECS': ['规格', '参数', '配置'],
            'BENCHMARK': ['基准', '测试', '对比'],
            'UPDATE': ['更新', '升级', '版本'],
        }
        
        for eng_tag, chinese_keywords in tag_mapping.items():
            for keyword in chinese_keywords:
                if keyword in self.text:
                    tags.append(eng_tag)
                    break
        
        # 如果标签太少，添加一些通用标签
        if len(tags) < 3:
            default_tags = ['INSIGHTS', 'ANALYSIS', 'REPORT']
            tags.extend(default_tags[:3-len(tags)])
        
        return list(set(tags))[:5]  # 去重并最多返回5个
    
    def get_context(self, start: int, end: int, context_chars: int = 50) -> str:
        """获取数字的上下文"""
        text_len = len(self.text)
        context_start = max(0, start - context_chars)
        context_end = min(text_len, end + context_chars)
        
        context = self.text[context_start:context_end]
        if context_start > 0:
            context = '...' + context
        if context_end < text_len:
            context = context + '...'
        
        return context
    
    def evaluate_number_importance(self, value: str, num_type: str, context: str) -> float:
        """评估数字的重要性（0-1）"""
        importance = 0.0
        
        # 数字类型权重
        type_weights = {
            'percent': 0.8,
            'growth': 0.9,
            'times': 0.7,
            'number_with_unit': 0.6,
            'number': 0.4
        }
        
        # 数字大小权重（大数字更重要）
        try:
            num_value = float(value)
            if num_type == 'percent' or num_type == 'growth':
                # 百分比：靠近100或变化大的更重要
                size_weight = min(abs(num_value - 50) / 50, 1.0)
            else:
                # 普通数字：对数缩放
                size_weight = min(math.log10(max(num_value, 1)) / 3, 1.0)
        except:
            size_weight = 0.5
        
        # 上下文关键词权重
        context_keywords = {
            '核心': 0.3,
            '关键': 0.3,
            '重要': 0.2,
            '主要': 0.2,
            '最高': 0.2,
            '最大': 0.2,
            '提升': 0.2,
            '增长': 0.2
        }
        
        context_weight = 0.0
        for keyword, weight in context_keywords.items():
            if keyword in context:
                context_weight += weight
        context_weight = min(context_weight, 0.5)
        
        # 综合重要性
        type_weight = type_weights.get(num_type, 0.5)
        importance = (type_weight * 0.4) + (size_weight * 0.4) + (context_weight * 0.2)
        
        return importance
    
    def parse_all(self) -> Dict[str, Any]:
        """解析所有内容"""
        return {
            'title': self.extract_title(),
            'concept': self.extract_concept(),
            'key_points': self.extract_key_points(),
            'numbers': self.extract_numbers(),
            'tags': self.extract_tags(),
            'source_text_length': len(self.text),
            'key_points_count': len(self.extract_key_points())
        }


def main():
    """命令行入口点"""
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法: python content-parser.py <文本文件路径>")
        print("示例: python content-parser.py input.txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        parser = ContentParser(text)
        result = parser.parse_all()
        
        # 输出JSON格式结果
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except FileNotFoundError:
        print(f"错误: 文件不存在 - {input_file}")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import math  # 在if __name__中导入，避免全局导入时在其他地方缺少math
    main()