#!/usr/bin/env python3
"""
对比两个数据收集任务的差异
"""
import sqlite3
import json

def compare_tasks():
    """对比两个任务的数据"""
    conn = sqlite3.connect('metra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 两个任务ID
    successful_task = 'task_1752609368_39ef54ee'  # 475条成功的
    failed_task = 'task_1752629176_20f01ee9'      # 1307条失败的（现在是10条）
    
    print("📊 任务对比分析")
    print("=" * 80)
    
    # 获取任务信息
    for task_id, task_label in [(successful_task, "成功任务"), (failed_task, "失败任务")]:
        cursor.execute("""
            SELECT id, job_id, task_name, task_info, status, collected_count, created_at
            FROM data_collection_tasks 
            WHERE job_id = ?
        """, (task_id,))
        
        task = cursor.fetchone()
        if task:
            print(f"\n{task_label}: {task['task_name']}")
            print(f"  Job ID: {task['job_id']}")
            print(f"  状态: {task['status']}")
            print(f"  收集数量: {task['collected_count']}")
            print(f"  创建时间: {task['created_at']}")
            
            # 解析任务信息
            task_info = json.loads(task['task_info'])
            print(f"  任务类型: {task_info.get('type', 'N/A')}")
            print(f"  任务描述: {task_info.get('description', 'N/A')}")
            
            # 获取数据样本
            cursor.execute("""
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN text IS NOT NULL AND text != '' THEN 1 END) as has_text,
                       COUNT(CASE WHEN input_text IS NOT NULL AND input_text != '' THEN 1 END) as has_input,
                       COUNT(CASE WHEN output_text IS NOT NULL AND output_text != '' THEN 1 END) as has_output,
                       AVG(CASE WHEN confidence IS NOT NULL THEN confidence END) as avg_confidence,
                       AVG(LENGTH(COALESCE(text, '') || COALESCE(input_text, '') || COALESCE(output_text, ''))) as avg_length
                FROM collected_data_samples 
                WHERE task_id = ?
            """, (task['id'],))
            
            stats = cursor.fetchone()
            print(f"\n  数据统计:")
            print(f"    总数据条数: {stats['total']}")
            print(f"    有text字段: {stats['has_text']}")
            print(f"    有input_text字段: {stats['has_input']}")
            print(f"    有output_text字段: {stats['has_output']}")
            print(f"    平均置信度: {stats['avg_confidence']:.3f}" if stats['avg_confidence'] else "    平均置信度: N/A")
            print(f"    平均文本长度: {stats['avg_length']:.1f}" if stats['avg_length'] else "    平均文本长度: 0")
            
            # 查看前3条数据样本
            cursor.execute("""
                SELECT text, input_text, output_text, confidence
                FROM collected_data_samples 
                WHERE task_id = ?
                LIMIT 3
            """, (task['id'],))
            
            samples = cursor.fetchall()
            print(f"\n  数据样本（前3条）:")
            for i, sample in enumerate(samples, 1):
                print(f"\n    样本 {i}:")
                if sample['text']:
                    print(f"      Text: {sample['text'][:100]}...")
                if sample['input_text']:
                    print(f"      Input: {sample['input_text'][:100]}...")
                if sample['output_text']:
                    print(f"      Output: {sample['output_text'][:100]}...")
                print(f"      置信度: {sample['confidence']}")
    
    conn.close()

if __name__ == "__main__":
    compare_tasks() 