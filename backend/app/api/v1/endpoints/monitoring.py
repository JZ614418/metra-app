"""
Monitoring API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.models.monitoring import (
    APICallLog, DeploymentMetrics, UsageStatistics, 
    SystemMetrics, AlertEvent, ModelPerformanceMetrics
)
from app.services.monitoring_service import monitoring_service

router = APIRouter()

@router.get("/health")
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "monitoring_active": monitoring_service.running
    }

@router.get("/system/overview")
async def get_system_overview(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """Get system overview"""
    
    # Get latest system metrics
    latest_metrics = db.query(SystemMetrics).order_by(
        SystemMetrics.timestamp.desc()
    ).first()
    
    if not latest_metrics:
        raise HTTPException(status_code=404, detail="System metrics data unavailable")
    
    # Get alert count for past 24 hours
    yesterday = datetime.utcnow() - timedelta(days=1)
    alerts_24h = db.query(AlertEvent).filter(
        AlertEvent.triggered_at >= yesterday
    ).count()
    
    critical_alerts = db.query(AlertEvent).filter(
        AlertEvent.status == "open",
        AlertEvent.severity == "critical"
    ).count()
    
    # Get total API calls for past 24 hours
    api_calls_24h = db.query(APICallLog).filter(
        APICallLog.timestamp >= yesterday
    ).count()
    
    return {
        "system_health": {
            "cpu_usage": latest_metrics.cpu_usage_percent,
            "memory_usage": latest_metrics.memory_usage_percent,
            "disk_usage": latest_metrics.disk_usage_percent,
            "services_status": latest_metrics.services_status,
            "active_users": latest_metrics.active_users_count,
            "active_deployments": latest_metrics.active_deployments_count,
            "active_training_jobs": latest_metrics.active_training_jobs
        },
        "external_services": {
            "openai": {
                "status": latest_metrics.openai_api_status,
                "response_time": latest_metrics.openai_response_time
            },
            "replicate": {
                "status": latest_metrics.replicate_api_status,
                "response_time": latest_metrics.replicate_response_time
            }
        },
        "alerts": {
            "total_24h": alerts_24h,
            "critical_open": critical_alerts
        },
        "api_usage": {
            "calls_24h": api_calls_24h
        },
        "timestamp": latest_metrics.timestamp.isoformat()
    }

@router.get("/deployments/{deployment_id}/metrics")
async def get_deployment_metrics(
    deployment_id: str,
    period: str = Query("7d", regex="^(1h|24h|7d|30d)$"),
    current_user: User = Depends(deps.get_current_user)
):
    """Get detailed metrics for specific deployment"""
    
    try:
        analytics = await monitoring_service.get_deployment_analytics(deployment_id, period)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get deployment metrics: {str(e)}")

@router.get("/deployments/{deployment_id}/realtime")
async def get_deployment_realtime(
    deployment_id: str,
    current_user: User = Depends(deps.get_current_user)
):
    """Get real-time metrics for deployment"""
    
    try:
        realtime_metrics = await monitoring_service.get_deployment_realtime_metrics(deployment_id)
        return realtime_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get realtime metrics: {str(e)}")

@router.get("/deployments/{deployment_id}/logs")
async def get_deployment_logs(
    deployment_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status_code: Optional[int] = Query(None),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """Get API call logs for deployment"""
    
    query = db.query(APICallLog).filter(
        APICallLog.deployment_id == deployment_id
    )
    
    if status_code:
        query = query.filter(APICallLog.status_code == status_code)
    
    logs = query.order_by(
        APICallLog.timestamp.desc()
    ).offset(offset).limit(limit).all()
    
    total = query.count()
    
    return {
        "logs": [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "method": log.method,
                "endpoint": log.endpoint,
                "status_code": log.status_code,
                "response_time_ms": log.response_time_ms,
                "request_size": log.request_size,
                "response_size": log.response_size,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "error_message": log.error_message
            }
            for log in logs
        ],
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
    }

@router.get("/alerts")
async def get_alerts(
    status: Optional[str] = Query(None, regex="^(open|acknowledged|resolved)$"),
    severity: Optional[str] = Query(None, regex="^(critical|warning|info)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """Get alerts list"""
    
    query = db.query(AlertEvent)
    
    if status:
        query = query.filter(AlertEvent.status == status)
    
    if severity:
        query = query.filter(AlertEvent.severity == severity)
    
    alerts = query.order_by(
        AlertEvent.triggered_at.desc()
    ).offset(offset).limit(limit).all()
    
    total = query.count()
    
    return {
        "alerts": [
            {
                "id": alert.id,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "resource_type": alert.resource_type,
                "resource_id": alert.resource_id,
                "metric_name": alert.metric_name,
                "metric_value": alert.metric_value,
                "threshold_value": alert.threshold_value,
                "status": alert.status,
                "triggered_at": alert.triggered_at.isoformat(),
                "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
            }
            for alert in alerts
        ],
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
    }

@router.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """Acknowledge alert"""
    
    alert = db.query(AlertEvent).filter(AlertEvent.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if alert.status != "open":
        raise HTTPException(status_code=400, detail="Can only acknowledge open alerts")
    
    alert.status = "acknowledged"
    alert.acknowledged_by = str(current_user.id)
    alert.acknowledged_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Alert acknowledged"}

@router.put("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """Resolve alert"""
    
    alert = db.query(AlertEvent).filter(AlertEvent.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if alert.status == "resolved":
        raise HTTPException(status_code=400, detail="Alert already resolved")
    
    alert.status = "resolved"
    alert.resolved_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Alert resolved"}

@router.get("/usage/user/{user_id}")
async def get_user_usage(
    user_id: str,
    period: str = Query("30d", regex="^(24h|7d|30d)$"),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """Get user usage statistics"""
    
    # Simple permission check - users can only view their own usage statistics
    if str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="No permission to access other users' usage statistics")
    
    # Calculate time range
    if period == "24h":
        start_date = datetime.utcnow() - timedelta(days=1)
        period_type = "daily"
    elif period == "7d":
        start_date = datetime.utcnow() - timedelta(days=7)
        period_type = "daily"
    elif period == "30d":
        start_date = datetime.utcnow() - timedelta(days=30)
        period_type = "daily"
    else:
        start_date = datetime.utcnow() - timedelta(days=30)
        period_type = "daily"
    
    # Get usage statistics
    usage_stats = db.query(UsageStatistics).filter(
        UsageStatistics.user_id == user_id,
        UsageStatistics.date >= start_date,
        UsageStatistics.period_type == period_type
    ).order_by(UsageStatistics.date).all()
    
    # Calculate summary data
    total_api_calls = sum(stat.api_calls_count for stat in usage_stats)
    total_data_samples = sum(stat.data_collected_samples for stat in usage_stats)
    total_models_trained = sum(stat.models_trained for stat in usage_stats)
    total_cost = sum(stat.total_cost_usd for stat in usage_stats)
    
    return {
        "period": period,
        "summary": {
            "total_api_calls": total_api_calls,
            "total_data_samples": total_data_samples,
            "total_models_trained": total_models_trained,
            "total_cost_usd": total_cost
        },
        "daily_breakdown": [
            {
                "date": stat.date.date().isoformat(),
                "api_calls": stat.api_calls_count,
                "data_samples": stat.data_collected_samples,
                "models_trained": stat.models_trained,
                "cost_usd": stat.total_cost_usd
            }
            for stat in usage_stats
        ]
    }

@router.get("/analytics/overview")
async def get_analytics_overview(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    """Get platform analytics overview"""
    
    # Statistics for past 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # API call statistics
    total_api_calls = db.query(APICallLog).filter(
        APICallLog.timestamp >= thirty_days_ago
    ).count()
    
    successful_calls = db.query(APICallLog).filter(
        APICallLog.timestamp >= thirty_days_ago,
        APICallLog.status_code >= 200,
        APICallLog.status_code < 300
    ).count()
    
    # Model performance statistics
    model_stats = db.query(ModelPerformanceMetrics).filter(
        ModelPerformanceMetrics.created_at >= thirty_days_ago
    ).all()
    
    avg_training_accuracy = sum(m.training_accuracy or 0 for m in model_stats) / len(model_stats) if model_stats else 0
    avg_data_quality = sum(m.data_quality_score or 0 for m in model_stats) / len(model_stats) if model_stats else 0
    
    # User activity
    active_users = db.query(APICallLog.user_id).filter(
        APICallLog.timestamp >= thirty_days_ago
    ).distinct().count()
    
    return {
        "period": "30d",
        "api_usage": {
            "total_calls": total_api_calls,
            "successful_calls": successful_calls,
            "success_rate": (successful_calls / total_api_calls * 100) if total_api_calls > 0 else 100.0
        },
        "model_performance": {
            "models_trained": len(model_stats),
            "avg_training_accuracy": avg_training_accuracy,
            "avg_data_quality": avg_data_quality
        },
        "user_engagement": {
            "active_users": active_users
        }
    }

@router.post("/monitoring/start")
async def start_monitoring(
    current_user: User = Depends(deps.get_current_user)
):
    """Start monitoring system (admin function)"""
    
    # Should check if user is admin here
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="Admin privileges required")
    
    if monitoring_service.running:
        return {"message": "Monitoring system is already running"}
    
    await monitoring_service.start_monitoring()
    return {"message": "Monitoring system started"}

@router.post("/monitoring/stop")
async def stop_monitoring(
    current_user: User = Depends(deps.get_current_user)
):
    """Stop monitoring system (admin function)"""
    
    # Should check if user is admin here
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="Admin privileges required")
    
    if not monitoring_service.running:
        return {"message": "Monitoring system is not running"}
    
    await monitoring_service.stop_monitoring()
    return {"message": "Monitoring system stopped"}