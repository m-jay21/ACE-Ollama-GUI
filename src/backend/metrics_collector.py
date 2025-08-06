import time
import json
import os
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import threading
import sys
import pickle

logger = logging.getLogger(__name__)

# Define persistent storage file
METRICS_STORAGE_FILE = os.path.join(os.path.dirname(__file__), 'metrics_data.pkl')

@dataclass
class QueryMetrics:
    """Individual query metrics"""
    timestamp: str
    model_name: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: float
    query_type: str
    file_processed: bool
    success: bool
    error_message: Optional[str] = None

@dataclass
class SystemMetrics:
    """System resource metrics"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_usage_percent: float
    gpu_available: bool
    gpu_memory_percent: Optional[float] = None

@dataclass
class DashboardMetrics:
    """Aggregated dashboard metrics"""
    total_queries: int
    successful_queries: int
    failed_queries: int
    avg_latency_ms: float
    total_tokens_used: int
    active_models: List[str]
    queries_last_hour: int
    queries_last_24h: int
    system_health: str
    current_model_usage: Dict[str, int]

class MetricsCollector:
    """Real-time metrics collection and aggregation for MLOps dashboard"""
    
    def __init__(self, max_history_hours: int = 24):
        self.max_history_hours = max_history_hours
        self.query_history = deque(maxlen=10000)  # Keep last 10k queries
        self.system_history = deque(maxlen=1440)  # Keep last 24 hours of system metrics (1 per minute)
        
        # Real-time counters
        self.total_queries = 0
        self.successful_queries = 0
        self.failed_queries = 0
        self.total_tokens_used = 0
        self.model_usage = defaultdict(int)
        
        # Threading for background system monitoring
        self.monitoring_active = False
        self.monitor_thread = None
        self.lock = threading.Lock()
        
        # Load existing metrics data
        self.load_metrics()
        
        # Start background system monitoring
        self.start_system_monitoring()
        
        # Collect initial system metrics immediately
        try:
            initial_metrics = self.get_system_metrics()
            self.system_history.append(initial_metrics)
            logger.info(f"Initial system metrics collected: CPU={initial_metrics.cpu_percent}%, Memory={initial_metrics.memory_percent}%")
        except Exception as e:
            logger.error(f"Error collecting initial system metrics: {e}")
    
    def record_query(self, query_data: Dict[str, Any]) -> None:
        """Record a query with its metrics"""
        try:
            # Extract query information
            model_name = query_data.get('model_name', 'unknown')
            input_tokens = query_data.get('input_tokens', 0)
            output_tokens = query_data.get('output_tokens', 0)
            total_tokens = query_data.get('total_tokens', 0)
            latency_ms = query_data.get('latency_ms', 0)
            query_type = query_data.get('query_type', 'text')
            file_processed = query_data.get('file_processed', False)
            success = query_data.get('success', True)
            error_message = query_data.get('error_message', None)
            
            # Create query metrics
            query_metrics = QueryMetrics(
                timestamp=datetime.now().isoformat(),
                model_name=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                latency_ms=latency_ms,
                query_type=query_type,
                file_processed=file_processed,
                success=success,
                error_message=error_message
            )
            
            # Update metrics without lock for basic operations
            self.total_queries += 1
            if success:
                self.successful_queries += 1
            else:
                self.failed_queries += 1
            
            self.total_tokens_used += total_tokens
            self.model_usage[model_name] += 1
            
            # Add to history
            self.query_history.append(query_metrics)
            
            # Log the recording
            logger.info(f"Recorded query: {model_name}, {total_tokens} tokens, {latency_ms}ms")
            logger.info(f"Total queries: {self.total_queries}, Total tokens: {self.total_tokens_used}")
            
            # Save metrics data to persistent storage
            try:
                self.save_metrics()
            except Exception as e:
                logger.error(f"Error saving metrics: {e}")
                
        except Exception as e:
            logger.error(f"Error recording query metrics: {e}")
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system resource metrics"""
        try:
            # CPU and Memory - use non-blocking calls
            cpu_percent = psutil.cpu_percent(interval=None)  # Non-blocking
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage_percent = (disk.used / disk.total) * 100
            
            # GPU detection (basic) - with shorter timeout
            gpu_available = False
            gpu_memory_percent = None
            
            try:
                # Try to get GPU info using nvidia-smi with shorter timeout
                import subprocess
                result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits'], 
                                      capture_output=True, text=True, timeout=1)  # Reduced from 5s to 1s
                if result.returncode == 0:
                    gpu_available = True
                    # Parse GPU memory usage
                    lines = result.stdout.strip().split('\n')
                    if lines and lines[0]:
                        used, total = map(int, lines[0].split(', '))
                        gpu_memory_percent = (used / total) * 100 if total > 0 else 0
            except Exception:
                gpu_available = False
            
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_gb=memory_used_gb,
                memory_total_gb=memory_total_gb,
                disk_usage_percent=disk_usage_percent,
                gpu_available=gpu_available,
                gpu_memory_percent=gpu_memory_percent
            )
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=0,
                memory_percent=0,
                memory_used_gb=0,
                memory_total_gb=0,
                disk_usage_percent=0,
                gpu_available=False,
                gpu_memory_percent=None
            )
    
    def start_system_monitoring(self) -> None:
        """Start background system monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._system_monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def _system_monitor_loop(self) -> None:
        """Background loop for system monitoring"""
        while self.monitoring_active:
            try:
                system_metrics = self.get_system_metrics()
                # Add to history without lock to prevent deadlocks
                self.system_history.append(system_metrics)
                
                # Debug logging
                logger.info(f"System metrics collected: CPU={system_metrics.cpu_percent}%, Memory={system_metrics.memory_percent}%")
                
                # Sleep for 30 seconds to be more responsive
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in system monitoring loop: {e}")
                time.sleep(30)
    
    def get_dashboard_metrics(self) -> DashboardMetrics:
        """Get aggregated metrics for dashboard display"""
        try:
            # Calculate time ranges
            now = datetime.now()
            one_hour_ago = now - timedelta(hours=1)
            one_day_ago = now - timedelta(hours=24)
            
            # Filter queries by time
            recent_queries = [
                q for q in self.query_history 
                if datetime.fromisoformat(q.timestamp) >= one_hour_ago
            ]
            
            day_queries = [
                q for q in self.query_history 
                if datetime.fromisoformat(q.timestamp) >= one_day_ago
            ]
            
            # Calculate averages
            if self.query_history:
                avg_latency = sum(q.latency_ms for q in self.query_history) / len(self.query_history)
            else:
                avg_latency = 0
            
            # Get active models (used in last 24 hours)
            active_models = list(set(q.model_name for q in day_queries))
            
            # Determine system health
            system_health = self._determine_system_health()
            
            # Get current model usage (last hour)
            current_model_usage = defaultdict(int)
            for query in recent_queries:
                current_model_usage[query.model_name] += 1
            
            return DashboardMetrics(
                total_queries=self.total_queries,
                successful_queries=self.successful_queries,
                failed_queries=self.failed_queries,
                avg_latency_ms=avg_latency,
                total_tokens_used=self.total_tokens_used,
                active_models=active_models,
                queries_last_hour=len(recent_queries),
                queries_last_24h=len(day_queries),
                system_health=system_health,
                current_model_usage=dict(current_model_usage)
            )
            
        except Exception as e:
            logger.error(f"Error getting dashboard metrics: {e}")
            return DashboardMetrics(
                total_queries=0,
                successful_queries=0,
                failed_queries=0,
                avg_latency_ms=0,
                total_tokens_used=0,
                active_models=[],
                queries_last_hour=0,
                queries_last_24h=0,
                system_health="Unknown",
                current_model_usage={}
            )
    
    def _determine_system_health(self) -> str:
        """Determine overall system health based on metrics"""
        try:
            if not self.system_history:
                return "Unknown"
            
            latest_system = self.system_history[-1]
            
            # Check CPU usage
            if latest_system.cpu_percent > 90:
                return "Critical"
            elif latest_system.cpu_percent > 80:
                return "Warning"
            
            # Check memory usage
            if latest_system.memory_percent > 90:
                return "Critical"
            elif latest_system.memory_percent > 80:
                return "Warning"
            
            # Check disk usage
            if latest_system.disk_usage_percent > 90:
                return "Critical"
            elif latest_system.disk_usage_percent > 80:
                return "Warning"
            
            return "Healthy"
            
        except Exception as e:
            logger.error(f"Error determining system health: {e}")
            return "Unknown"
    
    def get_time_series_data(self, hours: int = 24) -> Dict[str, List]:
        """Get time series data for charts"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Filter queries by time
            recent_queries = [
                q for q in self.query_history 
                if datetime.fromisoformat(q.timestamp) >= cutoff_time
            ]
            
            # Create hourly buckets for the last 24 hours
            hourly_data = {}
            current_time = datetime.now()
            
            # Initialize all hours in the range with zero data
            for i in range(hours):
                hour_time = current_time - timedelta(hours=i)
                hour_key = hour_time.replace(minute=0, second=0, microsecond=0)
                hourly_data[hour_key] = {
                    'queries': 0,
                    'tokens': 0,
                    'latency_sum': 0,
                    'count': 0
                }
            
            # Add actual query data to the appropriate hours
            for query in recent_queries:
                query_time = datetime.fromisoformat(query.timestamp)
                hour_key = query_time.replace(minute=0, second=0, microsecond=0)
                
                if hour_key in hourly_data:
                    hourly_data[hour_key]['queries'] += 1
                    hourly_data[hour_key]['tokens'] += query.total_tokens
                    hourly_data[hour_key]['latency_sum'] += query.latency_ms
                    hourly_data[hour_key]['count'] += 1
            
            # Convert to lists for charting (in chronological order)
            timestamps = []
            queries_per_hour = []
            tokens_per_hour = []
            avg_latency_per_hour = []
            
            for hour in sorted(hourly_data.keys()):
                data = hourly_data[hour]
                timestamps.append(hour.isoformat())
                queries_per_hour.append(data['queries'])
                tokens_per_hour.append(data['tokens'])
                avg_latency_per_hour.append(
                    data['latency_sum'] / data['count'] if data['count'] > 0 else 0
                )
            
            return {
                'timestamps': timestamps,
                'queries_per_hour': queries_per_hour,
                'tokens_per_hour': tokens_per_hour,
                'avg_latency_per_hour': avg_latency_per_hour
            }
            
        except Exception as e:
            logger.error(f"Error getting time series data: {e}")
            return {
                'timestamps': [],
                'queries_per_hour': [],
                'tokens_per_hour': [],
                'avg_latency_per_hour': []
            }
    
    def get_latest_system_metrics(self) -> Optional[SystemMetrics]:
        """Get the most recent system metrics"""
        try:
            if self.system_history:
                return self.system_history[-1]
            return None
        except Exception as e:
            logger.error(f"Error getting latest system metrics: {e}")
            return None
    
    def cleanup_old_data(self) -> None:
        """Clean up old metrics data"""
        try:
            with self.lock:
                cutoff_time = datetime.now() - timedelta(hours=self.max_history_hours)
                
                # Clean up query history
                self.query_history = deque(
                    [q for q in self.query_history 
                     if datetime.fromisoformat(q.timestamp) >= cutoff_time],
                    maxlen=10000
                )
                
                # Clean up system history
                self.system_history = deque(
                    [s for s in self.system_history 
                     if datetime.fromisoformat(s.timestamp) >= cutoff_time],
                    maxlen=1440
                )
                
                logger.info("Cleaned up old metrics data")
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics data"""
        try:
            with self.lock:
                data = {
                    'dashboard_metrics': asdict(self.get_dashboard_metrics()),
                    'query_history': [asdict(q) for q in list(self.query_history)[-1000:]],  # Last 1000 queries
                    'system_history': [asdict(s) for s in list(self.system_history)[-1440:]],  # Last 24 hours
                    'export_timestamp': datetime.now().isoformat()
                }
                
                if format == 'json':
                    return json.dumps(data, indent=2)
                else:
                    raise ValueError(f"Unsupported format: {format}")
                    
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return "{}"

    def save_metrics(self) -> None:
        """Save metrics data to persistent storage"""
        try:
            data = {
                'total_queries': self.total_queries,
                'successful_queries': self.successful_queries,
                'failed_queries': self.failed_queries,
                'total_tokens_used': self.total_tokens_used,
                'model_usage': dict(self.model_usage),
                'query_history': list(self.query_history),
                'system_history': list(self.system_history),
                'last_save': datetime.now().isoformat()
            }
            
            with open(METRICS_STORAGE_FILE, 'wb') as f:
                pickle.dump(data, f)
                
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
    
    def load_metrics(self) -> None:
        """Load metrics data from persistent storage"""
        try:
            if os.path.exists(METRICS_STORAGE_FILE):
                with open(METRICS_STORAGE_FILE, 'rb') as f:
                    data = pickle.load(f)
                
                self.total_queries = data.get('total_queries', 0)
                self.successful_queries = data.get('successful_queries', 0)
                self.failed_queries = data.get('failed_queries', 0)
                self.total_tokens_used = data.get('total_tokens_used', 0)
                self.model_usage = defaultdict(int, data.get('model_usage', {}))
                
                # Load history with proper maxlen
                query_history = data.get('query_history', [])
                self.query_history = deque(query_history, maxlen=10000)
                
                system_history = data.get('system_history', [])
                self.system_history = deque(system_history, maxlen=1440)
                
        except Exception as e:
            logger.error(f"Error loading metrics: {e}")

# Global metrics collector instance (lazy-loaded)
_metrics_collector_instance = None

def get_metrics_collector():
    """Get the global metrics collector instance (lazy-loaded)"""
    global _metrics_collector_instance
    if _metrics_collector_instance is None:
        _metrics_collector_instance = MetricsCollector()
    return _metrics_collector_instance

# For backward compatibility - don't call immediately
def get_metrics_collector_instance():
    return get_metrics_collector()

# Don't initialize immediately - let it be lazy-loaded
metrics_collector = None 