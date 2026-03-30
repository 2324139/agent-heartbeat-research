#!/usr/bin/env python3
"""
Agent Heartbeat 系統實現示例

演示如何實現一個簡單但功能完整的心跳系統
"""

import time
import threading
import json
from datetime import datetime
from collections import defaultdict
from enum import Enum
from typing import Dict, Callable, Optional
import logging

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent 狀態枚舉"""
    ALIVE = "ALIVE"           # 正常
    SUSPECTED = "SUSPECTED"   # 可疑
    DEAD = "DEAD"            # 故障
    RECOVERED = "RECOVERED"  # 已恢復


class HeartbeatConfig:
    """心跳配置"""
    def __init__(
        self,
        interval: float = 5.0,           # 心跳間隔 (秒)
        timeout: float = 15.0,           # 超時時間 (秒)
        failure_threshold: int = 3,      # 故障確認次數
        check_interval: float = 2.0      # 檢查間隔 (秒)
    ):
        self.interval = interval
        self.timeout = timeout
        self.failure_threshold = failure_threshold
        self.check_interval = check_interval


class Agent:
    """Agent 類 - 代表一個分布式代理"""
    
    def __init__(self, agent_id: str, config: HeartbeatConfig):
        self.agent_id = agent_id
        self.config = config
        self.sequence = 0
        self.metrics = {
            "cpu": 0.0,
            "memory": 0.0,
            "requests": 0,
            "errors": 0
        }
        self.running = False
        self.heartbeat_thread = None
    
    def collect_metrics(self) -> Dict:
        """收集性能指標"""
        import random
        return {
            "cpu": round(random.uniform(10, 80), 2),
            "memory": round(random.uniform(20, 60), 2),
            "requests": random.randint(100, 1000),
            "errors": random.randint(0, 5)
        }
    
    def get_heartbeat_message(self) -> Dict:
        """構建心跳消息"""
        self.sequence += 1
        return {
            "agent_id": self.agent_id,
            "sequence": self.sequence,
            "timestamp": datetime.now().isoformat(),
            "status": "ALIVE",
            "metrics": self.collect_metrics()
        }
    
    def start_heartbeat(self, callback: Callable[[Dict], None]):
        """啟動定期心跳"""
        self.running = True
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            args=(callback,),
            daemon=True
        )
        self.heartbeat_thread.start()
        logger.info(f"Agent {self.agent_id} 啟動心跳")
    
    def _heartbeat_loop(self, callback: Callable[[Dict], None]):
        """心跳循環"""
        while self.running:
            message = self.get_heartbeat_message()
            callback(message)
            logger.debug(f"Agent {self.agent_id} 發送心跳 (序列: {self.sequence})")
            time.sleep(self.config.interval)
    
    def stop_heartbeat(self):
        """停止心跳"""
        self.running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join()
        logger.info(f"Agent {self.agent_id} 停止心跳")


class AgentRegistry:
    """Agent 註冊表 - 追踪所有 Agent 的狀態"""
    
    def __init__(self, config: HeartbeatConfig):
        self.config = config
        self.agents: Dict[str, Dict] = {}  # agent_id -> {last_heartbeat, status, fail_count}
        self.status_callbacks: Dict[str, Callable] = defaultdict(list)
    
    def register_agent(self, agent_id: str):
        """註冊新 Agent"""
        self.agents[agent_id] = {
            "last_heartbeat": None,
            "status": AgentStatus.ALIVE,
            "fail_count": 0,
            "sequence": 0
        }
        logger.info(f"Agent {agent_id} 已註冊")
    
    def on_heartbeat(self, agent_id: str, message: Dict):
        """處理心跳消息"""
        if agent_id not in self.agents:
            self.register_agent(agent_id)
        
        agent_info = self.agents[agent_id]
        agent_info["last_heartbeat"] = time.time()
        agent_info["fail_count"] = 0
        agent_info["sequence"] = message.get("sequence", 0)
        
        # 如果是從 SUSPECTED 或 DEAD 恢復
        if agent_info["status"] != AgentStatus.ALIVE:
            old_status = agent_info["status"]
            agent_info["status"] = AgentStatus.RECOVERED
            logger.warning(
                f"Agent {agent_id} 從 {old_status.value} 恢復到 ALIVE"
            )
            self._trigger_callbacks(agent_id, AgentStatus.RECOVERED)
    
    def check_timeout(self):
        """檢查超時的 Agent"""
        current_time = time.time()
        
        for agent_id, agent_info in self.agents.items():
            if agent_info["last_heartbeat"] is None:
                continue
            
            elapsed = current_time - agent_info["last_heartbeat"]
            
            if elapsed > self.config.timeout:
                agent_info["fail_count"] += 1
                
                # 更新狀態
                if agent_info["fail_count"] == 1:
                    # 第一次超時
                    if agent_info["status"] == AgentStatus.ALIVE:
                        agent_info["status"] = AgentStatus.SUSPECTED
                        logger.warning(
                            f"Agent {agent_id} 超時 ({elapsed:.1f}s > {self.config.timeout}s), "
                            f"狀態: SUSPECTED"
                        )
                        self._trigger_callbacks(agent_id, AgentStatus.SUSPECTED)
                
                elif agent_info["fail_count"] >= self.config.failure_threshold:
                    # 多次超時，確認故障
                    if agent_info["status"] != AgentStatus.DEAD:
                        agent_info["status"] = AgentStatus.DEAD
                        logger.error(
                            f"Agent {agent_id} 確認故障 (連續 {agent_info['fail_count']} 次超時), "
                            f"狀態: DEAD"
                        )
                        self._trigger_callbacks(agent_id, AgentStatus.DEAD)
    
    def register_callback(
        self,
        status: AgentStatus,
        callback: Callable[[str], None]
    ):
        """註冊狀態變更回調"""
        key = f"status_change_{status.value}"
        self.status_callbacks[key].append(callback)
    
    def _trigger_callbacks(self, agent_id: str, status: AgentStatus):
        """觸發回調"""
        key = f"status_change_{status.value}"
        for callback in self.status_callbacks.get(key, []):
            try:
                callback(agent_id)
            except Exception as e:
                logger.error(f"回調執行失敗: {e}")
    
    def get_status(self, agent_id: str) -> Optional[AgentStatus]:
        """獲取 Agent 狀態"""
        if agent_id in self.agents:
            return self.agents[agent_id]["status"]
        return None
    
    def get_all_agents(self) -> Dict[str, Dict]:
        """獲取所有 Agent 狀態"""
        return self.agents.copy()


class HeartbeatMonitor:
    """心跳監測器 - 主控制器"""
    
    def __init__(self, config: HeartbeatConfig):
        self.config = config
        self.registry = AgentRegistry(config)
        self.running = False
        self.monitor_thread = None
    
    def start(self):
        """啟動監測"""
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("心跳監測器已啟動")
    
    def _monitor_loop(self):
        """監測循環"""
        while self.running:
            self.registry.check_timeout()
            time.sleep(self.config.check_interval)
    
    def stop(self):
        """停止監測"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("心跳監測器已停止")
    
    def print_status(self):
        """打印所有 Agent 狀態"""
        print("\n" + "="*60)
        print("Agent 狀態報告")
        print("="*60)
        
        agents = self.registry.get_all_agents()
        
        for agent_id, info in sorted(agents.items()):
            last_hb = info["last_heartbeat"]
            if last_hb:
                elapsed = time.time() - last_hb
                last_hb_str = f"{elapsed:.1f}s 前"
            else:
                last_hb_str = "未收到"
            
            print(f"{agent_id:20} | 狀態: {info['status'].value:10} | "
                  f"序列: {info['sequence']:3} | "
                  f"最後心跳: {last_hb_str}")
        
        print("="*60 + "\n")


def demo_basic_heartbeat():
    """演示 1: 基本心跳系統"""
    print("\n" + "="*60)
    print("演示 1: 基本心跳系統")
    print("="*60 + "\n")
    
    config = HeartbeatConfig(
        interval=2.0,           # 每 2 秒一個心跳
        timeout=6.0,            # 6 秒超時
        failure_threshold=2,    # 2 次失敗確認故障
        check_interval=1.0      # 每 1 秒檢查一次
    )
    
    monitor = HeartbeatMonitor(config)
    monitor.start()
    
    # 創建 3 個 Agent
    agents = {
        "agent-001": Agent("agent-001", config),
        "agent-002": Agent("agent-002", config),
        "agent-003": Agent("agent-003", config),
    }
    
    # 啟動 Agent
    for agent in agents.values():
        agent.start_heartbeat(
            lambda msg, aid=agent.agent_id: monitor.registry.on_heartbeat(aid, msg)
        )
    
    # 運行 20 秒
    try:
        for i in range(10):
            time.sleep(2)
            monitor.print_status()
            
            # 在第 5 秒時停止 agent-002
            if i == 2:
                print(">>> 模擬 Agent 002 故障...")
                agents["agent-002"].stop_heartbeat()
            
            # 在第 15 秒時恢復 agent-002
            if i == 7:
                print(">>> Agent 002 已恢復...")
                agents["agent-002"].start_heartbeat(
                    lambda msg: monitor.registry.on_heartbeat("agent-002", msg)
                )
    finally:
        # 清理
        for agent in agents.values():
            agent.stop_heartbeat()
        monitor.stop()
        
        print("\n演示完成！")


def demo_failure_handling():
    """演示 2: 故障轉移"""
    print("\n" + "="*60)
    print("演示 2: 故障轉移")
    print("="*60 + "\n")
    
    config = HeartbeatConfig(
        interval=1.0,
        timeout=3.0,
        failure_threshold=2,
        check_interval=0.5
    )
    
    monitor = HeartbeatMonitor(config)
    monitor.start()
    
    # 註冊故障轉移回調
    def on_agent_dead(agent_id):
        print(f"🚨 ALERT: {agent_id} 故障，啟動故障轉移...")
        print(f"   - 重新分配任務")
        print(f"   - 啟動備用 Agent")
        print(f"   - 發送告警通知")
    
    monitor.registry.register_callback(
        AgentStatus.DEAD,
        on_agent_dead
    )
    
    # 創建 Agent
    agent = Agent("critical-agent", config)
    agent.start_heartbeat(
        lambda msg: monitor.registry.on_heartbeat("critical-agent", msg)
    )
    
    # 運行並模擬故障
    try:
        for i in range(15):
            time.sleep(0.5)
            
            if i == 8:
                print("\n>>> 模擬 Agent 故障...")
                agent.stop_heartbeat()
            
            if i % 3 == 0:
                monitor.print_status()
    finally:
        agent.stop_heartbeat()
        monitor.stop()


def demo_adaptive_timeout():
    """演示 3: 適應性超時"""
    print("\n" + "="*60)
    print("演示 3: 適應性超時")
    print("="*60 + "\n")
    
    print("""
適應性超時概念:
- 基礎超時: 5 秒
- 網絡抖動時動態調整
- 平均延遲 < 1s: 使用 5s 超時
- 平均延遲 1-2s: 使用 8s 超時  
- 平均延遲 > 2s: 使用 12s 超時

優點:
- 減少誤判率
- 適應不同網絡狀況
- 提高系統可靠性
    """)


if __name__ == "__main__":
    # 運行演示
    demo_basic_heartbeat()
    # demo_failure_handling()
    # demo_adaptive_timeout()
