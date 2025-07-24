#!/usr/bin/env python3
"""
DataBuilder V3 CLI 工具
用于测试和管理数据收集任务
"""

import asyncio
import json
import sys
import time
from typing import Dict, Any
import click

from .pipeline import data_builder_pipeline
from .monitoring import monitoring
from .storage_writer import storage_writer
from .config import config

@click.group()
def cli():
    """DataBuilder V3 命令行工具"""
    pass

@cli.command()
@click.option('--task-file', '-f', type=click.Path(exists=True), help='任务定义JSON文件路径')
@click.option('--task-name', '-n', default='测试任务', help='任务名称')
@click.option('--domain', '-d', default='general', help='任务领域')
@click.option('--task-type', '-t', default='qa', help='任务类型')
@click.option('--language', '-l', default='chinese', help='语言')
@click.option('--target-samples', '-s', default=100, help='目标样本数量')
@click.option('--labels', multiple=True, help='标签关键词')
def start(task_file, task_name, domain, task_type, language, target_samples, labels):
    """启动数据收集任务"""
    
    if task_file:
        # 从文件加载任务定义
        with open(task_file, 'r', encoding='utf-8') as f:
            task_definition = json.load(f)
    else:
        # 从命令行参数构建任务定义
        task_definition = {
            "task": task_name,
            "type": task_type,
            "language": language,
            "domain": domain,
            "description": f"{domain}领域的{task_type}任务",
            "labels": list(labels) if labels else [],
            "data_volume": target_samples
        }
    
    click.echo(f"🚀 启动数据收集任务: {task_definition['task']}")
    click.echo(f"📋 任务配置: {json.dumps(task_definition, ensure_ascii=False, indent=2)}")
    
    async def run_task():
        task_id = await data_builder_pipeline.start_data_collection(
            task_definition, 
            target_samples
        )
        
        click.echo(f"✅ 任务已启动，ID: {task_id}")
        
        # 实时显示进度
        while True:
            progress = data_builder_pipeline.get_task_progress(task_id)
            if not progress:
                break
            
            status = progress['status']
            percentage = progress['progress_percentage']
            current_step = progress['current_step']
            
            click.echo(f"\r🔄 进度: {percentage:.1f}% | 状态: {status} | 步骤: {current_step}", nl=False)
            
            if status in ['completed', 'failed']:
                break
            
            await asyncio.sleep(5)
        
        click.echo("\n")
        
        # 显示最终结果
        final_progress = data_builder_pipeline.get_task_progress(task_id)
        if final_progress:
            if final_progress['status'] == 'completed':
                click.echo(f"✅ 任务完成!")
                click.echo(f"📊 收集样本: {final_progress['samples_collected']}")
                click.echo(f"✅ 验证样本: {final_progress['samples_validated']}")
                click.echo(f"💾 存储样本: {final_progress['samples_stored']}")
                click.echo(f"📈 质量通过率: {final_progress['quality_pass_rate']:.1%}")
                click.echo(f"⏱️ 总耗时: {final_progress['elapsed_time']:.1f}秒")
            else:
                click.echo(f"❌ 任务失败: {final_progress.get('error_message', '未知错误')}")
    
    asyncio.run(run_task())

@cli.command()
@click.option('--task-id', '-i', help='任务ID')
def status(task_id):
    """查看任务状态"""
    
    if task_id:
        # 查看特定任务
        progress = data_builder_pipeline.get_task_progress(task_id)
        if progress:
            click.echo(f"📋 任务状态: {task_id}")
            click.echo(f"状态: {progress['status']}")
            click.echo(f"进度: {progress['progress_percentage']:.1f}%")
            click.echo(f"当前步骤: {progress['current_step']}")
            click.echo(f"收集样本: {progress['samples_collected']}")
            click.echo(f"验证样本: {progress['samples_validated']}")
            click.echo(f"存储样本: {progress['samples_stored']}")
            click.echo(f"质量通过率: {progress['quality_pass_rate']:.1%}")
            click.echo(f"已耗时: {progress['elapsed_time']:.1f}秒")
            if progress['estimated_remaining_time'] > 0:
                click.echo(f"预计剩余: {progress['estimated_remaining_time']:.1f}秒")
            if progress.get('error_message'):
                click.echo(f"错误信息: {progress['error_message']}")
        else:
            click.echo(f"❌ 未找到任务: {task_id}")
    else:
        # 查看所有任务
        all_tasks = data_builder_pipeline.get_all_tasks()
        
        click.echo(f"📊 系统状态")
        click.echo(f"活动任务: {all_tasks['total_active']}")
        click.echo(f"已完成任务: {all_tasks['total_completed']}")
        
        if all_tasks['active_tasks']:
            click.echo("\n🔄 活动任务:")
            for task_id, progress in all_tasks['active_tasks'].items():
                click.echo(f"  {task_id}: {progress['status']} ({progress['progress_percentage']:.1f}%)")
        
        if all_tasks['completed_tasks']:
            click.echo("\n✅ 最近完成任务:")
            for task in all_tasks['completed_tasks'][-5:]:
                status_icon = "✅" if task['status'] == 'completed' else "❌"
                click.echo(f"  {status_icon} {task['task_id']}: {task['samples_stored']}样本 ({task['elapsed_time']:.1f}秒)")

@cli.command()
@click.option('--task-id', '-i', required=True, help='任务ID')
def stop(task_id):
    """停止任务"""
    
    async def stop_task():
        success = await data_builder_pipeline.stop_task(task_id)
        if success:
            click.echo(f"✅ 任务已停止: {task_id}")
        else:
            click.echo(f"❌ 未找到活动任务: {task_id}")
    
    asyncio.run(stop_task())

@cli.command()
def monitor():
    """查看监控状态"""
    
    async def show_monitoring():
        status = monitoring.get_current_status()
        
        click.echo(f"📊 监控状态: {status['status_emoji']} {status['status']}")
        click.echo(f"健康度: {status['health_score']:.1%}")
        
        if 'quality_metrics' in status:
            qm = status['quality_metrics']
            click.echo(f"\n📈 质量指标:")
            click.echo(f"  通过率: {qm['current_pass_rate']:.1%}")
            click.echo(f"  平均分: {qm['average_quality_score']:.2f}")
            click.echo(f"  总样本: {qm['total_samples']}")
            click.echo(f"  失败样本: {qm['failed_samples']}")
        
        if 'performance_metrics' in status:
            pm = status['performance_metrics']
            click.echo(f"\n⚡ 性能指标:")
            click.echo(f"  处理速度: {pm['samples_per_minute']:.1f}/分钟")
            click.echo(f"  当前并发: {pm['current_concurrency']}")
            click.echo(f"  成功率: {pm['success_rate']:.1%}")
            click.echo(f"  响应时间: {pm['avg_response_time']:.1f}秒")
        
        if status.get('recent_alerts'):
            click.echo(f"\n🚨 最近告警:")
            for alert in status['recent_alerts']:
                severity_icon = {"warning": "⚠️", "error": "🚨", "critical": "🆘"}.get(alert['severity'], "⚠️")
                click.echo(f"  {severity_icon} {alert['message']}")
    
    asyncio.run(show_monitoring())

@cli.command()
def stats():
    """查看存储统计"""
    
    async def show_stats():
        stats = await storage_writer.get_storage_stats()
        
        click.echo(f"💾 存储统计:")
        click.echo(f"总处理: {stats['total_processed']}")
        click.echo(f"成功插入: {stats['total_inserted']}")
        click.echo(f"重复过滤: {stats['total_duplicated']}")
        click.echo(f"失败数量: {stats['total_failed']}")
        click.echo(f"数据库总量: {stats['total_in_database']}")
        click.echo(f"去重缓存: {stats['dedup_cache_size']}")
        click.echo(f"处理速度: {stats['samples_per_minute']:.1f}/分钟")
        
        # 质量分布
        quality_dist = await storage_writer.get_sample_quality_distribution()
        if quality_dist:
            click.echo(f"\n📊 质量分布:")
            click.echo(f"平均分: {quality_dist['average_score']:.2f}")
            click.echo(f"分数范围: {quality_dist['min_score']:.2f} - {quality_dist['max_score']:.2f}")
            
            for range_name, count in quality_dist['score_ranges'].items():
                percentage = count / quality_dist['total_samples'] * 100
                click.echo(f"  {range_name}: {count} ({percentage:.1f}%)")
    
    asyncio.run(show_stats())

@cli.command()
@click.option('--config-file', '-c', type=click.Path(), help='配置文件路径')
def config_show(config_file):
    """显示配置"""
    
    if config_file:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    else:
        config_data = {
            'concurrency': config.concurrency.__dict__,
            'quality': config.quality.__dict__,
            'performance': config.performance.__dict__,
            'monitoring': config.monitoring.__dict__
        }
    
    click.echo("⚙️ 当前配置:")
    click.echo(json.dumps(config_data, ensure_ascii=False, indent=2))

@cli.command()
@click.option('--days', '-d', default=30, help='清理天数')
def cleanup(days):
    """清理旧数据"""
    
    async def cleanup_data():
        # 清理旧样本
        deleted_count = await storage_writer.cleanup_old_samples(days)
        click.echo(f"🗑️ 清理旧样本: {deleted_count}条")
        
        # 清理旧任务
        await data_builder_pipeline.cleanup_old_tasks(100)
        click.echo("🗑️ 清理旧任务记录")
    
    asyncio.run(cleanup_data())

@cli.command()
def test():
    """运行测试任务"""
    
    # 创建测试任务
    test_task = {
        "task": "测试任务",
        "type": "qa",
        "language": "chinese",
        "domain": "general",
        "description": "用于测试的通用问答任务",
        "labels": ["测试", "问答"],
        "data_volume": 10
    }
    
    click.echo("🧪 运行测试任务...")
    
    async def run_test():
        task_id = await data_builder_pipeline.start_data_collection(test_task, 10)
        
        # 等待完成
        while True:
            progress = data_builder_pipeline.get_task_progress(task_id)
            if not progress or progress['status'] in ['completed', 'failed']:
                break
            await asyncio.sleep(2)
        
        final_progress = data_builder_pipeline.get_task_progress(task_id)
        if final_progress and final_progress['status'] == 'completed':
            click.echo("✅ 测试通过!")
            return True
        else:
            click.echo("❌ 测试失败!")
            return False
    
    success = asyncio.run(run_test())
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    cli()