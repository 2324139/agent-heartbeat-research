# 🫀 Agent Heartbeat: 分布式代理系統的心跳機制

**研究文檔** | 2026-03-29

---

## 📖 摘要

Agent Heartbeat（代理心跳）是分布式系統中的一種核心機制，用於監測 Agent 的健康狀態、存活性和可用性。通過定期發送心跳信號，系統可以及時發現故障、實現自動故障轉移和負載均衡。

---

## 1️⃣ 基本概念

### 什麼是 Agent Heartbeat？

Agent Heartbeat 是指：
- **定期信號** - Agent 定時發送「我還活著」的信號
- **健康檢查** - 監測 Agent 是否正常運行
- **故障檢測** - 快速發現 Agent 宕機或無響應
- **自愈機制** - 觸發自動恢復和故障轉移

### 核心組成

```
┌─────────────────────────────────────────┐
│          Heartbeat System               │
├─────────────────────────────────────────┤
│                                         │
│  Agent    Heartbeat Sender              │
│    │          │                         │
│    ├─ Interval Timer (5-10s)           │
│    ├─ Health Info                      │
│    └─ Status Message                   │
│                                         │
│  Monitor  Heartbeat Receiver            │
│    │          │                         │
│    ├─ Listener                         │
│    ├─ Timeout Detector                 │
│    └─ Failure Trigger                  │
│                                         │
│  Registry Health State Machine          │
│    │          │                         │
│    ├─ ALIVE   (接收到心跳)             │
│    ├─ SUSPECTED (超時未收)             │
│    ├─ DEAD    (多次超時)               │
│    └─ RECOVERED (恢復信號)             │
│                                         │
└─────────────────────────────────────────┘
```

---

## 2️⃣ 工作原理

### 典型心跳流程

```
時間軸：

T=0s    Agent A 啟動
        ├─ 自動向 Monitor 註冊
        └─ 開始發送心跳

T=5s    Agent A 發送第 1 個心跳 ✓
        Monitor 收到 → 狀態: ALIVE

T=10s   Agent A 發送第 2 個心跳 ✓
        Monitor 收到 → 狀態: ALIVE

T=15s   Agent A 發送第 3 個心跳 ✓
        Monitor 收到 → 狀態: ALIVE

T=20s   Agent A 崩潰 ✗
        (心跳信號停止發送)

T=25s   Monitor 超時警告
        (1 次未收到)
        狀態: SUSPECTED

T=30s   Monitor 仍未收到
        (2 次未收到)
        狀態: SUSPECTED

T=35s   Monitor 確認故障
        (3 次未收到)
        狀態: DEAD
        ├─ 觸發故障轉移
        ├─ 啟動備用 Agent
        └─ 發送告警

T=40s   Agent A 恢復 ✓
        發送恢復信號
        狀態: ALIVE → RECOVERED
```

### 心跳信號內容

典型的心跳消息包含：

```json
{
  "agent_id": "agent-001",
  "timestamp": 1680076800,
  "sequence": 42,
  "status": "ALIVE",
  "metrics": {
    "cpu_usage": 45.2,
    "memory_mb": 256.5,
    "disk_usage": 72.1,
    "request_count": 1523,
    "error_count": 2,
    "uptime_seconds": 3600
  },
  "health": {
    "database": "HEALTHY",
    "cache": "HEALTHY",
    "api": "DEGRADED"
  },
  "version": "1.0.5",
  "capabilities": ["search", "index", "classify"]
}
```

---

## 3️⃣ 應用場景

### 場景 1: 微服務架構

```
┌─────────────────┐
│  Service A      │ ─┐ 心跳
├─────────────────┤  │
│  Service B      │ ─┤ 心跳
├─────────────────┤  │
│  Service C      │ ─┤ 心跳
├─────────────────┤  │
│  Service D      │ ─┘ 心跳
└─────────────────┘
         │
         ↓ (所有心跳彙總)
┌─────────────────┐
│  Health Monitor │
├─────────────────┤
│  - 監測 4 個服務│
│  - 計算可用性   │
│  - 觸發故障轉移 │
└─────────────────┘
```

### 場景 2: 分布式爬蟲

```
爬蟲 Node 1 ──┐
爬蟲 Node 2 ──┤
爬蟲 Node 3 ──├─→ Monitor ─→ 動態分配任務
爬蟲 Node 4 ──┤              自動擴縮容
爬蟲 Node 5 ──┘
```

### 場景 3: 多 Agent 協作

```
Agent A (任務分配)
    │ 監測心跳
    ├─→ Agent B (執行)
    ├─→ Agent C (執行)
    └─→ Agent D (執行)

如果 B 沒有心跳 → 自動分配給 C 或 D
```

### 場景 4: 數據庫集群

```
Primary DB ──┐
Secondary 1 ──┤
Secondary 2 ──├─→ Cluster Manager
Secondary 3 ──┤
Backup DB   ──┘

心跳 + Quorum 共識 → 自動故障轉移
```

---

## 4️⃣ 核心指標

### 性能指標

| 指標 | 建議值 | 說明 |
|------|--------|------|
| **心跳間隔** | 5-10s | 太頻繁浪費資源，太稀疏無法及時發現 |
| **超時倍數** | 2-3x | 允許 2-3 個心跳周期失敗 |
| **檢測延遲** | 10-30s | 從故障到檢測的時間 |
| **假死率** | < 1% | 誤判為故障的概率 |
| **恢復時間** | < 1s | 自動恢復的平均時間 |

### 可靠性指標

```
可用性 = (正常運行時間) / (總時間)

例：
- 99% 可用性 = 年停機 87.6 小時
- 99.9% 可用性 = 年停機 8.76 小時
- 99.99% 可用性 = 年停機 52.6 分鐘

心跳機制可幫助達到 99.9%+ 的可用性
```

---

## 5️⃣ 實現方案

### 方案 1: 簡單心跳 (TCP/UDP)

```bash
#!/bin/bash
# Agent 心跳發送器

AGENT_ID="agent-001"
MONITOR_HOST="monitor.example.com"
MONITOR_PORT=5000
INTERVAL=10

while true; do
  # 構建心跳消息
  HEARTBEAT="{
    \"agent_id\": \"$AGENT_ID\",
    \"timestamp\": $(date +%s),
    \"status\": \"ALIVE\",
    \"cpu\": $(top -bn1 | grep "Cpu" | awk '{print $2}')
  }"
  
  # 發送心跳
  echo "$HEARTBEAT" | nc -u $MONITOR_HOST $MONITOR_PORT
  
  sleep $INTERVAL
done
```

### 方案 2: HTTP 長輪詢

```python
import requests
import time
import json

class AgentHeartbeat:
    def __init__(self, agent_id, monitor_url):
        self.agent_id = agent_id
        self.monitor_url = monitor_url
        self.sequence = 0
    
    def send_heartbeat(self):
        """發送心跳信號"""
        payload = {
            "agent_id": self.agent_id,
            "sequence": self.sequence,
            "timestamp": time.time(),
            "status": "ALIVE",
            "metrics": self.collect_metrics()
        }
        
        try:
            response = requests.post(
                f"{self.monitor_url}/heartbeat",
                json=payload,
                timeout=5
            )
            self.sequence += 1
            return response.status_code == 200
        except Exception as e:
            print(f"心跳發送失敗: {e}")
            return False
    
    def collect_metrics(self):
        """收集性能指標"""
        import psutil
        return {
            "cpu": psutil.cpu_percent(),
            "memory": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage('/').percent
        }
    
    def start_heartbeat_loop(self, interval=10):
        """啟動心跳循環"""
        while True:
            self.send_heartbeat()
            time.sleep(interval)

# 使用
agent = AgentHeartbeat("agent-001", "http://monitor:8080")
agent.start_heartbeat_loop(interval=10)
```

### 方案 3: 消息隊列 (RabbitMQ/Kafka)

```python
import pika
import json
import time

class HeartbeatPublisher:
    def __init__(self, agent_id, rabbitmq_host):
        self.agent_id = agent_id
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(rabbitmq_host)
        )
        self.channel = self.connection.channel()
        self.channel.exchange_declare(
            exchange='heartbeat',
            exchange_type='fanout',
            durable=True
        )
    
    def publish_heartbeat(self):
        """發布心跳到交換機"""
        message = {
            "agent_id": self.agent_id,
            "timestamp": time.time(),
            "status": "ALIVE"
        }
        
        self.channel.basic_publish(
            exchange='heartbeat',
            routing_key='',
            body=json.dumps(message)
        )
    
    def start(self, interval=10):
        """啟動發佈"""
        try:
            while True:
                self.publish_heartbeat()
                time.sleep(interval)
        finally:
            self.connection.close()

# 監聽端
class HeartbeatSubscriber:
    def __init__(self, rabbitmq_host):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(rabbitmq_host)
        )
        self.channel = self.connection.channel()
        self.channel.exchange_declare(
            exchange='heartbeat',
            exchange_type='fanout'
        )
        
        result = self.channel.queue_declare(queue='', exclusive=True)
        self.queue_name = result.method.queue
        
        self.channel.queue_bind(
            exchange='heartbeat',
            queue=self.queue_name
        )
    
    def callback(self, ch, method, properties, body):
        """處理心跳"""
        message = json.loads(body)
        print(f"收到心跳: {message['agent_id']}")
        self.on_heartbeat(message)
    
    def on_heartbeat(self, message):
        """心跳處理邏輯"""
        # 更新 Agent 狀態
        # 更新時間戳
        # 檢查是否超時
        pass
    
    def start(self):
        """啟動監聽"""
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self.callback
        )
        self.channel.start_consuming()
```

### 方案 4: Raft 一致性協議

```python
# 使用 Raft 實現高可靠的集群心跳
# (偽代碼)

class RaftNode:
    def __init__(self, node_id, peers):
        self.node_id = node_id
        self.peers = peers
        self.state = "FOLLOWER"
        self.term = 0
        self.log = []
    
    def heartbeat(self):
        """Leader 發送心跳"""
        for peer in self.peers:
            message = {
                "type": "HEARTBEAT",
                "term": self.term,
                "leader_id": self.node_id,
                "commit_index": len(self.log),
                "timestamp": time.time()
            }
            self.send_to(peer, message)
    
    def on_heartbeat_received(self, message):
        """Follower 收到心跳"""
        if message["term"] > self.term:
            self.term = message["term"]
            self.state = "FOLLOWER"
        
        self.reset_election_timer()
    
    def election_timeout(self):
        """選舉超時"""
        if self.state == "FOLLOWER":
            self.start_election()
    
    def start_election(self):
        """啟動 Leader 選舉"""
        self.state = "CANDIDATE"
        self.term += 1
        self.vote_for(self.node_id)
        
        # 請求投票
        for peer in self.peers:
            self.request_vote(peer)
```

---

## 6️⃣ 故障轉移策略

### 策略 1: 立即轉移

```
Agent 心跳超時
    ↓
立即啟動備用 Agent
    ↓
問題: 可能誤判，資源浪費
```

### 策略 2: 延遲轉移（推薦）

```
第 1 次超時 (5s)
    ↓ SUSPECTED 狀態
第 2 次超時 (10s)
    ↓ 發送健康檢查請求
第 3 次超時 (15s)
    ↓ 確認故障 DEAD
    ↓ 啟動故障轉移
    ├─ 停止發送請求到故障 Agent
    ├─ 啟動備用 Agent
    └─ 重新分配任務
```

### 策略 3: 漸進式降級

```
正常
    ↓ (1 次超時)
降級 - 減少負載 50%
    ↓ (2 次超時)
降級 - 減少負載 25%，改用緩存
    ↓ (3 次超時)
故障轉移 - 切換到備用
```

---

## 7️⃣ 常見問題與解決方案

### Q1: 網絡抖動導致誤判

**問題**：網絡不穩定，正常 Agent 被誤判為故障

**解決**：
```
使用適應性超時
    ├─ 基礎超時: 10s
    ├─ 動態調整: 根據網絡延遲調整
    └─ 例: 如果平均延遲 2s，超時設為 10s
    
或使用多次確認
    ├─ 需要連續 3 次超時才確認故障
    ├─ 而不是 1 次就故障轉移
    └─ 成本: 增加檢測延遲 15s
```

### Q2: 心跳風暴

**問題**：所有 Agent 同時發送心跳，導致網絡擁塞

**解決**：
```
隨機化心跳時間
    ├─ 基礎間隔: 10s
    ├─ 隨機偏移: ±2s
    └─ 分散心跳發送時間

或使用分層架構
    ├─ 直接心跳: Agent → Local Monitor (10s)
    ├─ 彙總心跳: Local Monitor → Central (30s)
    └─ 減少中央負載
```

### Q3: Agent 停機維護

**問題**：正常的維護停機被誤認為故障

**解決**：
```
優雅關閉協議
    ├─ 步驟 1: Agent 發送 SHUTTING_DOWN 信號
    ├─ 步驟 2: Monitor 進入 MAINTENANCE 狀態
    ├─ 步驟 3: 停止分配新任務
    ├─ 步驟 4: 等待現有任務完成
    └─ 步驟 5: 關閉 Agent

或預約停機
    ├─ 提前 24 小時通知 Monitor
    ├─ Monitor 進入 SCHEDULED_MAINTENANCE
    └─ 自動安排故障轉移
```

### Q4: 時鐘不同步

**問題**：分布式系統中節點時鐘不一致

**解決**：
```
使用相對時間
    ├─ 不依賴絕對時間戳
    ├─ 而是使用相對超時
    └─ 例: 3 個心跳周期無響應

或 NTP 時鐘同步
    ├─ 所有節點同步到中央時鐘
    ├─ 誤差 < 100ms
    └─ 定期重新同步
```

---

## 8️⃣ 性能優化

### 優化 1: 批量心跳

```
原始方法:
    ├─ 5 個 Agent
    ├─ 每個每 10s 發送 1 個心跳
    └─ 總計: 每秒 0.5 個消息

批量方法:
    ├─ 收集 5 個 Agent 的心跳
    ├─ 每 10s 發送 1 個批量消息
    └─ 總計: 每秒 0.1 個消息
    
好處: 減少 80% 消息開銷
```

### 優化 2: 壓縮格式

```
JSON 格式 (典型):
    {"agent_id": "agent-001", ...} ≈ 200 bytes

Protobuf 格式:
    ≈ 50 bytes (減少 75%)

MessagePack 格式:
    ≈ 80 bytes (減少 60%)
```

### 優化 3: 心跳去重

```
只發送變化的信息
    ├─ 增量式心跳
    ├─ 例: CPU 未變化，不發送
    └─ 減少 50% 心跳大小

或週期性完整心跳
    ├─ 大多數時間: 輕量級心跳 (10 bytes)
    ├─ 每 5 分鐘: 完整心跳 (200 bytes)
    └─ 平均開銷減少 95%
```

---

## 9️⃣ 最佳實踐

### ✅ DO

```
✅ 使用適應性超時
✅ 實現優雅關閉
✅ 監測心跳延遲
✅ 記錄所有狀態轉移
✅ 定期測試故障轉移
✅ 實現告警機制
✅ 使用多層級檢查
✅ 實現自動恢復
```

### ❌ DON'T

```
❌ 太頻繁的心跳 (浪費資源)
❌ 太稀疏的心跳 (無法及時發現)
❌ 立即故障轉移 (容易誤判)
❌ 心跳與業務邏輯混淆
❌ 忽視網絡延遲
❌ 無日誌記錄
❌ 沒有監測和告警
❌ 不測試故障場景
```

---

## 🔟 實際案例

### 案例 1: Kafka Broker 心跳

```
Kafka 如何實現 Broker 健康檢查：

1. Broker 向 ZooKeeper 發送心跳
2. 心跳間隔: 6 秒
3. 超時: 18 秒 (3x 倍數)
4. 如果 Broker 離線:
   ├─ ZooKeeper 感知故障
   ├─ Controller 觸發 Leader 選舉
   └─ 自動重分配分區副本

效果: 故障檢測 < 20 秒
```

### 案例 2: Consul Service Mesh

```
Consul 的健康檢查機制：

1. Agent 啟動時註冊
2. 定期執行健康檢查
   ├─ HTTP check (調用 /health)
   ├─ TCP check (連接測試)
   ├─ Script check (執行腳本)
   └─ TTL check (依賴客戶端上報)
3. 檢查間隔: 10 秒
4. 失敗門檻: 3 次失敗確認
5. 故障檢測延遲: ~30 秒

效果: 99.99% 可用性
```

### 案例 3: Kubernetes Pod 健康檢查

```
K8s 的 Probe 機制：

1. Liveness Probe (存活檢查)
   ├─ 檢查容器是否仍在運行
   ├─ 失敗則重啟容器
   └─ 間隔: 10 秒

2. Readiness Probe (就緒檢查)
   ├─ 檢查是否可接收流量
   ├─ 失敗則移除負載均衡
   └─ 間隔: 5 秒

3. Startup Probe (啟動檢查)
   ├─ 檢查應用是否啟動完成
   ├─ 失敗則重啟容器
   └─ 間隔: 1 秒

效果: 自動故障恢復，無需手工干預
```

---

## 1️⃣1️⃣ 相關技術

### 相關概念

| 技術 | 用途 | 關聯 |
|------|------|------|
| **健康檢查** | 驗證服務健康 | 比心跳更詳細 |
| **故障轉移** | 自動切換 | 由心跳觸發 |
| **服務發現** | 動態定位服務 | 需要心跳確認可用性 |
| **負載均衡** | 分散請求 | 基於心跳狀態分配 |
| **監測告警** | 性能監測 | 整合心跳數據 |
| **日誌聚合** | 事件記錄 | 記錄心跳相關事件 |

### 實現框架

```
開源項目:
├─ ZooKeeper     (分布式協調)
├─ etcd          (KV 存儲 + 心跳)
├─ Consul        (Service Mesh)
├─ Eureka        (服務發現)
├─ Nacos         (配置 + 服務)
├─ Sentinel      (流量控制)
└─ Envoy         (L7 代理)

都內置了心跳機制
```

---

## 1️⃣2️⃣ 總結

### 核心要點

✅ **心跳是分布式系統的基礎**
- 故障檢測的第一步
- 啟動故障轉移的觸發器
- 維護系統健康狀態的關鍵

✅ **心跳間隔需要平衡**
- 太短: 浪費資源，增加網絡負擔
- 太長: 無法及時發現故障

✅ **需要多層級驗證**
- 避免誤判
- 實現優雅降級
- 逐步擴大

✅ **監測和告警很重要**
- 記錄所有心跳事件
- 監測心跳延遲
- 及時發出告警

✅ **要進行故障轉移演練**
- 定期測試
- 驗證自動轉移有效性
- 發現潛在問題

---

## 📚 推薦閱讀

- *The Art of Computer System Performance Analysis*
- *Designing Data-Intensive Applications* (Chapter 8: The Trouble with Distributed Systems)
- Raft Consensus Algorithm: https://raft.github.io/
- Google Chubby: https://research.google/pubs/chubby/

---

**文檔版本**: 1.0  
**最後更新**: 2026-03-29  
**作者**: Pi Coding Agent  
**狀態**: 完成
