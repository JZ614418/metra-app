"""
EnhancedMonitoring - 双重监控和告警系统
提供质量监控、性能监控和Slack实时告警
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import aiohttp

from app.services.data_builder_v3.config import config

logger = logging.getLogger(__name__)

@dataclass
class QualityMetrics:
    """质量指标"""
    current_pass_rate: float
    average_quality_score: float
    total_samples: int
    failed_samples: int
    trend_direction: str  # "up", "down", "stable"
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class PerformanceMetrics:
    """性能指标"""
    samples_per_minute: float
    current_concurrency: int
    success_rate: float
    avg_response_time: float
    openai_usage: Dict[str, Any]
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class AlertCondition:
    """告警条件"""
    metric_name: str
    threshold: float
    operator: str  # ">=", "<=", "==", "!="
    severity: str  # "warning", "error", "critical"
    message_template: str
    cooldown_minutes: int = 10

class EnhancedMonitoring:
    """增强监控系统"""
    
    def __init__(self):
        self.quality_history: List[QualityMetrics] = []
        self.performance_history: List[PerformanceMetrics] = []
        self.alert_history: List[Dict[str, Any]] = []
        self.last_alert_times: Dict[str, float] = {}
        
        # 告警规则
        self.alert_conditions = [
            AlertCondition(
                metric_name="quality_pass_rate",
                threshold=config.quality.alert_threshold,
                operator="<=",
                severity="warning",
                message_template="⚠️ 质量通过率过低: {value:.1%} (阈值: {threshold:.1%})",
                cooldown_minutes=5
            ),
            AlertCondition(
                metric_name="samples_per_minute",
                threshold=config.performance.min_samples_per_minute,
                operator="<=",
                severity="warning",
                message_template="⚠️ 处理速度过慢: {value:.1f}/分钟 (最低: {threshold:.1f}/分钟)",
                cooldown_minutes=10
            ),
            AlertCondition(
                metric_name="success_rate",
                threshold=0.7,
                operator="<=",
                severity="error",
                message_template="🚨 成功率过低: {value:.1%} (阈值: 70%)",
                cooldown_minutes=5
            ),
            AlertCondition(
                metric_name="avg_response_time",
                threshold=10.0,
                operator=">=",
                severity="warning",
                message_template="⚠️ 平均响应时间过长: {value:.1f}秒 (阈值: 10秒)",
                cooldown_minutes=15
            )
        ]
        
        # 启动监控任务
        self.monitoring_task = None
        self._monitoring_started = False
    
    def start_monitoring(self):
        """启动监控任务"""
        try:
            if self.monitoring_task is None or self.monitoring_task.done():
                try:
                    loop = asyncio.get_running_loop()
                    self.monitoring_task = loop.create_task(self._monitoring_loop())
                    logger.info("📊 监控系统已启动")
                    self._monitoring_started = True
                except RuntimeError:
                    # 没有运行的事件循环，稍后启动
                    logger.debug("监控系统将在事件循环启动后开始")
                    self._monitoring_started = False
        except Exception as e:
            logger.error(f"监控启动失败: {e}")
            self._monitoring_started = False
    
    def stop_monitoring(self):
        """停止监控任务"""
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
            logger.info("📊 监控系统已停止")
    
    async def _monitoring_loop(self):
        """监控循环"""
        while True:
            try:
                # 收集指标
                await self._collect_metrics()
                
                # 检查告警条件
                await self._check_alerts()
                
                # 清理历史数据
                self._cleanup_history()
                
                # 等待下一次检查
                await asyncio.sleep(60)  # 每分钟检查一次
                
            except asyncio.CancelledError:
                logger.info("监控任务被取消")
                break
            except Exception as e:
                logger.error(f"监控任务错误: {str(e)}")
                await asyncio.sleep(60)
    
    async def _collect_metrics(self):
        """收集指标"""
        # 这里需要从各个模块收集指标
        # 为了演示，我们创建模拟数据
        current_time = time.time()
        
        # 质量指标 (实际应用中应该从quality_validator获取)
        quality_metrics = QualityMetrics(
            current_pass_rate=0.75,  # 从实际数据获取
            average_quality_score=0.68,
            total_samples=1000,
            failed_samples=250,
            trend_direction="stable",
            timestamp=current_time
        )
        
        # 性能指标 (实际应用中应该从各模块获取)
        performance_metrics = PerformanceMetrics(
            samples_per_minute=45.0,
            current_concurrency=150,
            success_rate=0.85,
            avg_response_time=5.2,
            openai_usage={"rpm": 2500, "tpm": 35000},
            timestamp=current_time
        )
        
        # 添加到历史记录
        self.quality_history.append(quality_metrics)
        self.performance_history.append(performance_metrics)
        
        logger.debug(f"📊 指标收集完成: 质量通过率 {quality_metrics.current_pass_rate:.1%}, 速度 {performance_metrics.samples_per_minute:.1f}/分钟")
    
    async def _check_alerts(self):
        """检查告警条件"""
        if not self.quality_history or not self.performance_history:
            return
        
        latest_quality = self.quality_history[-1]
        latest_performance = self.performance_history[-1]
        
        # 构建指标字典
        metrics = {
            "quality_pass_rate": latest_quality.current_pass_rate,
            "samples_per_minute": latest_performance.samples_per_minute,
            "success_rate": latest_performance.success_rate,
            "avg_response_time": latest_performance.avg_response_time
        }
        
        # 检查每个告警条件
        for condition in self.alert_conditions:
            if condition.metric_name not in metrics:
                continue
            
            current_value = metrics[condition.metric_name]
            should_alert = False
            
            # 检查阈值
            if condition.operator == "<=":
                should_alert = current_value <= condition.threshold
            elif condition.operator == ">=":
                should_alert = current_value >= condition.threshold
            elif condition.operator == "==":
                should_alert = current_value == condition.threshold
            elif condition.operator == "!=":
                should_alert = current_value != condition.threshold
            
            if should_alert:
                await self._send_alert(condition, current_value)
    
    async def _send_alert(self, condition: AlertCondition, current_value: float):
        """发送告警"""
        # 检查冷却时间
        alert_key = f"{condition.metric_name}_{condition.severity}"
        current_time = time.time()
        
        last_alert_time = self.last_alert_times.get(alert_key, 0)
        cooldown_seconds = condition.cooldown_minutes * 60
        
        if current_time - last_alert_time < cooldown_seconds:
            return  # 还在冷却期内
        
        # 构建告警消息
        message = condition.message_template.format(
            value=current_value,
            threshold=condition.threshold
        )
        
        # 记录告警
        alert_record = {
            "metric_name": condition.metric_name,
            "severity": condition.severity,
            "message": message,
            "value": current_value,
            "threshold": condition.threshold,
            "timestamp": current_time,
            "datetime": datetime.fromtimestamp(current_time).isoformat()
        }
        
        self.alert_history.append(alert_record)
        self.last_alert_times[alert_key] = current_time
        
        # 发送Slack通知
        await self._send_slack_alert(alert_record)
        
        logger.warning(f"🚨 告警触发: {message}")
    
    async def _send_slack_alert(self, alert_record: Dict[str, Any]):
        """发送Slack告警"""
        if not config.monitoring.enable_slack_alerts or not config.monitoring.slack_webhook_url:
            return
        
        # 构建Slack消息
        color = {
            "warning": "#ffaa00",
            "error": "#ff0000",
            "critical": "#990000"
        }.get(alert_record["severity"], "#ffaa00")
        
        slack_message = {
            "attachments": [
                {
                    "color": color,
                    "title": f"DataBuilder V3 告警 - {alert_record['severity'].upper()}",
                    "text": alert_record["message"],
                    "fields": [
                        {
                            "title": "当前值",
                            "value": f"{alert_record['value']:.3f}",
                            "short": True
                        },
                        {
                            "title": "阈值",
                            "value": f"{alert_record['threshold']:.3f}",
                            "short": True
                        },
                        {
                            "title": "时间",
                            "value": alert_record["datetime"],
                            "short": True
                        }
                    ],
                    "footer": "DataBuilder V3 Monitoring",
                    "ts": int(alert_record["timestamp"])
                }
            ]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    config.monitoring.slack_webhook_url,
                    json=slack_message,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        logger.info("✅ Slack告警发送成功")
                    else:
                        logger.error(f"❌ Slack告警发送失败: {response.status}")
        
        except Exception as e:
            logger.error(f"❌ Slack告警发送异常: {str(e)}")
    
    def _cleanup_history(self):
        """清理历史数据"""
        current_time = time.time()
        retention_seconds = config.monitoring.metrics_retention_days * 24 * 60 * 60
        cutoff_time = current_time - retention_seconds
        
        # 清理质量指标历史
        self.quality_history = [
            m for m in self.quality_history 
            if m.timestamp > cutoff_time
        ]
        
        # 清理性能指标历史
        self.performance_history = [
            m for m in self.performance_history 
            if m.timestamp > cutoff_time
        ]
        
        # 清理告警历史
        self.alert_history = [
            a for a in self.alert_history 
            if a["timestamp"] > cutoff_time
        ]
    
    def get_current_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        if not self.quality_history or not self.performance_history:
            return {"status": "initializing", "message": "监控系统正在初始化..."}
        
        latest_quality = self.quality_history[-1]
        latest_performance = self.performance_history[-1]
        
        # 计算总体健康度
        health_score = (
            latest_quality.current_pass_rate * 0.4 +
            latest_performance.success_rate * 0.3 +
            min(latest_performance.samples_per_minute / config.performance.min_samples_per_minute, 1.0) * 0.3
        )
        
        # 确定状态
        if health_score >= 0.8:
            status = "healthy"
            status_emoji = "🟢"
        elif health_score >= 0.6:
            status = "warning"
            status_emoji = "🟡"
        else:
            status = "critical"
            status_emoji = "🔴"
        
        return {
            "status": status,
            "status_emoji": status_emoji,
            "health_score": health_score,
            "quality_metrics": latest_quality.to_dict(),
            "performance_metrics": latest_performance.to_dict(),
            "recent_alerts": self.alert_history[-5:],  # 最近5个告警
            "monitoring_uptime": time.time() - (self.quality_history[0].timestamp if self.quality_history else time.time())
        }
    
    def get_quality_trend(self, hours: int = 24) -> Dict[str, Any]:
        """获取质量趋势"""
        cutoff_time = time.time() - (hours * 3600)
        
        recent_quality = [
            m for m in self.quality_history 
            if m.timestamp > cutoff_time
        ]
        
        if len(recent_quality) < 2:
            return {"trend": "insufficient_data"}
        
        # 计算趋势
        scores = [m.current_pass_rate for m in recent_quality]
        
        if len(scores) >= 10:
            # 使用线性回归计算趋势
            x = list(range(len(scores)))
            y = scores
            
            n = len(scores)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(x[i] ** 2 for i in range(n))
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            
            if slope > 0.001:
                trend = "improving"
            elif slope < -0.001:
                trend = "declining"
            else:
                trend = "stable"
        else:
            # 简单比较
            if scores[-1] > scores[0]:
                trend = "improving"
            elif scores[-1] < scores[0]:
                trend = "declining"
            else:
                trend = "stable"
        
        return {
            "trend": trend,
            "current_score": scores[-1],
            "average_score": sum(scores) / len(scores),
            "min_score": min(scores),
            "max_score": max(scores),
            "data_points": len(scores)
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self.performance_history:
            return {"status": "no_data"}
        
        recent_performance = self.performance_history[-60:]  # 最近60个数据点
        
        speeds = [m.samples_per_minute for m in recent_performance]
        response_times = [m.avg_response_time for m in recent_performance]
        success_rates = [m.success_rate for m in recent_performance]
        
        return {
            "average_speed": sum(speeds) / len(speeds),
            "peak_speed": max(speeds),
            "min_speed": min(speeds),
            "average_response_time": sum(response_times) / len(response_times),
            "average_success_rate": sum(success_rates) / len(success_rates),
            "current_concurrency": recent_performance[-1].current_concurrency,
            "data_points": len(recent_performance)
        }
    
    async def send_daily_report(self):
        """发送每日报告"""
        if not config.monitoring.enable_slack_alerts or not config.monitoring.slack_webhook_url:
            return
        
        # 计算24小时统计
        cutoff_time = time.time() - (24 * 3600)
        
        daily_quality = [m for m in self.quality_history if m.timestamp > cutoff_time]
        daily_performance = [m for m in self.performance_history if m.timestamp > cutoff_time]
        daily_alerts = [a for a in self.alert_history if a["timestamp"] > cutoff_time]
        
        if not daily_quality or not daily_performance:
            return
        
        # 构建报告
        avg_quality = sum(m.current_pass_rate for m in daily_quality) / len(daily_quality)
        avg_speed = sum(m.samples_per_minute for m in daily_performance) / len(daily_performance)
        total_samples = daily_quality[-1].total_samples - daily_quality[0].total_samples
        
        report_message = {
            "text": "📊 DataBuilder V3 每日报告",
            "attachments": [
                {
                    "color": "#36a64f",
                    "fields": [
                        {
                            "title": "平均质量通过率",
                            "value": f"{avg_quality:.1%}",
                            "short": True
                        },
                        {
                            "title": "平均处理速度",
                            "value": f"{avg_speed:.1f}/分钟",
                            "short": True
                        },
                        {
                            "title": "总处理样本",
                            "value": f"{total_samples:,}",
                            "short": True
                        },
                        {
                            "title": "告警次数",
                            "value": f"{len(daily_alerts)}",
                            "short": True
                        }
                    ],
                    "footer": "DataBuilder V3 Daily Report",
                    "ts": int(time.time())
                }
            ]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    config.monitoring.slack_webhook_url,
                    json=report_message,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        logger.info("✅ 每日报告发送成功")
                    else:
                        logger.error(f"❌ 每日报告发送失败: {response.status}")
        
        except Exception as e:
            logger.error(f"❌ 每日报告发送异常: {str(e)}")

# 创建全局实例
monitoring = EnhancedMonitoring()