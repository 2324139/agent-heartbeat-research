# Agent Heartbeat 最佳實踐指南

## 📋 快速檢查清單

### ✅ DO - 應該做的事

```
心跳設計:
  ✅ 根據場景選擇合適的間隔 (5-30s)
  ✅ 使用適應性超時機制
  ✅ 實現多層級驗證 (最少 2-3 層)
  ✅ 支持優雅關閉協議
  ✅ 記錄所有狀態轉移

實現質量:
  ✅ 非阻塞式心跳發送
  ✅ 獨立的監測線程
  ✅ 完善的錯誤處理
  ✅ 詳細的日誌記錄
  ✅ 測試各種故障場景

監測告警:
  ✅ 監測心跳延遲
  ✅ 實時告警機制
  ✅ 故障自動恢復
  ✅ 性能指標收集
  ✅ 定期健康檢查報告

維護運維:
  ✅ 定期測試故障轉移
  ✅ 監測系統資源使用
  ✅ 保留心跳歷史數據
  ✅ 文檔化配置說明
  ✅ 演練故障恢復流程
```

### ❌ DON'T - 不應該做的事

```
常見錯誤:
  ❌ 心跳間隔過短 (< 1s) - 浪費資源
  ❌ 心跳間隔過長 (> 60s) - 無法及時發現
  ❌ 立即故障轉移 - 容易誤判
  ❌ 無日誌記錄 - 無法診斷問題
  ❌ 不測試故障場景 - 上線後出問題

實現問題:
  ❌ 心跳在主線程阻塞 - 影響正常業務
  ❌ 沒有異常處理 - 單點故障風險
  ❌ 硬編碼超時時間 - 不適應環境變化
  ❌ 心跳風暴 - 所有 Agent 同時發送
  ❌ 依賴精確時鐘 - 分布式系統不可靠

監測問題:
  ❌ 無可視化儀表板 - 難以理解系統狀態
  ❌ 不監測心跳延遲 - 忽視性能退化
  ❌ 無告警機制 - 故障無人知曉
  ❌ 不保存歷史數據 - 無法分析趨勢
  ❌ 無恢復機制 - 故障自行消失
```

---

## 🎯 場景化建議

### 場景 1: 微服務框架 (Dubbo/Nacos)

```yaml
配置建議:
  心跳間隔: 10 秒
  超時時間: 30 秒 (3x)
  失敗次數: 3 次
  檢查間隔: 2 秒
  
特點:
  - 需要高可用性
  - 網絡相對穩定
  - 快速故障轉移 (< 1 分鐘)
  - 支持自動擴縮容
```

**實現示例**:
```python
config = HeartbeatConfig(
    interval=10,
    timeout=30,
    failure_threshold=3,
    check_interval=2
)
```

---

### 場景 2: Kubernetes 集群

```yaml
配置建議:
  Liveness Probe: 每 10 秒檢查一次
  Readiness Probe: 每 5 秒檢查一次
  Startup Probe: 每 1 秒檢查一次
  失敗次數: 3 次
  
特點:
  - 多層級檢查
  - 自動重啟
  - Pod 自動轉移
  - 支持健康檢查端點
```

**實現示例**:
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

---

### 場景 3: 分布式爬蟲系統

```yaml
配置建議:
  心跳間隔: 30 秒
  超時時間: 90 秒 (3x)
  失敗次數: 3 次
  檢查間隔: 10 秒
  
特點:
  - 網絡可能不穩定
  - 允許較長檢測延遲
  - 動態任務分配
  - 支持任務遷移
```

**實現示例**:
```python
config = HeartbeatConfig(
    interval=30,          # 較長間隔適應網絡不穩定
    timeout=90,           # 3 倍容差
    failure_threshold=3,
    check_interval=10
)
```

---

### 場景 4: 實時通信系統 (WebSocket)

```yaml
配置建議:
  心跳間隔: 30 秒
  心跳超時: 90 秒
  Ping/Pong: 加強級別
  
特點:
  - WebSocket 持久連接
  - 需要雙向心跳
  - 快速故障檢測
  - 自動重新連接
```

**實現示例**:
```javascript
// 客戶端 (JavaScript)
const ws = new WebSocket('ws://server:8080');

// 心跳發送
const heartbeatInterval = setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'heartbeat',
      timestamp: Date.now()
    }));
  }
}, 30000);

// 心跳接收
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === 'heartbeat') {
    // 更新最後心跳時間
    lastHeartbeatTime = Date.now();
  }
};

// 檢查超時
setInterval(() => {
  if (Date.now() - lastHeartbeatTime > 90000) {
    console.error('心跳超時，重新連接...');
    ws.close();
    reconnect();
  }
}, 10000);
```

---

## 📊 性能調優

### 問題: 高延遲環境

```
症狀:
  - 心跳經常超時
  - 誤判率高
  - 頻繁故障轉移

解決方案:
  1. 增加超時時間
  2. 實現適應性超時
  3. 使用多次確認
  4. 添加網絡狀態檢查
```

**實現**:
```python
class AdaptiveHeartbeatConfig:
    def __init__(self, base_interval=10, base_timeout=30):
        self.base_interval = base_interval
        self.base_timeout = base_timeout
        self.network_latency = 0
    
    def update_latency(self, latency_samples):
        # 計算平均延遲
        self.network_latency = sum(latency_samples) / len(latency_samples)
    
    def get_timeout(self):
        # 根據網絡延遲動態調整
        if self.network_latency < 1:
            return self.base_timeout
        elif self.network_latency < 2:
            return self.base_timeout * 1.5
        else:
            return self.base_timeout * 2
```

---

### 問題: 心跳風暴

```
症狀:
  - 大量 Agent 同時發送心跳
  - 網絡擁塞
  - Monitor CPU 飆升

解決方案:
  1. 隨機化心跳時間
  2. 使用分層架構
  3. 批量發送心跳
  4. 優化序列化格式
```

**實現**:
```python
import random

class StaggeredHeartbeatConfig:
    def __init__(self, base_interval=10):
        self.base_interval = base_interval
        self.jitter = base_interval * 0.2  # 20% 隨機偏移
    
    def get_next_heartbeat_delay(self):
        # 隨機偏移避免同時發送
        offset = random.uniform(-self.jitter, self.jitter)
        return self.base_interval + offset

# 使用
config = StaggeredHeartbeatConfig(base_interval=10)
delay = config.get_next_heartbeat_delay()  # 8-12 秒之間
```

---

## 🔍 監測和調試

### 監測指標

```python
class HeartbeatMetrics:
    def __init__(self):
        self.total_heartbeats = 0
        self.failed_heartbeats = 0
        self.timeout_count = 0
        self.recovery_count = 0
        self.latencies = []
    
    def record_heartbeat(self, latency):
        self.total_heartbeats += 1
        self.latencies.append(latency)
    
    def record_failure(self):
        self.failed_heartbeats += 1
    
    def get_stats(self):
        return {
            "total": self.total_heartbeats,
            "failures": self.failed_heartbeats,
            "failure_rate": self.failed_heartbeats / max(1, self.total_heartbeats),
            "avg_latency": sum(self.latencies) / len(self.latencies),
            "max_latency": max(self.latencies),
            "min_latency": min(self.latencies),
            "timeouts": self.timeout_count,
            "recoveries": self.recovery_count
        }
```

### 日誌示例

```
# 正常運行
2026-03-29 10:00:05 INFO  Agent agent-001 發送心跳 (序列: 42)
2026-03-29 10:00:05 INFO  Monitor 收到心跳 (延遲: 2ms)

# 檢測到超時
2026-03-29 10:00:15 WARN  Agent agent-001 超時 (6.1s > 6.0s), 狀態: SUSPECTED

# 確認故障
2026-03-29 10:00:21 ERROR Agent agent-001 確認故障 (連續 3 次超時), 狀態: DEAD

# 觸發故障轉移
2026-03-29 10:00:21 ERROR 啟動故障轉移:
                           - 停止分配任務到 agent-001
                           - 啟動備用 Agent agent-001-backup
                           - 發送告警通知

# 恢復
2026-03-29 10:00:45 INFO  Agent agent-001 恢復信號收到, 狀態: RECOVERED
```

---

## 🧪 測試檢查清單

### 功能測試

```python
def test_heartbeat_system():
    """測試心跳系統"""
    
    # 1. 正常情況
    test_normal_operation()
    
    # 2. Agent 宕機
    test_agent_crash()
    
    # 3. 網絡延遲
    test_network_latency()
    
    # 4. 網絡抖動
    test_network_jitter()
    
    # 5. 故障恢復
    test_failure_recovery()
    
    # 6. 批量失敗
    test_batch_failure()
    
    # 7. 誤判恢復
    test_false_positive()
    
    # 8. 長時間穩定性
    test_long_term_stability()
```

### 性能測試

```bash
# 測試 1: 吞吐量
python benchmark_throughput.py --agents 100 --duration 300

# 測試 2: 延遲
python benchmark_latency.py --agents 50 --heartbeat-interval 5

# 測試 3: 內存使用
python benchmark_memory.py --agents 1000

# 測試 4: CPU 使用
python benchmark_cpu.py --agents 200
```

---

## 📚 參考資源

| 資源 | 用途 |
|------|------|
| Raft 一致性 | https://raft.github.io/ |
| Google Chubby | 分布式鎖和心跳 |
| ZooKeeper | 分布式協調 |
| Consul | Service Mesh 實現 |
| etcd | KV 存儲 + 心跳 |
| Kubernetes Probe | 容器健康檢查 |

---

## 🎓 總結

心跳系統是分布式系統的基石：

1. **正確設計** - 選擇合適的間隔和超時
2. **多層驗證** - 避免誤判
3. **完善監測** - 及時發現問題
4. **自動恢復** - 減少人工干預
5. **充分測試** - 驗證各種場景

通過遵循這些最佳實踐，可以建立一個高可用、快速故障轉移的分布式系統。

---

**文檔版本**: 1.0  
**最後更新**: 2026-03-29
