#!/usr/bin/env python3
"""
深入分析475条数据的质量和实用性
"""
import sqlite3
import json
from collections import Counter

def analyze_data_quality():
    """分析475条数据的质量"""
    conn = sqlite3.connect('metra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取成功任务的ID
    cursor.execute("""
        SELECT id FROM data_collection_tasks 
        WHERE job_id = 'task_1752609368_39ef54ee'
    """)
    task_id = cursor.fetchone()['id']
    
    print("📊 475条数据质量深度分析")
    print("=" * 80)
    
    # 获取所有数据
    cursor.execute("""
        SELECT input_text, output_text, confidence
        FROM collected_data_samples 
        WHERE task_id = ?
    """, (task_id,))
    
    all_data = cursor.fetchall()
    
    # 统计分析
    total = len(all_data)
    input_lengths = []
    output_lengths = []
    combined_lengths = []
    
    # 内容分类
    too_short = []  # 太短的
    metadata_only = []  # 只有元数据
    incomplete = []  # 不完整的
    potentially_useful = []  # 可能有用的
    
    for data in all_data:
        input_len = len(data['input_text'] or '')
        output_len = len(data['output_text'] or '')
        combined_len = input_len + output_len
        
        input_lengths.append(input_len)
        output_lengths.append(output_len)
        combined_lengths.append(combined_len)
        
        # 分类数据
        if combined_len < 20:  # 总长度小于20字符
            too_short.append(data)
        elif "视频" in data['output_text'] or "网站" in data['output_text'] or ".com" in data['output_text']:
            metadata_only.append(data)
        elif input_len < 5 or output_len < 5:  # 输入或输出太短
            incomplete.append(data)
        else:
            potentially_useful.append(data)
    
    # 打印统计
    print(f"\n📈 长度统计:")
    print(f"   输入平均长度: {sum(input_lengths)/len(input_lengths):.1f} 字符")
    print(f"   输出平均长度: {sum(output_lengths)/len(output_lengths):.1f} 字符")
    print(f"   总平均长度: {sum(combined_lengths)/len(combined_lengths):.1f} 字符")
    
    print(f"\n🏷️ 数据分类:")
    print(f"   太短（<20字符）: {len(too_short)} 条 ({len(too_short)/total*100:.1f}%)")
    print(f"   仅元数据（链接/视频）: {len(metadata_only)} 条 ({len(metadata_only)/total*100:.1f}%)")
    print(f"   不完整: {len(incomplete)} 条 ({len(incomplete)/total*100:.1f}%)")
    print(f"   可能有用: {len(potentially_useful)} 条 ({len(potentially_useful)/total*100:.1f}%)")
    
    # 展示各类数据样本
    print(f"\n❌ 太短的数据示例（前5条）:")
    for i, data in enumerate(too_short[:5], 1):
        print(f"   {i}. Input: '{data['input_text']}' | Output: '{data['output_text']}'")
    
    print(f"\n🔗 仅元数据示例（前5条）:")
    for i, data in enumerate(metadata_only[:5], 1):
        print(f"   {i}. Input: '{data['input_text']}' | Output: '{data['output_text']}'")
    
    print(f"\n⚠️ 不完整数据示例（前5条）:")
    for i, data in enumerate(incomplete[:5], 1):
        print(f"   {i}. Input: '{data['input_text']}' | Output: '{data['output_text']}'")
    
    print(f"\n✅ 可能有用的数据示例（前10条）:")
    for i, data in enumerate(potentially_useful[:10], 1):
        print(f"\n   {i}. Input: {data['input_text']}")
        print(f"      Output: {data['output_text']}")
    
    # 检查是否有真正的问答对
    real_qa_pairs = []
    for data in all_data:
        input_text = data['input_text'] or ''
        output_text = data['output_text'] or ''
        
        # 检查是否像问答对
        if ('？' in input_text or '吗' in input_text or '什么' in input_text or 
            '如何' in input_text or '怎么' in input_text):
            if len(output_text) > 20:  # 回答有一定长度
                real_qa_pairs.append(data)
    
    print(f"\n💬 真正的问答对: {len(real_qa_pairs)} 条 ({len(real_qa_pairs)/total*100:.1f}%)")
    if real_qa_pairs:
        print("   示例:")
        for i, data in enumerate(real_qa_pairs[:3], 1):
            print(f"\n   {i}. Q: {data['input_text']}")
            print(f"      A: {data['output_text']}")
    
    # 最终评估
    print("\n" + "="*80)
    print("🎯 最终评估:")
    useful_ratio = len(potentially_useful) / total * 100
    print(f"   可能有用的数据占比: {useful_ratio:.1f}%")
    
    if useful_ratio < 10:
        print("   ❌ 数据质量极差：绝大部分数据无法用于训练")
    elif useful_ratio < 30:
        print("   ⚠️ 数据质量差：大部分数据是碎片信息，训练效果会很差")
    elif useful_ratio < 50:
        print("   🤔 数据质量一般：需要大量清理和筛选")
    else:
        print("   ✅ 数据质量尚可：经过筛选后可以使用")
    
    conn.close()

if __name__ == "__main__":
    analyze_data_quality() 