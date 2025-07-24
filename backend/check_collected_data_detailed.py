#!/usr/bin/env python3
"""
详细检查收集的数据，包括所有字段
"""
import sqlite3
import json
from datetime import datetime

def analyze_collected_data_detailed():
    """详细分析收集的数据"""
    conn = sqlite3.connect('metra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 查找任务ID为 task_1752629176_20f01ee9 的任务
    task_id = 'task_1752629176_20f01ee9'
    
    # 先查找对应的数据收集任务
    cursor.execute("""
        SELECT * FROM data_collection_tasks 
        WHERE job_id = ?
    """, (task_id,))
    
    task = cursor.fetchone()
    if task:
        print(f"📋 Found task: {task['task_name']}")
        print(f"   Status: {task['status']}")
        print(f"   Collected: {task['collected_count']} items")
        print(f"   Task ID in DB: {task['id']}")
        print(f"   Task Info: {task['task_info']}")
        print()
        
        # 查询前10条数据样本的所有字段
        cursor.execute("""
            SELECT * FROM collected_data_samples 
            WHERE task_id = ?
            LIMIT 10
        """, (task['id'],))
        
        samples = cursor.fetchall()
        print(f"📊 Showing first {len(samples)} samples with ALL fields:")
        print("-" * 100)
        
        for i, sample in enumerate(samples, 1):
            print(f"\n{i}. Sample ID: {sample['id']}")
            print(f"   text: '{sample['text']}'")
            print(f"   label: {sample['label']}")
            print(f"   input_text: {sample['input_text']}")
            print(f"   output_text: {sample['output_text']}")
            print(f"   source: {sample['source']}")
            print(f"   source_type: {sample['source_type']}")
            print(f"   confidence: {sample['confidence']}")
            print(f"   created_at: {sample['created_at']}")
            
            # 解析meta_data
            if sample['meta_data']:
                try:
                    meta = json.loads(sample['meta_data'])
                    print(f"   meta_data: {json.dumps(meta, indent=4, ensure_ascii=False)}")
                except:
                    print(f"   meta_data (raw): {sample['meta_data']}")
        
        # 检查各字段的填充情况
        print("\n📊 Field Analysis:")
        
        # 检查text字段
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN text IS NOT NULL AND LENGTH(text) > 0 THEN 1 ELSE 0 END) as non_empty_text,
                SUM(CASE WHEN input_text IS NOT NULL AND LENGTH(input_text) > 0 THEN 1 ELSE 0 END) as non_empty_input,
                SUM(CASE WHEN output_text IS NOT NULL AND LENGTH(output_text) > 0 THEN 1 ELSE 0 END) as non_empty_output,
                SUM(CASE WHEN label IS NOT NULL AND LENGTH(label) > 0 THEN 1 ELSE 0 END) as non_empty_label
            FROM collected_data_samples 
            WHERE task_id = ?
        """, (task['id'],))
        
        field_stats = cursor.fetchone()
        print(f"   Total samples: {field_stats['total']}")
        print(f"   Non-empty 'text': {field_stats['non_empty_text']}")
        print(f"   Non-empty 'input_text': {field_stats['non_empty_input']}")
        print(f"   Non-empty 'output_text': {field_stats['non_empty_output']}")
        print(f"   Non-empty 'label': {field_stats['non_empty_label']}")
        
        # 查看input_text和output_text的长度
        cursor.execute("""
            SELECT 
                MIN(LENGTH(input_text)) as min_input_len,
                MAX(LENGTH(input_text)) as max_input_len,
                AVG(LENGTH(input_text)) as avg_input_len,
                MIN(LENGTH(output_text)) as min_output_len,
                MAX(LENGTH(output_text)) as max_output_len,
                AVG(LENGTH(output_text)) as avg_output_len
            FROM collected_data_samples 
            WHERE task_id = ? AND input_text IS NOT NULL AND output_text IS NOT NULL
        """, (task['id'],))
        
        length_stats = cursor.fetchone()
        if length_stats['avg_input_len']:
            print(f"\n📏 Length Statistics for non-null fields:")
            print(f"   Input text: min={length_stats['min_input_len']}, max={length_stats['max_input_len']}, avg={length_stats['avg_input_len']:.2f}")
            print(f"   Output text: min={length_stats['min_output_len']}, max={length_stats['max_output_len']}, avg={length_stats['avg_output_len']:.2f}")
                
    else:
        print(f"❌ Task {task_id} not found in database")
    
    conn.close()

if __name__ == "__main__":
    analyze_collected_data_detailed() 