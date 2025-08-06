#!/usr/bin/env python3
"""
Dashboard API - Serves metrics data for the MLOps dashboard
"""

import json
import sys
from metrics_collector import get_metrics_collector

def get_dashboard_data():
    """Get all dashboard data for the frontend"""
    try:
        # Get dashboard metrics
        dashboard_metrics = get_metrics_collector().get_dashboard_metrics()
        
        # Get time series data for charts
        time_series_data = get_metrics_collector().get_time_series_data(hours=24)
        
        # Get latest system metrics
        system_metrics = get_metrics_collector().get_latest_system_metrics()
        
        # Compile complete dashboard data
        dashboard_data = {
            'dashboard_metrics': {
                'total_queries': dashboard_metrics.total_queries,
                'successful_queries': dashboard_metrics.successful_queries,
                'failed_queries': dashboard_metrics.failed_queries,
                'avg_latency_ms': round(dashboard_metrics.avg_latency_ms, 1),
                'total_tokens_used': dashboard_metrics.total_tokens_used,
                'active_models': dashboard_metrics.active_models,
                'queries_last_hour': dashboard_metrics.queries_last_hour,
                'queries_last_24h': dashboard_metrics.queries_last_24h,
                'system_health': dashboard_metrics.system_health,
                'current_model_usage': dashboard_metrics.current_model_usage
            },
            'time_series_data': time_series_data,
            'system_metrics': {
                'cpu_percent': round(system_metrics.cpu_percent, 1) if system_metrics else 0,
                'memory_percent': round(system_metrics.memory_percent, 1) if system_metrics else 0,
                'memory_used_gb': round(system_metrics.memory_used_gb, 2) if system_metrics else 0,
                'memory_total_gb': round(system_metrics.memory_total_gb, 2) if system_metrics else 0,
                'disk_usage_percent': round(system_metrics.disk_usage_percent, 1) if system_metrics else 0,
                'gpu_available': system_metrics.gpu_available if system_metrics else False,
                'gpu_memory_percent': round(system_metrics.gpu_memory_percent, 1) if system_metrics and system_metrics.gpu_memory_percent else None
            }
        }
        
        # Output as JSON for IPC
        print(json.dumps(dashboard_data))
        sys.stdout.flush()
        
    except Exception as e:
        error_data = {
            'error': str(e),
            'dashboard_metrics': {
                'total_queries': 0,
                'successful_queries': 0,
                'failed_queries': 0,
                'avg_latency_ms': 0,
                'total_tokens_used': 0,
                'active_models': [],
                'queries_last_hour': 0,
                'queries_last_24h': 0,
                'system_health': 'Unknown',
                'current_model_usage': {}
            },
            'time_series_data': {
                'timestamps': [],
                'queries_per_hour': [],
                'tokens_per_hour': [],
                'avg_latency_per_hour': []
            },
            'system_metrics': {
                'cpu_percent': 0,
                'memory_percent': 0,
                'memory_used_gb': 0,
                'memory_total_gb': 0,
                'disk_usage_percent': 0,
                'gpu_available': False,
                'gpu_memory_percent': None
            }
        }
        print(json.dumps(error_data))
        sys.stdout.flush()

if __name__ == "__main__":
    get_dashboard_data() 