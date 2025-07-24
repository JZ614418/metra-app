"""
Production-Grade Monitoring Service
生产级监控服务 - 真实指标收集、分析和告警
"""
import asyncio
import logging
import psutil
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict
import statistics

from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import httpx

from app.db.session import get_db
from app.models.monitoring import (
    APICallLog, DeploymentMetrics, UsageStatistics, 
    SystemMetrics, AlertEvent, ModelPerformanceMetrics
)
from app.core.config import settings

logger = logging.getLogger(__name__)

class MonitoringService:
    """生产级监控服务"""
    
    def __init__(self):
        self.running = False
        self.monitoring_task = None
        self.metrics_cache = {}
        self.alert_cooldowns = {}  # 防止告警风暴
        
    async def start_monitoring(self):
        """启动监控系统"""
        if self.running:
            logger.warning("监控系统已在运行")
            return
            
        self.running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("🚀 生产级监控系统已启动")
    
    async def stop_monitoring(self):
        """停止监控系统"""
        self.running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("⏹️ 监控系统已停止")
    
    async def log_api_call(self, 
                          deployment_id: str,
                          user_id: str,
                          method: str,
                          endpoint: str,
                          status_code: int,
                          response_time_ms: float,
                          request_size: int = 0,
                          response_size: int = 0,
                          ip_address: str = None,
                          user_agent: str = None,
                          error_message: str = None) -> None:
        """记录API调用日志"""
        
        with next(get_db()) as db:
            try:
                log_entry = APICallLog(
                    deployment_id=deployment_id,
                    user_id=user_id,
                    method=method,
                    endpoint=endpoint,
                    status_code=status_code,
                    response_time_ms=response_time_ms,
                    request_size=request_size,
                    response_size=response_size,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    error_message=error_message,
                    timestamp=datetime.utcnow()
                )
                
                db.add(log_entry)
                db.commit()
                
                # 实时更新部署指标缓存
                await self._update_realtime_metrics(deployment_id, status_code, response_time_ms)
                
            except Exception as e:
                logger.error(f"记录API调用失败: {e}")
                db.rollback()
    
    async def _update_realtime_metrics(self, deployment_id: str, status_code: int, response_time_ms: float):
        """实时更新部署指标"""
        if deployment_id not in self.metrics_cache:
            self.metrics_cache[deployment_id] = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'response_times': [],
                'last_updated': datetime.utcnow()
            }
        
        cache = self.metrics_cache[deployment_id]
        cache['total_requests'] += 1
        
        if 200 <= status_code < 300:
            cache['successful_requests'] += 1
        else:
            cache['failed_requests'] += 1
            
        cache['response_times'].append(response_time_ms)
        
        # 保持最近1000个响应时间样本
        if len(cache['response_times']) > 1000:
            cache['response_times'] = cache['response_times'][-1000:]
            
        cache['last_updated'] = datetime.utcnow()
    
    async def get_deployment_realtime_metrics(self, deployment_id: str) -> Dict[str, Any]:
        """获取部署的实时指标"""
        cache = self.metrics_cache.get(deployment_id)
        if not cache:
            return {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'avg_response_time': 0.0,
                'success_rate': 100.0,
                'last_updated': None
            }
        
        response_times = cache['response_times']
        return {
            'total_requests': cache['total_requests'],
            'successful_requests': cache['successful_requests'],
            'failed_requests': cache['failed_requests'],
            'avg_response_time': statistics.mean(response_times) if response_times else 0.0,
            'p95_response_time': statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else 0.0,
            'p99_response_time': statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else 0.0,
            'success_rate': (cache['successful_requests'] / cache['total_requests'] * 100) if cache['total_requests'] > 0 else 100.0,
            'last_updated': cache['last_updated']
        }
    
    async def _monitoring_loop(self):
        """主监控循环"""
        while self.running:
            try:
                # 收集系统指标
                await self._collect_system_metrics()
                
                # 聚合API调用指标
                await self._aggregate_api_metrics()
                
                # 检查告警条件
                await self._check_alerts()
                
                # 清理过期数据
                await self._cleanup_old_data()
                
                # 等待下一次检查（每分钟）
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                await asyncio.sleep(60)
    
    async def _collect_system_metrics(self):
        """收集系统性能指标"""
        try:
            # 获取系统性能数据
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 检查外部服务状态
            openai_status, openai_time = await self._check_service_health("https://api.openai.com/v1/models")
            replicate_status, replicate_time = await self._check_service_health("https://api.replicate.com/v1/models")
            
            # 获取数据库连接数
            db_connections = await self._get_db_connection_count()
            
            # 计算活跃用户和部署数
            active_users, active_deployments, active_trainings = await self._get_active_counts()
            
            with next(get_db()) as db:
                metrics = SystemMetrics(
                    timestamp=datetime.utcnow(),
                    cpu_usage_percent=cpu_percent,
                    memory_usage_percent=memory.percent,
                    disk_usage_percent=disk.percent,
                    services_status={
                        "api": "healthy",
                        "database": "healthy" if db_connections < 100 else "degraded",
                        "openai": openai_status,
                        "replicate": replicate_status
                    },
                    db_connection_count=db_connections,
                    openai_api_status=openai_status,
                    replicate_api_status=replicate_status,
                    openai_response_time=openai_time,
                    replicate_response_time=replicate_time,
                    active_users_count=active_users,
                    active_deployments_count=active_deployments,
                    active_training_jobs=active_trainings
                )
                
                db.add(metrics)
                db.commit()
                
        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
    
    async def _check_service_health(self, url: str) -> tuple[str, float]:
        """检查外部服务健康状态"""
        try:
            start_time = datetime.utcnow()
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                if response.status_code == 200:
                    return "healthy", response_time
                else:
                    return "degraded", response_time
                    
        except Exception:
            return "down", 0.0
    
    async def _get_db_connection_count(self) -> int:
        """获取数据库连接数"""
        try:
            with next(get_db()) as db:
                result = db.execute("SELECT count(*) FROM pg_stat_activity").scalar()
                return result or 0
        except Exception:
            return 0
    
    async def _get_active_counts(self) -> tuple[int, int, int]:
        """获取活跃用户、部署和训练任务数量"""
        try:
            with next(get_db()) as db:
                # 最近24小时活跃用户数
                yesterday = datetime.utcnow() - timedelta(days=1)
                active_users = db.query(func.count(func.distinct(APICallLog.user_id))).filter(
                    APICallLog.timestamp >= yesterday
                ).scalar() or 0
                
                # 活跃部署数 (从deployment service获取)
                from app.services.deployment_service import DeploymentService
                deployment_service = DeploymentService()
                all_deployments = []
                # 这里需要遍历所有用户，在实际应用中应该从数据库获取
                active_deployments = sum(1 for d in all_deployments if d.get('status') == 'active')
                
                # 活跃训练任务数
                from app.services.training_service import training_service
                active_trainings = sum(1 for job in training_service.training_jobs.values() 
                                     if job.get('status') in ['preparing', 'training'])
                
                return active_users, active_deployments, active_trainings
                
        except Exception as e:
            logger.error(f"获取活跃计数失败: {e}")
            return 0, 0, 0
    
    async def _aggregate_api_metrics(self):
        """聚合API调用指标到小时/天/月维度"""
        try:
            with next(get_db()) as db:
                now = datetime.utcnow()
                
                # 聚合过去1小时的数据
                hour_start = now.replace(minute=0, second=0, microsecond=0)
                await self._aggregate_metrics_for_period(db, hour_start, 'hour')
                
                # 每天00:00聚合前一天的数据
                if now.hour == 0 and now.minute < 5:
                    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
                    await self._aggregate_metrics_for_period(db, day_start, 'day')
                
        except Exception as e:
            logger.error(f"聚合API指标失败: {e}")
    
    async def _aggregate_metrics_for_period(self, db: Session, period_start: datetime, window_type: str):
        """为特定时间窗口聚合指标"""
        if window_type == 'hour':
            period_end = period_start + timedelta(hours=1)
        elif window_type == 'day':
            period_end = period_start + timedelta(days=1)
        else:
            return
        
        # 按部署ID分组聚合
        deployments = db.query(func.distinct(APICallLog.deployment_id)).filter(
            APICallLog.timestamp >= period_start,
            APICallLog.timestamp < period_end
        ).all()
        
        for (deployment_id,) in deployments:
            # 聚合该部署在该时间窗口内的指标
            logs = db.query(APICallLog).filter(
                APICallLog.deployment_id == deployment_id,
                APICallLog.timestamp >= period_start,
                APICallLog.timestamp < period_end
            ).all()
            
            if not logs:
                continue
            
            # 计算聚合指标
            total_requests = len(logs)
            successful_requests = sum(1 for log in logs if 200 <= log.status_code < 300)
            failed_requests = total_requests - successful_requests
            
            response_times = [log.response_time_ms for log in logs if log.response_time_ms]
            avg_response_time = statistics.mean(response_times) if response_times else 0.0
            min_response_time = min(response_times) if response_times else 0.0
            max_response_time = max(response_times) if response_times else 0.0
            
            p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else 0.0
            p99_response_time = statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else 0.0
            
            total_bytes_in = sum(log.request_size or 0 for log in logs)
            total_bytes_out = sum(log.response_size or 0 for log in logs)
            
            error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0.0
            
            unique_users = len(set(log.user_id for log in logs if log.user_id))
            unique_ips = len(set(log.ip_address for log in logs if log.ip_address))
            
            # 检查是否已存在记录
            existing = db.query(DeploymentMetrics).filter(
                DeploymentMetrics.deployment_id == deployment_id,
                DeploymentMetrics.date == period_start,
                DeploymentMetrics.window_type == window_type
            ).first()
            
            if existing:
                # 更新现有记录
                existing.total_requests = total_requests
                existing.successful_requests = successful_requests
                existing.failed_requests = failed_requests
                existing.avg_response_time = avg_response_time
                existing.min_response_time = min_response_time
                existing.max_response_time = max_response_time
                existing.p95_response_time = p95_response_time
                existing.p99_response_time = p99_response_time
                existing.total_bytes_in = total_bytes_in
                existing.total_bytes_out = total_bytes_out
                existing.error_rate = error_rate
                existing.unique_users = unique_users
                existing.unique_ips = unique_ips
            else:
                # 创建新记录
                metrics = DeploymentMetrics(
                    deployment_id=deployment_id,
                    date=period_start,
                    window_type=window_type,
                    total_requests=total_requests,
                    successful_requests=successful_requests,
                    failed_requests=failed_requests,
                    avg_response_time=avg_response_time,
                    min_response_time=min_response_time,
                    max_response_time=max_response_time,
                    p95_response_time=p95_response_time,
                    p99_response_time=p99_response_time,
                    total_bytes_in=total_bytes_in,
                    total_bytes_out=total_bytes_out,
                    error_rate=error_rate,
                    unique_users=unique_users,
                    unique_ips=unique_ips
                )
                db.add(metrics)
        
        db.commit()
    
    async def _check_alerts(self):
        """检查告警条件"""
        try:
            # 检查部署错误率告警
            await self._check_error_rate_alerts()
            
            # 检查响应时间告警
            await self._check_response_time_alerts()
            
            # 检查系统资源告警
            await self._check_system_resource_alerts()
            
            # 检查外部服务告警
            await self._check_external_service_alerts()
            
        except Exception as e:
            logger.error(f"检查告警失败: {e}")
    
    async def _check_error_rate_alerts(self):
        """检查部署错误率告警"""
        with next(get_db()) as db:
            # 检查最近15分钟的错误率
            cutoff_time = datetime.utcnow() - timedelta(minutes=15)
            
            # 按部署分组计算错误率
            deployments_with_errors = db.query(
                APICallLog.deployment_id,
                func.count(APICallLog.id).label('total'),
                func.sum(func.case([(func.and_(APICallLog.status_code >= 400), 1)], else_=0)).label('errors')
            ).filter(
                APICallLog.timestamp >= cutoff_time
            ).group_by(APICallLog.deployment_id).all()
            
            for deployment_id, total, errors in deployments_with_errors:
                if total < 10:  # 样本太少，跳过
                    continue
                    
                error_rate = (errors / total) * 100
                
                # 错误率超过20%触发告警
                if error_rate > 20:
                    await self._create_alert(
                        alert_type="high_error_rate",
                        severity="critical" if error_rate > 50 else "warning",
                        title=f"部署 {deployment_id} 错误率过高",
                        message=f"过去15分钟错误率: {error_rate:.1f}% (阈值: 20%)",
                        resource_type="deployment",
                        resource_id=deployment_id,
                        metric_name="error_rate",
                        metric_value=error_rate,
                        threshold_value=20.0
                    )
    
    async def _check_response_time_alerts(self):
        """检查响应时间告警"""
        # 实时检查缓存中的响应时间
        for deployment_id, cache in self.metrics_cache.items():
            response_times = cache['response_times']
            if len(response_times) < 10:
                continue
            
            # 计算P95响应时间
            p95_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else 0
            
            # P95响应时间超过5秒触发告警
            if p95_time > 5000:  # 5秒 = 5000ms
                await self._create_alert(
                    alert_type="high_response_time",
                    severity="warning",
                    title=f"部署 {deployment_id} 响应时间过慢",
                    message=f"P95响应时间: {p95_time:.0f}ms (阈值: 5000ms)",
                    resource_type="deployment",
                    resource_id=deployment_id,
                    metric_name="p95_response_time",
                    metric_value=p95_time,
                    threshold_value=5000.0
                )
    
    async def _check_system_resource_alerts(self):
        """检查系统资源告警"""
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # CPU使用率超过90%
            if cpu_percent > 90:
                await self._create_alert(
                    alert_type="high_cpu_usage",
                    severity="critical",
                    title="系统CPU使用率过高",
                    message=f"CPU使用率: {cpu_percent:.1f}% (阈值: 90%)",
                    resource_type="system",
                    resource_id="server",
                    metric_name="cpu_usage",
                    metric_value=cpu_percent,
                    threshold_value=90.0
                )
            
            # 内存使用率超过85%
            if memory.percent > 85:
                await self._create_alert(
                    alert_type="high_memory_usage",
                    severity="warning",
                    title="系统内存使用率过高",
                    message=f"内存使用率: {memory.percent:.1f}% (阈值: 85%)",
                    resource_type="system",
                    resource_id="server",
                    metric_name="memory_usage",
                    metric_value=memory.percent,
                    threshold_value=85.0
                )
            
            # 磁盘使用率超过90%
            if disk.percent > 90:
                await self._create_alert(
                    alert_type="high_disk_usage",
                    severity="critical",
                    title="系统磁盘使用率过高",
                    message=f"磁盘使用率: {disk.percent:.1f}% (阈值: 90%)",
                    resource_type="system",
                    resource_id="server",
                    metric_name="disk_usage",
                    metric_value=disk.percent,
                    threshold_value=90.0
                )
                
        except Exception as e:
            logger.error(f"检查系统资源告警失败: {e}")
    
    async def _check_external_service_alerts(self):
        """检查外部服务告警"""
        # 这里可以检查OpenAI和Replicate服务状态
        # 实际实现中会检查最近的服务健康检查结果
        pass
    
    async def _create_alert(self, 
                           alert_type: str,
                           severity: str,
                           title: str,
                           message: str,
                           resource_type: str,
                           resource_id: str,
                           metric_name: str,
                           metric_value: float,
                           threshold_value: float):
        """创建告警"""
        
        # 检查冷却时间，防止告警风暴
        alert_key = f"{alert_type}:{resource_id}"
        cooldown_minutes = 30 if severity == "warning" else 15  # 严重告警冷却时间更短
        
        if alert_key in self.alert_cooldowns:
            last_alert_time = self.alert_cooldowns[alert_key]
            if datetime.utcnow() - last_alert_time < timedelta(minutes=cooldown_minutes):
                return  # 在冷却期内，跳过
        
        with next(get_db()) as db:
            try:
                alert = AlertEvent(
                    alert_type=alert_type,
                    severity=severity,
                    title=title,
                    message=message,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    metric_name=metric_name,
                    metric_value=metric_value,
                    threshold_value=threshold_value,
                    triggered_at=datetime.utcnow()
                )
                
                db.add(alert)
                db.commit()
                
                # 更新冷却时间
                self.alert_cooldowns[alert_key] = datetime.utcnow()
                
                # 发送通知
                await self._send_alert_notification(alert)
                
                logger.warning(f"告警触发: {title}")
                
            except Exception as e:
                logger.error(f"创建告警失败: {e}")
                db.rollback()
    
    async def _send_alert_notification(self, alert: AlertEvent):
        """发送告警通知"""
        try:
            # 这里可以集成Slack、邮件等通知方式
            # 目前只记录日志
            if alert.severity == "critical":
                logger.critical(f"🚨 严重告警: {alert.title} - {alert.message}")
            elif alert.severity == "warning":
                logger.warning(f"⚠️ 警告: {alert.title} - {alert.message}")
            else:
                logger.info(f"ℹ️ 信息: {alert.title} - {alert.message}")
                
        except Exception as e:
            logger.error(f"发送告警通知失败: {e}")
    
    async def _cleanup_old_data(self):
        """清理过期数据"""
        try:
            with next(get_db()) as db:
                # 清理30天前的API调用日志
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                db.query(APICallLog).filter(APICallLog.timestamp < cutoff_date).delete()
                
                # 清理90天前的系统指标
                cutoff_date = datetime.utcnow() - timedelta(days=90)
                db.query(SystemMetrics).filter(SystemMetrics.timestamp < cutoff_date).delete()
                
                # 清理已解决的告警（保留30天）
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                db.query(AlertEvent).filter(
                    AlertEvent.status == 'resolved',
                    AlertEvent.resolved_at < cutoff_date
                ).delete()
                
                db.commit()
                
        except Exception as e:
            logger.error(f"清理过期数据失败: {e}")
    
    async def get_deployment_analytics(self, deployment_id: str, period: str = "7d") -> Dict[str, Any]:
        """获取部署的详细分析数据"""
        with next(get_db()) as db:
            # 计算时间范围
            if period == "1h":
                start_time = datetime.utcnow() - timedelta(hours=1)
                window_type = "hour"
            elif period == "24h":
                start_time = datetime.utcnow() - timedelta(days=1)
                window_type = "hour"
            elif period == "7d":
                start_time = datetime.utcnow() - timedelta(days=7)
                window_type = "day"
            elif period == "30d":
                start_time = datetime.utcnow() - timedelta(days=30)
                window_type = "day"
            else:
                start_time = datetime.utcnow() - timedelta(days=7)
                window_type = "day"
            
            # 获取聚合指标
            metrics = db.query(DeploymentMetrics).filter(
                DeploymentMetrics.deployment_id == deployment_id,
                DeploymentMetrics.date >= start_time,
                DeploymentMetrics.window_type == window_type
            ).order_by(DeploymentMetrics.date).all()
            
            # 计算总计和趋势
            total_requests = sum(m.total_requests for m in metrics)
            total_successful = sum(m.successful_requests for m in metrics)
            total_failed = sum(m.failed_requests for m in metrics)
            
            avg_response_time = statistics.mean([m.avg_response_time for m in metrics]) if metrics else 0.0
            avg_error_rate = (total_failed / total_requests * 100) if total_requests > 0 else 0.0
            
            return {
                "period": period,
                "summary": {
                    "total_requests": total_requests,
                    "successful_requests": total_successful,
                    "failed_requests": total_failed,
                    "success_rate": (total_successful / total_requests * 100) if total_requests > 0 else 100.0,
                    "avg_response_time": avg_response_time,
                    "avg_error_rate": avg_error_rate
                },
                "time_series": [
                    {
                        "timestamp": m.date.isoformat(),
                        "requests": m.total_requests,
                        "success_rate": (m.successful_requests / m.total_requests * 100) if m.total_requests > 0 else 100.0,
                        "avg_response_time": m.avg_response_time,
                        "error_rate": m.error_rate
                    }
                    for m in metrics
                ],
                "realtime": await self.get_deployment_realtime_metrics(deployment_id)
            }

# 全局监控服务实例
monitoring_service = MonitoringService()