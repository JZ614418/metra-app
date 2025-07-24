#!/usr/bin/env python3
"""
检查收集的数据内容和长度分布
"""
import sqlite3
import json
from datetime import datetime

def analyze_collected_data():
    """分析收集的数据"""
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
        print()
        
        # 查询收集的数据样本
        cursor.execute("""
            SELECT * FROM collected_data_samples 
            WHERE task_id = ?
            ORDER BY LENGTH(text) DESC
            LIMIT 20
        """, (task['id'],))
        
        samples = cursor.fetchall()
        print(f"📊 Found {len(samples)} samples in database")
        print()
        
        # 分析文本长度分布
        cursor.execute("""
            SELECT 
                COUNT(*) as count,
                MIN(LENGTH(text)) as min_length,
                MAX(LENGTH(text)) as max_length,
                AVG(LENGTH(text)) as avg_length
            FROM collected_data_samples 
            WHERE task_id = ?
        """, (task['id'],))
        
        stats = cursor.fetchone()
        print("📈 Text Length Statistics:")
        print(f"   Total samples: {stats['count']}")
        print(f"   Min length: {stats['min_length']} chars")
        print(f"   Max length: {stats['max_length']} chars")
        print(f"   Avg length: {stats['avg_length']:.2f} chars")
        print()
        
        # 显示前10个最长的样本
        print("🔍 Top 10 longest samples:")
        print("-" * 80)
        
        for i, sample in enumerate(samples[:10], 1):
            text = sample['text']
            label = sample['label']
            source = sample['source']
            confidence = sample['confidence']
            
            print(f"\n{i}. Label: {label}, Source: {source}, Confidence: {confidence}")
            print(f"   Length: {len(text)} chars")
            print(f"   Preview: {text[:200]}...")
            if len(text) > 200:
                print(f"   ...{text[-100:]}")
        
        # 查看长度分布
        print("\n📊 Length Distribution:")
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN LENGTH(text) < 100 THEN '< 100'
                    WHEN LENGTH(text) < 500 THEN '100-500'
                    WHEN LENGTH(text) < 1000 THEN '500-1K'
                    WHEN LENGTH(text) < 5000 THEN '1K-5K'
                    WHEN LENGTH(text) < 10000 THEN '5K-10K'
                    WHEN LENGTH(text) < 50000 THEN '10K-50K'
                    ELSE '> 50K'
                END as length_range,
                COUNT(*) as count
            FROM collected_data_samples 
            WHERE task_id = ?
            GROUP BY length_range
            ORDER BY MIN(LENGTH(text))
        """, (task['id'],))
        
        distribution = cursor.fetchall()
        for row in distribution:
            print(f"   {row['length_range']}: {row['count']} samples")
        
        # 检查是否有空文本
        cursor.execute("""
            SELECT COUNT(*) as empty_count
            FROM collected_data_samples 
            WHERE task_id = ? AND (text IS NULL OR text = '' OR LENGTH(TRIM(text)) = 0)
        """, (task['id'],))
        
        empty = cursor.fetchone()
        if empty['empty_count'] > 0:
            print(f"\n⚠️  Found {empty['empty_count']} empty samples!")
        
        # 检查重复数据
        cursor.execute("""
            SELECT text, COUNT(*) as duplicate_count
            FROM collected_data_samples 
            WHERE task_id = ?
            GROUP BY text
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC
            LIMIT 5
        """, (task['id'],))
        
        duplicates = cursor.fetchall()
        if duplicates:
            print(f"\n⚠️  Found duplicates:")
            for dup in duplicates:
                print(f"   Text appears {dup['duplicate_count']} times: {dup['text'][:100]}...")
                
    else:
        print(f"❌ Task {task_id} not found in database")
        
        # 列出所有任务
        cursor.execute("""
            SELECT job_id, task_name, status, collected_count, created_at
            FROM data_collection_tasks
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        all_tasks = cursor.fetchall()
        if all_tasks:
            print("\n📋 Recent tasks:")
            for task in all_tasks:
                print(f"   - {task['job_id']}: {task['task_name']} ({task['status']}, {task['collected_count']} items)")
    
    conn.close()

if __name__ == "__main__":
    analyze_collected_data() 