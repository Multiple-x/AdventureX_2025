# shitbro WebServo API 文档

## 📋 概述

shitbro WebServo API 是一个基于 ESP32-S3 的舵机控制 RESTful API 服务。通过 HTTP 请求可以远程控制两个 SCServo 总线舵机，支持实时角度调节和状态查询。

## 🔧 硬件要求

- **主控板**: ESP32-S3 XIAO Sense
- **舵机**: SCServo 总线舵机 (ID: 1, 2)
- **连接方式**: 
  - 信号线: GPIO43 (TX), GPIO44 (RX)
  - 电源: 5V, GND
- **通信协议**: SCServo 总线协议 (1000000 baud)

## 🌐 网络配置

- **WiFi模式**: Station 模式
- **SSID**: `hupan1` (可在代码中修改)
- **IP地址**: 自动获取 (DHCP)
- **端口**: 80 (HTTP), 81 (WebSocket)

## 📡 API 接口

### 基础信息

- **协议**: HTTP/1.1
- **数据格式**: JSON
- **字符编码**: UTF-8
- **CORS**: 支持跨域请求

### 1. 设置舵机角度

**接口地址**: `GET /api/servo`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 | 取值范围 |
|--------|------|------|------|----------|
| angle | int | 是 | 舵机角度 | 0-80 |

**请求示例**:
```bash
curl "http://192.168.1.100/api/servo?angle=45"
```

**响应格式**:
```json
{
  "status": "success",
  "angle": 45,
  "message": "舵机角度设置为45度"
}
```

**错误响应**:
```json
{
  "status": "error",
  "message": "缺少angle参数"
}
```

### 2. 舵机回中

**接口地址**: `GET /api/servo/center`

**请求参数**: 无

**请求示例**:
```bash
curl "http://192.168.1.100/api/servo/center"
```

**响应格式**:
```json
{
  "status": "success",
  "angle": 0,
  "message": "舵机已回中"
}
```

### 3. 获取系统状态

**接口地址**: `GET /api/status`

**请求参数**: 无

**请求示例**:
```bash
curl "http://192.168.1.100/api/status"
```

**响应格式**:
```json
{
  "status": "success",
  "data": {
    "current_angle": 45,
    "wifi_connected": true,
    "ip_address": "192.168.1.100",
    "servo_count": 2
  }
}
```

## 🔌 WebSocket 接口

### 连接信息

- **地址**: `ws://ESP32_IP:81`
- **协议**: WebSocket

### 消息格式

**发送舵机控制命令**:
```
SERVO:角度值
```

**示例**:
```
SERVO:60
```

## 📱 Web 控制界面

访问 `http://ESP32_IP` 可获得图形化控制界面，包含：

- 实时滑块控制 (0-80度)
- 快捷按钮 (0°, 40°, 80°)
- API 测试功能
- 实时响应显示

## 🚀 使用示例

### Python 示例

```python
import requests
import json

# 基础配置
base_url = "http://192.168.1.100"

# 设置舵机角度
def set_servo_angle(angle):
    url = f"{base_url}/api/servo?angle={angle}"
    response = requests.get(url)
    return response.json()

# 舵机回中
def center_servo():
    url = f"{base_url}/api/servo/center"
    response = requests.get(url)
    return response.json()

# 获取状态
def get_status():
    url = f"{base_url}/api/status"
    response = requests.get(url)
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 设置舵机到30度
    result = set_servo_angle(30)
    print("设置角度:", result)
    
    # 获取当前状态
    status = get_status()
    print("系统状态:", status)
    
    # 舵机回中
    center = center_servo()
    print("回中结果:", center)
```

### JavaScript 示例

```javascript
// 基础配置
const baseUrl = 'http://192.168.1.100';

// 设置舵机角度
async function setServoAngle(angle) {
    try {
        const response = await fetch(`${baseUrl}/api/servo?angle=${angle}`);
        const data = await response.json();
        console.log('设置角度结果:', data);
        return data;
    } catch (error) {
        console.error('设置角度失败:', error);
    }
}

// 舵机回中
async function centerServo() {
    try {
        const response = await fetch(`${baseUrl}/api/servo/center`);
        const data = await response.json();
        console.log('回中结果:', data);
        return data;
    } catch (error) {
        console.error('回中失败:', error);
    }
}

// 获取状态
async function getStatus() {
    try {
        const response = await fetch(`${baseUrl}/api/status`);
        const data = await response.json();
        console.log('系统状态:', data);
        return data;
    } catch (error) {
        console.error('获取状态失败:', error);
    }
}

// WebSocket 连接
function connectWebSocket() {
    const ws = new WebSocket(`ws://${baseUrl.replace('http://', '')}:81`);
    
    ws.onopen = () => {
        console.log('WebSocket 连接成功');
    };
    
    ws.onmessage = (event) => {
        console.log('收到消息:', event.data);
    };
    
    ws.onclose = () => {
        console.log('WebSocket 连接关闭');
    };
    
    return ws;
}

// 使用示例
const ws = connectWebSocket();

// 通过 WebSocket 设置角度
function setAngleViaWebSocket(angle) {
    ws.send(`SERVO:${angle}`);
}
```

### Node.js 示例

```javascript
const axios = require('axios');

class ShitbroServoAPI {
    constructor(baseUrl = 'http://192.168.1.100') {
        this.baseUrl = baseUrl;
    }
    
    // 设置舵机角度
    async setAngle(angle) {
        try {
            const response = await axios.get(`${this.baseUrl}/api/servo?angle=${angle}`);
            return response.data;
        } catch (error) {
            throw new Error(`设置角度失败: ${error.message}`);
        }
    }
    
    // 舵机回中
    async center() {
        try {
            const response = await axios.get(`${this.baseUrl}/api/servo/center`);
            return response.data;
        } catch (error) {
            throw new Error(`舵机回中失败: ${error.message}`);
        }
    }
    
    // 获取状态
    async getStatus() {
        try {
            const response = await axios.get(`${this.baseUrl}/api/status`);
            return response.data;
        } catch (error) {
            throw new Error(`获取状态失败: ${error.message}`);
        }
    }
}

// 使用示例
async function main() {
    const api = new ShitbroServoAPI();
    
    try {
        // 获取初始状态
        const status = await api.getStatus();
        console.log('初始状态:', status);
        
        // 设置舵机角度
        const result = await api.setAngle(50);
        console.log('设置角度结果:', result);
        
        // 舵机回中
        const center = await api.center();
        console.log('回中结果:', center);
        
    } catch (error) {
        console.error('操作失败:', error.message);
    }
}

main();
```

## ⚠️ 注意事项

### 1. 角度限制
- 舵机角度范围: 0-80度
- 超出范围会自动限制到边界值

### 2. 响应时间
- API 响应时间: < 100ms
- 舵机执行时间: 取决于角度变化量

### 3. 并发控制
- 支持多个客户端同时连接
- 建议控制请求频率，避免舵机抖动

### 4. 错误处理
- 网络断开时返回连接错误
- 参数错误时返回 JSON 格式错误信息

## 🔧 故障排除

### 常见问题

1. **舵机无响应**
   - 检查电源连接
   - 确认舵机ID设置
   - 检查信号线连接

2. **API 请求失败**
   - 确认 ESP32 IP 地址
   - 检查 WiFi 连接状态
   - 验证网络连通性

3. **角度控制不准确**
   - 检查舵机机械结构
   - 确认电源电压稳定
   - 验证舵机型号兼容性

### 调试信息

串口输出包含详细的调试信息：
```
🔧 shitbro_webservo 启动中...
🔧 初始化舵机串口...
🔍 检查舵机连接状态...
✅ 舵机ID1 连接正常
✅ 舵机ID2 连接正常
📶 连接WiFi...
✅ WiFi连接成功! IP地址: 192.168.1.100
🌐 启动Web服务器...
✅ Web服务器启动成功
🔧 API设置舵机角度: 45°
```

## 📄 版本信息

- **版本**: 1.0.0
- **开发平台**: Arduino Framework
- **目标硬件**: ESP32-S3 XIAO Sense
- **舵机库**: SCServo
- **Web服务器**: esp_http_server
- **WebSocket**: WebSocketsServer

## 📞 技术支持

如有问题，请检查：
1. 硬件连接是否正确
2. WiFi 配置是否正确
3. 串口输出的错误信息
4. API 请求格式是否正确

---

*本文档适用于 shitbro WebServo API v1.0.0* 