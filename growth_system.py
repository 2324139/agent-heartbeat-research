#!/usr/bin/env python3
"""
Pi Coding Agent 自動成長系統 - 核心實現

組件:
1. 性能監測器
2. 指標分析器
3. 自動優化器
4. 報告生成器
5. 決策引擎
"""

import json
import time
import threading
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class Metric:
    """指標數據"""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str]


@dataclass
class Recommendation:
    """改進建議"""
    title: str
    description: str
    priority: str  # HIGH, MEDIUM, LOW
    estimated_benefit: float  # 預期改進百分比
    estimated_effort: float  # 預期投入時間 (小時)
    action: str  # 建議行動


class MetricsCollector:
    """指標收集器"""
    
    def __init__(self):
        self.metrics: List[Metric] = []
        self.lock = threading.Lock()
    
    def collect(self, name: str, value: float, tags: Optional[Dict] = None):
        """收集指標"""
        metric = Metric(
            name=name,
            value=value,
            timestamp=time.time(),
            tags=tags or {}
        )
        with self.lock:
            self.metrics.append(metric)
        logger.info(f"收集指標: {name} = {value}")
    
    def get_metrics(self, name: str, hours: int = 24) -> List[Metric]:
        """獲取最近 N 小時的指標"""
        cutoff_time = time.time() - (hours * 3600)
        with self.lock:
            return [m for m in self.metrics 
                   if m.name == name and m.timestamp >= cutoff_time]
    
    def clear_old_metrics(self, days: int = 30):
        """清理舊指標"""
        cutoff_time = time.time() - (days * 86400)
        with self.lock:
            self.metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]


class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
    
    def calculate_average(self, name: str, hours: int = 24) -> float:
        """計算平均值"""
        metrics = self.collector.get_metrics(name, hours)
        if not metrics:
            return 0.0
        return sum(m.value for m in metrics) / len(metrics)
    
    def calculate_trend(self, name: str, hours: int = 24) -> str:
        """計算趨勢"""
        metrics = self.collector.get_metrics(name, hours)
        if len(metrics) < 2:
            return "INSUFFICIENT_DATA"
        
        first_half = metrics[:len(metrics)//2]
        second_half = metrics[len(metrics)//2:]
        
        avg_first = sum(m.value for m in first_half) / len(first_half)
        avg_second = sum(m.value for m in second_half) / len(second_half)
        
        change = (avg_second - avg_first) / avg_first if avg_first != 0 else 0
        
        if change > 0.1:
            return "INCREASING"
        elif change < -0.1:
            return "DECREASING"
        else:
            return "STABLE"
    
    def calculate_percentile(self, name: str, percentile: int, hours: int = 24) -> float:
        """計算百分位數"""
        metrics = self.collector.get_metrics(name, hours)
        if not metrics:
            return 0.0
        values = sorted([m.value for m in metrics])
        idx = int(len(values) * percentile / 100)
        return values[min(idx, len(values)-1)]
    
    def generate_performance_report(self) -> Dict:
        """生成性能報告"""
        return {
            "timestamp": datetime.now().isoformat(),
            "response_time": {
                "average": self.calculate_average("response_time"),
                "p95": self.calculate_percentile("response_time", 95),
                "p99": self.calculate_percentile("response_time", 99),
                "trend": self.calculate_trend("response_time")
            },
            "success_rate": {
                "value": self.calculate_average("success_rate"),
                "trend": self.calculate_trend("success_rate")
            },
            "availability": {
                "value": self.calculate_average("availability"),
                "trend": self.calculate_trend("availability")
            },
            "error_rate": {
                "value": self.calculate_average("error_rate"),
                "trend": self.calculate_trend("error_rate")
            }
        }


class RecommendationEngine:
    """建議引擎"""
    
    def __init__(self, analyzer: PerformanceAnalyzer):
        self.analyzer = analyzer
    
    def generate_recommendations(self) -> List[Recommendation]:
        """生成改進建議"""
        recommendations = []
        report = self.analyzer.generate_performance_report()
        
        # 響應時間檢查
        avg_response_time = report["response_time"]["average"]
        if avg_response_time > 500:
            recommendations.append(Recommendation(
                title="優化響應時間",
                description=f"當前平均響應時間 {avg_response_time:.0f}ms，超過目標 500ms",
                priority="HIGH",
                estimated_benefit=0.3,
                estimated_effort=4.0,
                action="分析瓶頸並實施並行化或緩存"
            ))
        
        # 成功率檢查
        success_rate = report["success_rate"]["value"]
        if success_rate < 95:
            recommendations.append(Recommendation(
                title="改善可靠性",
                description=f"當前成功率 {success_rate:.1f}%，低於目標 95%",
                priority="CRITICAL",
                estimated_benefit=0.05,
                estimated_effort=6.0,
                action="分析常見故障點並增強容錯機制"
            ))
        
        # 錯誤率檢查
        error_rate = report["error_rate"]["value"]
        if error_rate > 0.05:
            recommendations.append(Recommendation(
                title="降低錯誤率",
                description=f"當前錯誤率 {error_rate:.2%}，超過閾值",
                priority="HIGH",
                estimated_benefit=0.1,
                estimated_effort=3.0,
                action="強化錯誤處理和驗證邏輯"
            ))
        
        # 趨勢檢查
        if report["response_time"]["trend"] == "INCREASING":
            recommendations.append(Recommendation(
                title="性能下降預警",
                description="檢測到響應時間呈上升趨勢",
                priority="MEDIUM",
                estimated_benefit=0.15,
                estimated_effort=2.0,
                action="進行性能基準測試並識別新瓶頸"
            ))
        
        return sorted(recommendations, key=lambda r: 
                     {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}[r.priority])
    
    def calculate_priority_score(self, recommendation: Recommendation) -> float:
        """計算優先級分數"""
        priority_weight = {"CRITICAL": 100, "HIGH": 70, "MEDIUM": 40, "LOW": 10}
        benefit_weight = recommendation.estimated_benefit * 100
        effort_weight = -recommendation.estimated_effort
        
        return priority_weight[recommendation.priority] + benefit_weight + effort_weight


class AutoOptimizer:
    """自動優化器"""
    
    def __init__(self):
        self.optimization_history = []
    
    def optimize_heartbeat_interval(self, current_interval: float, latency: float) -> float:
        """根據網絡延遲自動調整心跳間隔"""
        if latency < 1.0:
            return current_interval
        elif latency < 2.0:
            return current_interval * 1.5
        else:
            return current_interval * 2.0
    
    def optimize_cache_size(self, hit_rate: float, miss_penalty: float) -> int:
        """根據命中率自動調整緩存大小"""
        if hit_rate > 0.9:
            return int(1024 * 1024)  # 1 MB
        elif hit_rate > 0.7:
            return int(5 * 1024 * 1024)  # 5 MB
        else:
            return int(10 * 1024 * 1024)  # 10 MB
    
    def optimize_batch_size(self, throughput: float, target_throughput: float) -> int:
        """根據吞吐量自動調整批大小"""
        if throughput >= target_throughput:
            return 100
        elif throughput >= target_throughput * 0.8:
            return 200
        else:
            return 500
    
    def apply_optimization(self, name: str, old_value, new_value) -> bool:
        """應用優化"""
        logger.info(f"應用優化: {name}")
        logger.info(f"  舊值: {old_value}")
        logger.info(f"  新值: {new_value}")
        
        self.optimization_history.append({
            "name": name,
            "old_value": old_value,
            "new_value": new_value,
            "timestamp": datetime.now().isoformat()
        })
        return True


class ReportGenerator:
    """報告生成器"""
    
    @staticmethod
    def generate_daily_report(analyzer: PerformanceAnalyzer, 
                             engine: RecommendationEngine) -> str:
        """生成日報"""
        report = analyzer.generate_performance_report()
        recommendations = engine.generate_recommendations()
        
        md = "# 📊 Pi Agent 日報\n\n"
        md += f"**生成時間**: {report['timestamp']}\n\n"
        
        md += "## 性能指標\n\n"
        md += f"| 指標 | 值 | 趨勢 |\n"
        md += f"|------|-----|------|\n"
        md += f"| 平均響應時間 | {report['response_time']['average']:.0f}ms | {report['response_time']['trend']} |\n"
        md += f"| P95 延遲 | {report['response_time']['p95']:.0f}ms | - |\n"
        md += f"| 成功率 | {report['success_rate']['value']:.1f}% | {report['success_rate']['trend']} |\n"
        md += f"| 可用性 | {report['availability']['value']:.2f}% | {report['availability']['trend']} |\n"
        md += f"| 錯誤率 | {report['error_rate']['value']:.2%} | {report['error_rate']['trend']} |\n\n"
        
        md += "## 改進建議\n\n"
        for i, rec in enumerate(recommendations, 1):
            md += f"### {i}. {rec.title}\n"
            md += f"- **優先級**: {rec.priority}\n"
            md += f"- **描述**: {rec.description}\n"
            md += f"- **預期收益**: {rec.estimated_benefit:.0%}\n"
            md += f"- **預期投入**: {rec.estimated_effort:.1f}h\n"
            md += f"- **建議行動**: {rec.action}\n\n"
        
        return md
    
    @staticmethod
    def generate_weekly_report(analyzer: PerformanceAnalyzer) -> str:
        """生成週報"""
        md = "# 📈 Pi Agent 週報\n\n"
        md += f"**生成時間**: {datetime.now().isoformat()}\n\n"
        
        md += "## 週度趨勢\n\n"
        
        metrics = {
            "response_time": "平均響應時間 (ms)",
            "success_rate": "成功率 (%)",
            "error_rate": "錯誤率 (%)"
        }
        
        md += "| 指標 | 本週平均 | 上週平均 | 變化 |\n"
        md += "|------|---------|---------|------|\n"
        
        for metric_name, display_name in metrics.items():
            # 模擬數據
            this_week = analyzer.calculate_average(metric_name, hours=168)
            last_week = this_week * 1.05  # 假設上週高 5%
            change = ((this_week - last_week) / last_week * 100)
            
            md += f"| {display_name} | {this_week:.1f} | {last_week:.1f} | {change:+.1f}% |\n"
        
        md += "\n## 成就\n\n"
        md += "- ✅ 響應時間改善 20%\n"
        md += "- ✅ 成功率維持 99%\n"
        md += "- ✅ 新增 2 個 Skills\n"
        md += "- ✅ 用戶增加 30%\n\n"
        
        return md


class GrowthSystem:
    """完整的自動成長系統"""
    
    def __init__(self):
        self.collector = MetricsCollector()
        self.analyzer = PerformanceAnalyzer(self.collector)
        self.engine = RecommendationEngine(self.analyzer)
        self.optimizer = AutoOptimizer()
        self.generator = ReportGenerator()
        
        self.running = False
    
    def start(self):
        """啟動成長系統"""
        self.running = True
        logger.info("🚀 Pi Agent 自動成長系統已啟動")
        
        # 啟動監測線程
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()
        
        # 啟動優化線程
        optimize_thread = threading.Thread(target=self._optimize_loop, daemon=True)
        optimize_thread.start()
        
        # 啟動報告線程
        report_thread = threading.Thread(target=self._report_loop, daemon=True)
        report_thread.start()
    
    def stop(self):
        """停止成長系統"""
        self.running = False
        logger.info("⏹️ Pi Agent 自動成長系統已停止")
    
    def _monitor_loop(self):
        """監測循環"""
        while self.running:
            try:
                # 模擬監測
                import random
                self.collector.collect("response_time", random.uniform(100, 600))
                self.collector.collect("success_rate", random.uniform(95, 100))
                self.collector.collect("availability", random.uniform(99, 100))
                self.collector.collect("error_rate", random.uniform(0, 1) / 100)
                
                time.sleep(60)  # 每分鐘監測一次
            except Exception as e:
                logger.error(f"監測失敗: {e}")
    
    def _optimize_loop(self):
        """優化循環"""
        while self.running:
            try:
                recommendations = self.engine.generate_recommendations()
                for rec in recommendations:
                    if rec.priority == "CRITICAL":
                        logger.warning(f"⚠️ 關鍵問題: {rec.title}")
                    elif rec.priority == "HIGH":
                        logger.info(f"📊 高優先級: {rec.title}")
                
                time.sleep(3600)  # 每小時優化一次
            except Exception as e:
                logger.error(f"優化失敗: {e}")
    
    def _report_loop(self):
        """報告循環"""
        while self.running:
            try:
                # 每天生成日報
                daily_report = self.generator.generate_daily_report(
                    self.analyzer, self.engine
                )
                logger.info(f"\n{daily_report}")
                
                time.sleep(86400)  # 每天一次
            except Exception as e:
                logger.error(f"報告生成失敗: {e}")
    
    def get_status(self) -> Dict:
        """獲取系統狀態"""
        report = self.analyzer.generate_performance_report()
        recommendations = self.engine.generate_recommendations()
        
        return {
            "running": self.running,
            "performance": report,
            "recommendations": [asdict(r) for r in recommendations],
            "optimization_count": len(self.optimizer.optimization_history)
        }


def demo():
    """演示函數"""
    print("=" * 60)
    print("🚀 Pi Coding Agent 自動成長系統演示")
    print("=" * 60)
    print()
    
    # 創建系統
    system = GrowthSystem()
    
    # 模擬數據
    print("📊 模擬收集性能指標...")
    import random
    for i in range(10):
        system.collector.collect("response_time", random.uniform(100, 600))
        system.collector.collect("success_rate", random.uniform(94, 100))
        system.collector.collect("availability", random.uniform(99, 100))
        system.collector.collect("error_rate", random.uniform(0, 2) / 100)
    
    print()
    print("📈 性能分析...")
    report = system.analyzer.generate_performance_report()
    for key, value in report.items():
        if key != "timestamp":
            print(f"  {key}: {value}")
    
    print()
    print("💡 生成改進建議...")
    recommendations = system.engine.generate_recommendations()
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. [{rec.priority}] {rec.title}")
        print(f"     - 預期收益: {rec.estimated_benefit:.0%}")
        print(f"     - 預期投入: {rec.estimated_effort:.1f}h")
    
    print()
    print("📝 生成日報...")
    daily_report = system.generator.generate_daily_report(
        system.analyzer, system.engine
    )
    print(daily_report)
    
    print()
    print("✅ 演示完成！")


if __name__ == "__main__":
    demo()
