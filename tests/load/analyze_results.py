"""
Load Test Results Analysis Module

Analyzes load test results to provide latency statistics, throughput metrics,
error analysis, and scaling capacity recommendations.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from statistics import mean, median


class LoadTestAnalyzer:
    """
    Analyzes load test results from JSON format.
    
    Provides comprehensive analysis including latency statistics,
    throughput metrics, error analysis, and scaling recommendations.
    """
    
    def __init__(self, results_file: str):
        """
        Initialize the LoadTestAnalyzer.
        
        Args:
            results_file: Path to the JSON load test results file
        """
        self.results_file = Path(results_file)
        self.results = self._load_results()
    
    def _load_results(self) -> Dict[str, Any]:
        """
        Load and parse JSON results file.
        
        Returns:
            Dictionary containing load test results
            
        Raises:
            FileNotFoundError: If results file does not exist
            json.JSONDecodeError: If results file is not valid JSON
        """
        if not self.results_file.exists():
            raise FileNotFoundError(f"Results file not found: {self.results_file}")
        
        with open(self.results_file, 'r') as f:
            return json.load(f)
    
    def get_latency_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate latency statistics for each endpoint.
        
        Returns:
            Dictionary mapping endpoint names to latency stats:
                - min: Minimum latency in milliseconds
                - max: Maximum latency in milliseconds
                - mean: Mean latency in milliseconds
                - median: Median latency in milliseconds
                - p95: 95th percentile latency in milliseconds
                - p99: 99th percentile latency in milliseconds
        """
        stats_by_endpoint: Dict[str, Dict[str, float]] = {}
        
        # Group requests by endpoint
        endpoints: Dict[str, List[float]] = {}
        
        if 'requests' in self.results:
            for request in self.results['requests']:
                endpoint = request.get('endpoint', 'unknown')
                latency = request.get('latency_ms', 0)
                
                if endpoint not in endpoints:
                    endpoints[endpoint] = []
                endpoints[endpoint].append(latency)
        
        # Calculate statistics for each endpoint
        for endpoint, latencies in endpoints.items():
            if not latencies:
                continue
            
            sorted_latencies = sorted(latencies)
            
            # Calculate percentiles
            def percentile(data: List[float], p: float) -> float:
                index = int(len(data) * p / 100)
                return float(data[min(index, len(data) - 1)])
            
            stats_by_endpoint[endpoint] = {
                'min': float(min(sorted_latencies)),
                'max': float(max(sorted_latencies)),
                'mean': round(mean(sorted_latencies), 2),
                'median': float(median(sorted_latencies)),
                'p95': percentile(sorted_latencies, 95),
                'p99': percentile(sorted_latencies, 99),
            }
        
        return stats_by_endpoint
    
    def get_throughput_stats(self) -> Dict[str, float]:
        """
        Calculate throughput (requests per second) for each endpoint.
        
        Returns:
            Dictionary mapping endpoint names to throughput in requests/second
        """
        throughput_by_endpoint: Dict[str, float] = {}
        
        if 'duration_seconds' not in self.results or 'requests' not in self.results:
            return throughput_by_endpoint
        
        duration = self.results['duration_seconds']
        if duration <= 0:
            return throughput_by_endpoint
        
        # Count requests by endpoint
        endpoint_counts: Dict[str, int] = {}
        for request in self.results['requests']:
            endpoint = request.get('endpoint', 'unknown')
            endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1
        
        # Calculate throughput
        for endpoint, count in endpoint_counts.items():
            throughput_by_endpoint[endpoint] = round(count / duration, 2)
        
        return throughput_by_endpoint
    
    def get_error_analysis(self) -> Dict[str, Any]:
        """
        Analyze errors from load test results.
        
        Returns:
            Dictionary containing:
                - total_requests: Total number of requests
                - errors: Total number of errors
                - error_rate_pct: Error rate as percentage (0-100)
                - error_breakdown: Dictionary of error types and counts
        """
        total_requests = 0
        error_count = 0
        error_breakdown: Dict[str, int] = {}
        
        if 'requests' in self.results:
            for request in self.results['requests']:
                total_requests += 1
                
                if request.get('status_code', 200) >= 400:
                    error_count += 1
                    status_code = request.get('status_code', 'unknown')
                    error_type = f"HTTP {status_code}"
                    error_breakdown[error_type] = error_breakdown.get(error_type, 0) + 1
                
                if 'error' in request and request['error']:
                    error_count += 1
                    error_msg = request['error']
                    error_breakdown[error_msg] = error_breakdown.get(error_msg, 0) + 1
        
        error_rate_pct = (error_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'total_requests': total_requests,
            'errors': error_count,
            'error_rate_pct': round(error_rate_pct, 2),
            'error_breakdown': error_breakdown,
        }
    
    def get_scaling_capacity(self) -> Dict[str, Any]:
        """
        Estimate maximum safe load based on error rate.
        
        Uses the following scaling factors based on observed error rate:
            - <1% error rate: Can safely scale to 0.8x current load
            - <5% error rate: Can safely scale to 0.5x current load
            - >5% error rate: Can only scale to 0.2x current load
        
        Returns:
            Dictionary containing:
                - current_load: Current number of requests
                - error_rate_pct: Current error rate percentage
                - scaling_factor: Recommended scaling factor
                - max_safe_load: Estimated maximum safe load (requests)
        """
        error_analysis = self.get_error_analysis()
        current_load = error_analysis['total_requests']
        error_rate = error_analysis['error_rate_pct']
        
        # Determine scaling factor based on error rate
        if error_rate < 1:
            scaling_factor = 0.8
        elif error_rate < 5:
            scaling_factor = 0.5
        else:
            scaling_factor = 0.2
        
        max_safe_load = int(current_load * scaling_factor)
        
        return {
            'current_load': current_load,
            'error_rate_pct': error_rate,
            'scaling_factor': scaling_factor,
            'max_safe_load': max_safe_load,
        }
    
    def generate_report(self) -> str:
        """
        Generate a comprehensive markdown report of load test analysis.
        
        Returns:
            Markdown formatted report string
        """
        latency_stats = self.get_latency_stats()
        throughput_stats = self.get_throughput_stats()
        error_analysis = self.get_error_analysis()
        scaling_capacity = self.get_scaling_capacity()
        
        report = ["# Load Test Analysis Report", ""]
        
        # Summary Section
        report.append("## Summary")
        report.append(f"- **Total Requests**: {error_analysis['total_requests']}")
        report.append(f"- **Total Errors**: {error_analysis['errors']}")
        report.append(f"- **Error Rate**: {error_analysis['error_rate_pct']}%")
        report.append(f"- **Duration**: {self.results.get('duration_seconds', 'N/A')} seconds")
        report.append("")
        
        # Latency Statistics
        report.append("## Latency Statistics (ms)")
        if latency_stats:
            report.append("")
            report.append("| Endpoint | Min | Max | Mean | Median | P95 | P99 |")
            report.append("|----------|-----|-----|------|--------|-----|-----|")
            for endpoint, stats in latency_stats.items():
                report.append(
                    f"| {endpoint} | {stats['min']:.1f} | {stats['max']:.1f} | "
                    f"{stats['mean']:.1f} | {stats['median']:.1f} | "
                    f"{stats['p95']:.1f} | {stats['p99']:.1f} |"
                )
            report.append("")
        else:
            report.append("No latency data available")
            report.append("")
        
        # Throughput Statistics
        report.append("## Throughput (Requests/Second)")
        if throughput_stats:
            report.append("")
            report.append("| Endpoint | Throughput (req/s) |")
            report.append("|----------|-------------------|")
            for endpoint, throughput in throughput_stats.items():
                report.append(f"| {endpoint} | {throughput} |")
            report.append("")
        else:
            report.append("No throughput data available")
            report.append("")
        
        # Error Analysis
        report.append("## Error Analysis")
        if error_analysis['error_breakdown']:
            report.append("")
            report.append("| Error Type | Count |")
            report.append("|------------|-------|")
            for error_type, count in error_analysis['error_breakdown'].items():
                report.append(f"| {error_type} | {count} |")
            report.append("")
        else:
            report.append("No errors detected")
            report.append("")
        
        # Scaling Capacity
        report.append("## Scaling Capacity Analysis")
        report.append(f"- **Current Load**: {scaling_capacity['current_load']} requests")
        report.append(f"- **Error Rate**: {scaling_capacity['error_rate_pct']}%")
        report.append(f"- **Scaling Factor**: {scaling_capacity['scaling_factor']}")
        report.append(f"- **Max Safe Load**: {scaling_capacity['max_safe_load']} requests")
        report.append("")
        
        # Recommendations
        report.append("## Recommendations")
        if error_analysis['error_rate_pct'] < 1:
            report.append("✓ System performing excellently. Ready for production deployment.")
        elif error_analysis['error_rate_pct'] < 5:
            report.append("⚠ System performance acceptable. Monitor closely in production.")
        else:
            report.append("✗ System needs optimization. Consider scaling before production.")
        report.append("")
        
        return "\n".join(report)
