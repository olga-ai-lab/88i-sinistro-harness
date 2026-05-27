"""
Capacity Planning and System Monitoring Module

This module provides system metrics collection and capacity analysis
for production deployment optimization.
"""

import psutil
from typing import Dict, List, Any, Literal, Optional


class CapacityAnalyzer:
    """
    Analyzes system capacity and provides scaling recommendations.
    
    Monitors CPU, memory, and disk usage against configurable thresholds
    to determine system health status and scaling needs.
    """
    
    def __init__(
        self,
        max_concurrent_users: int = 1000,
        thresholds: Optional[Dict[str, int]] = None
    ):
        """
        Initialize the CapacityAnalyzer.
        
        Args:
            max_concurrent_users: Expected maximum concurrent users (default: 1000)
            thresholds: Dictionary with CPU, memory, and disk thresholds as percentages.
                       Expected keys: 'cpu_alert', 'cpu_scale', 'memory_alert', 
                       'memory_scale', 'disk_alert', 'disk_scale'
        """
        self.max_concurrent_users = max_concurrent_users
        
        # Default thresholds (percentages)
        self.thresholds = {
            'cpu_alert': 80,
            'cpu_scale': 90,
            'memory_alert': 80,
            'memory_scale': 90,
            'disk_alert': 80,
            'disk_scale': 90,
        }
        
        # Override with provided thresholds
        if thresholds:
            self.thresholds.update(thresholds)
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Retrieve current system metrics.
        
        Returns:
            Dictionary containing:
                - cpu_percent: CPU usage percentage (0-100)
                - memory_percent: Memory usage percentage (0-100)
                - memory_available_gb: Available memory in GB
                - disk_percent: Disk usage percentage (0-100)
                - disk_free_gb: Free disk space in GB
                - cpu_count: Number of CPU cores
        """
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count(logical=True)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024 ** 3)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free_gb = disk.free / (1024 ** 3)
            
            return {
                'cpu_percent': cpu_percent,
                'cpu_count': cpu_count,
                'memory_percent': memory_percent,
                'memory_available_gb': round(memory_available_gb, 2),
                'disk_percent': disk_percent,
                'disk_free_gb': round(disk_free_gb, 2),
            }
        except Exception as e:
            raise RuntimeError(f"Failed to collect system metrics: {e}")
    
    def get_capacity_status(self) -> Dict[str, Literal["healthy", "warning", "critical"]]:
        """
        Determine capacity status for each resource.
        
        Returns:
            Dictionary with status for cpu, memory, and disk:
                - 'healthy': Below alert threshold
                - 'warning': Between alert and scale threshold
                - 'critical': At or above scale threshold
        """
        metrics = self.get_system_metrics()
        status = {}
        
        # CPU status
        if metrics['cpu_percent'] >= self.thresholds['cpu_scale']:
            status['cpu'] = 'critical'
        elif metrics['cpu_percent'] >= self.thresholds['cpu_alert']:
            status['cpu'] = 'warning'
        else:
            status['cpu'] = 'healthy'
        
        # Memory status
        if metrics['memory_percent'] >= self.thresholds['memory_scale']:
            status['memory'] = 'critical'
        elif metrics['memory_percent'] >= self.thresholds['memory_alert']:
            status['memory'] = 'warning'
        else:
            status['memory'] = 'healthy'
        
        # Disk status
        if metrics['disk_percent'] >= self.thresholds['disk_scale']:
            status['disk'] = 'critical'
        elif metrics['disk_percent'] >= self.thresholds['disk_alert']:
            status['disk'] = 'warning'
        else:
            status['disk'] = 'healthy'
        
        return status
    
    def get_scaling_recommendation(self) -> Dict[str, Any]:
        """
        Generate scaling recommendations based on current metrics and status.
        
        Returns:
            Dictionary containing:
                - current_metrics: Current system metrics
                - status: Current capacity status
                - recommendations: List of scaling recommendations
        """
        metrics = self.get_system_metrics()
        status = self.get_capacity_status()
        recommendations: List[str] = []
        
        # Analyze CPU
        if status['cpu'] == 'critical':
            recommendations.append(
                f"CRITICAL: CPU at {metrics['cpu_percent']:.1f}%. "
                "Immediate vertical scaling (increase CPU cores) or horizontal scaling (add instances) required."
            )
        elif status['cpu'] == 'warning':
            recommendations.append(
                f"WARNING: CPU at {metrics['cpu_percent']:.1f}%. "
                "Monitor closely and prepare to scale horizontally."
            )
        
        # Analyze Memory
        if status['memory'] == 'critical':
            recommendations.append(
                f"CRITICAL: Memory at {metrics['memory_percent']:.1f}%. "
                "Immediate vertical scaling (increase RAM) or optimization required."
            )
        elif status['memory'] == 'warning':
            recommendations.append(
                f"WARNING: Memory at {metrics['memory_percent']:.1f}%. "
                "Monitor closely and consider memory optimization."
            )
        
        # Analyze Disk
        if status['disk'] == 'critical':
            recommendations.append(
                f"CRITICAL: Disk at {metrics['disk_percent']:.1f}%. "
                "Immediate cleanup or storage expansion required."
            )
        elif status['disk'] == 'warning':
            recommendations.append(
                f"WARNING: Disk at {metrics['disk_percent']:.1f}%. "
                "Plan storage expansion soon."
            )
        
        if not recommendations:
            recommendations.append(
                f"System healthy. Current load supports up to {self.max_concurrent_users} concurrent users."
            )
        
        return {
            'current_metrics': metrics,
            'status': status,
            'recommendations': recommendations,
        }
