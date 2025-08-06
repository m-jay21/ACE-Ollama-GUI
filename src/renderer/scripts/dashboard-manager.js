class DashboardManager {
  constructor() {
    this.charts = {};
    this.updateInterval = null;
    this.isActive = false;
    this.init();
  }

  init() {
    this.setupEventHandlers();
    this.initializeCharts();
  }

  setupEventHandlers() {
    // Dashboard button click handler will be set up in ui-manager.js
  }

  initializeCharts() {
    // Initialize Chart.js with theme colors
    const accentColor = getComputedStyle(document.documentElement).getPropertyValue('--accent');
    const textColor = getComputedStyle(document.documentElement).getPropertyValue('--text-primary');
    const gridColor = getComputedStyle(document.documentElement).getPropertyValue('--bg-primary');

    // Common chart configuration
    const chartConfig = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: textColor
          }
        }
      },
      scales: {
        x: {
          grid: {
            color: gridColor
          },
          ticks: {
            color: textColor
          }
        },
        y: {
          grid: {
            color: gridColor
          },
          ticks: {
            color: textColor
          }
        }
      }
    };

    // Query Volume Chart
    const queryVolumeCtx = document.getElementById('query-volume-chart');
    if (queryVolumeCtx) {
      this.charts.queryVolume = new Chart(queryVolumeCtx, {
        type: 'line',
        data: {
          labels: [],
          datasets: [{
            label: 'Queries per Hour',
            data: [],
            borderColor: accentColor,
            backgroundColor: accentColor + '20',
            tension: 0.4,
            fill: true
          }]
        },
        options: {
          ...chartConfig,
          plugins: {
            ...chartConfig.plugins,
            title: {
              display: true,
              text: 'Query Volume',
              color: textColor
            }
          }
        }
      });
    }

    // Response Time Chart
    const responseTimeCtx = document.getElementById('response-time-chart');
    if (responseTimeCtx) {
      this.charts.responseTime = new Chart(responseTimeCtx, {
        type: 'line',
        data: {
          labels: [],
          datasets: [{
            label: 'Average Response Time (ms)',
            data: [],
            borderColor: accentColor,
            backgroundColor: accentColor + '20',
            tension: 0.4,
            fill: true
          }]
        },
        options: {
          ...chartConfig,
          plugins: {
            ...chartConfig.plugins,
            title: {
              display: true,
              text: 'Response Time',
              color: textColor
            }
          }
        }
      });
    }
  }

  openDashboard() {
    this.isActive = true;
    this.loadDashboardData();
    this.startRealTimeUpdates();
  }

  closeDashboard() {
    this.isActive = false;
    this.stopRealTimeUpdates();
  }

  async loadDashboardData() {
    try {
      console.log('Loading dashboard data...');
      const data = await window.electronAPI.getDashboardData();
      console.log('Dashboard data received:', data);
      this.updateDashboard(data);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      this.showError('Failed to load dashboard data');
    }
  }

  updateDashboard(data) {
    if (!data) return;

    // Update key metrics cards
    this.updateMetricsCards(data.dashboard_metrics);
    
    // Update system resources
    this.updateSystemResources(data.system_metrics);
    
    // Update charts
    this.updateCharts(data.time_series_data);
    
    // Update recent activity
    this.updateRecentActivity(data.dashboard_metrics);
  }

  updateMetricsCards(metrics) {
    console.log('Updating metrics cards with:', metrics);
    
    // Total Queries
    const totalQueriesEl = document.getElementById('total-queries');
    console.log('Total queries element found:', !!totalQueriesEl);
    if (totalQueriesEl) {
      totalQueriesEl.textContent = metrics.total_queries.toLocaleString();
      console.log('Updated total queries to:', metrics.total_queries);
    }

    // Average Latency
    const avgLatencyEl = document.getElementById('avg-latency');
    console.log('Avg latency element found:', !!avgLatencyEl);
    if (avgLatencyEl) {
      avgLatencyEl.textContent = `${metrics.avg_latency_ms}ms`;
      console.log('Updated avg latency to:', metrics.avg_latency_ms);
    }

    // Active Models
    const activeModelsEl = document.getElementById('active-models');
    console.log('Active models element found:', !!activeModelsEl);
    if (activeModelsEl) {
      activeModelsEl.textContent = metrics.active_models.length;
      console.log('Updated active models to:', metrics.active_models.length);
    }

    // System Health
    const systemHealthEl = document.getElementById('system-health');
    console.log('System health element found:', !!systemHealthEl);
    if (systemHealthEl) {
      systemHealthEl.textContent = metrics.system_health;
      console.log('Updated system health to:', metrics.system_health);
      
      // Color code based on health
      switch (metrics.system_health.toLowerCase()) {
        case 'healthy':
          systemHealthEl.className = 'text-2xl font-bold text-green-500';
          break;
        case 'warning':
          systemHealthEl.className = 'text-2xl font-bold text-yellow-500';
          break;
        case 'critical':
          systemHealthEl.className = 'text-2xl font-bold text-red-500';
          break;
        default:
          systemHealthEl.className = 'text-2xl font-bold text-gray-500';
      }
    }
  }

  updateSystemResources(systemMetrics) {
    // CPU Usage
    const cpuBar = document.getElementById('cpu-bar');
    const cpuPercent = document.getElementById('cpu-percent');
    if (cpuBar && cpuPercent) {
      const cpuValue = systemMetrics.cpu_percent;
      cpuBar.style.width = `${cpuValue}%`;
      cpuPercent.textContent = `${cpuValue}%`;
      
      // Color code based on usage
      if (cpuValue > 80) {
        cpuBar.className = 'bg-red-500 h-2 rounded-full transition-all duration-300';
      } else if (cpuValue > 60) {
        cpuBar.className = 'bg-yellow-500 h-2 rounded-full transition-all duration-300';
      } else {
        cpuBar.className = 'bg-[var(--accent)] h-2 rounded-full transition-all duration-300';
      }
    }

    // Memory Usage
    const memoryBar = document.getElementById('memory-bar');
    const memoryPercent = document.getElementById('memory-percent');
    const memoryDetails = document.getElementById('memory-details');
    if (memoryBar && memoryPercent && memoryDetails) {
      const memoryValue = systemMetrics.memory_percent;
      memoryBar.style.width = `${memoryValue}%`;
      memoryPercent.textContent = `${memoryValue}%`;
      memoryDetails.textContent = `${systemMetrics.memory_used_gb} GB / ${systemMetrics.memory_total_gb} GB`;
      
      // Color code based on usage
      if (memoryValue > 80) {
        memoryBar.className = 'bg-red-500 h-2 rounded-full transition-all duration-300';
      } else if (memoryValue > 60) {
        memoryBar.className = 'bg-yellow-500 h-2 rounded-full transition-all duration-300';
      } else {
        memoryBar.className = 'bg-[var(--accent)] h-2 rounded-full transition-all duration-300';
      }
    }

    // Disk Usage
    const diskBar = document.getElementById('disk-bar');
    const diskPercent = document.getElementById('disk-percent');
    if (diskBar && diskPercent) {
      const diskValue = systemMetrics.disk_usage_percent;
      diskBar.style.width = `${diskValue}%`;
      diskPercent.textContent = `${diskValue}%`;
      
      // Color code based on usage
      if (diskValue > 80) {
        diskBar.className = 'bg-red-500 h-2 rounded-full transition-all duration-300';
      } else if (diskValue > 60) {
        diskBar.className = 'bg-yellow-500 h-2 rounded-full transition-all duration-300';
      } else {
        diskBar.className = 'bg-[var(--accent)] h-2 rounded-full transition-all duration-300';
      }
    }

    // GPU Usage
    const gpuBar = document.getElementById('gpu-bar');
    const gpuPercent = document.getElementById('gpu-percent');
    const gpuStatus = document.getElementById('gpu-status');
    if (gpuBar && gpuPercent && gpuStatus) {
      if (systemMetrics.gpu_available && systemMetrics.gpu_memory_percent !== null) {
        const gpuValue = systemMetrics.gpu_memory_percent;
        gpuBar.style.width = `${gpuValue}%`;
        gpuPercent.textContent = `${gpuValue}%`;
        gpuStatus.textContent = 'Available';
        
        // Color code based on usage
        if (gpuValue > 80) {
          gpuBar.className = 'bg-red-500 h-2 rounded-full transition-all duration-300';
        } else if (gpuValue > 60) {
          gpuBar.className = 'bg-yellow-500 h-2 rounded-full transition-all duration-300';
        } else {
          gpuBar.className = 'bg-[var(--accent)] h-2 rounded-full transition-all duration-300';
        }
      } else {
        gpuBar.style.width = '0%';
        gpuPercent.textContent = 'N/A';
        gpuStatus.textContent = 'Not Available';
        gpuBar.className = 'bg-gray-500 h-2 rounded-full transition-all duration-300';
      }
    }
  }

  updateCharts(timeSeriesData) {
    console.log('Updating charts with time series data:', timeSeriesData);
    
    // Update Query Volume Chart
    if (this.charts.queryVolume && timeSeriesData.timestamps.length > 0) {
      console.log('Updating query volume chart with:', timeSeriesData.queries_per_hour);
      this.charts.queryVolume.data.labels = timeSeriesData.timestamps.map(timestamp => {
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      });
      this.charts.queryVolume.data.datasets[0].data = timeSeriesData.queries_per_hour;
      this.charts.queryVolume.update('none');
    }

    // Update Response Time Chart
    if (this.charts.responseTime && timeSeriesData.timestamps.length > 0) {
      console.log('Updating response time chart with:', timeSeriesData.avg_latency_per_hour);
      this.charts.responseTime.data.labels = timeSeriesData.timestamps.map(timestamp => {
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      });
      this.charts.responseTime.data.datasets[0].data = timeSeriesData.avg_latency_per_hour;
      this.charts.responseTime.update('none');
    }
  }

  updateRecentActivity(metrics) {
    const recentActivityEl = document.getElementById('recent-activity');
    if (!recentActivityEl) return;

    const activityItems = [];

    // Add recent queries info
    if (metrics.queries_last_hour > 0) {
      activityItems.push(`<div class="flex items-center space-x-2 py-1">
        <span class="text-green-500">●</span>
        <span>${metrics.queries_last_hour} queries in the last hour</span>
      </div>`);
    }

    // Add model usage info
    if (metrics.current_model_usage && Object.keys(metrics.current_model_usage).length > 0) {
      Object.entries(metrics.current_model_usage).forEach(([model, count]) => {
        activityItems.push(`<div class="flex items-center space-x-2 py-1">
          <span class="text-blue-500">●</span>
          <span>${model}: ${count} queries</span>
        </div>`);
      });
    }

    // Add system health info
    if (metrics.system_health) {
      const healthColor = metrics.system_health.toLowerCase() === 'healthy' ? 'green' : 
                         metrics.system_health.toLowerCase() === 'warning' ? 'yellow' : 'red';
      activityItems.push(`<div class="flex items-center space-x-2 py-1">
        <span class="text-${healthColor}-500">●</span>
        <span>System: ${metrics.system_health}</span>
      </div>`);
    }

    // Add total tokens info
    if (metrics.total_tokens_used > 0) {
      activityItems.push(`<div class="flex items-center space-x-2 py-1">
        <span class="text-purple-500">●</span>
        <span>${metrics.total_tokens_used.toLocaleString()} total tokens used</span>
      </div>`);
    }

    if (activityItems.length > 0) {
      recentActivityEl.innerHTML = activityItems.join('');
    } else {
      recentActivityEl.innerHTML = '<div class="text-center py-4">No recent activity</div>';
    }
  }

  startRealTimeUpdates() {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
    }
    
    // Update every 5 seconds
    this.updateInterval = setInterval(() => {
      if (this.isActive) {
        this.loadDashboardData();
      }
    }, 5000);
  }

  stopRealTimeUpdates() {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
      this.updateInterval = null;
    }
  }

  showError(message) {
    console.error('Dashboard error:', message);
    // You could add a toast notification here
  }

  destroy() {
    this.stopRealTimeUpdates();
    
    // Destroy charts
    Object.values(this.charts).forEach(chart => {
      if (chart && typeof chart.destroy === 'function') {
        chart.destroy();
      }
    });
    
    this.charts = {};
  }
}

// Export for use in other modules
window.DashboardManager = DashboardManager; 