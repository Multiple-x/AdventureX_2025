/*
 * shitbro_webservo.ino
 * - Web端控制两个SCServo总线舵机（同步同一角度）
 */
#include <Arduino.h>
#include <WiFi.h>
#include <esp_wifi.h>
#include <esp_http_server.h>
#include <WebSocketsServer.h>
#include <SCServo.h>

/****************** WiFi 配置 *****************/
#define WIFI_SSID "hupan1"
#define WIFI_PASS ""
#define WIFI_TIMEOUT 30000

/****************** SCServo 配置 *****************/
#define SERVO_NUM 2
SMS_STS st;
byte ID[SERVO_NUM] = {1, 2};
u16 Speed[SERVO_NUM] = {1500, 1500};
byte ACC[SERVO_NUM] = {50, 50};
s16 Pos[SERVO_NUM] = {2048, 2048};
#define S_RXD 44
#define S_TXD 43



/****************** WebSocket *****************/
WebSocketsServer webSocket(81);
volatile bool websocket_connected = false;
String device_ip = "";

/****************** HTTP Server *****************/
static httpd_handle_t camera_httpd = NULL;
int current_servo_angle = 0;

/****************** 演示模式 *****************/
bool demo_mode = false;
unsigned long last_demo_time = 0;
const unsigned long demo_interval = 200; // 演示间隔200ms





/****************** WiFi 连接 *****************/
bool connectWiFi(){
  WiFi.mode(WIFI_STA);
  WiFi.disconnect(true);
  delay(500);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  unsigned long start = millis();
  while(WiFi.status() != WL_CONNECTED && millis() - start < WIFI_TIMEOUT){
    delay(200);
  }
  if(WiFi.status() == WL_CONNECTED){
    device_ip = WiFi.localIP().toString();
    return true;
  }
  Serial.println("[WiFi] FAILED");
  return false;
}

/****************** WebSocket事件 *****************/
void set_angle(int8_t angle) {
  if (angle >= 80) angle = 80;
  else if (angle <= 0) angle = 0;
  current_servo_angle = angle;
  Pos[0] = 2048 -  (s16)(11.37 * angle);
  Pos[1] = 2048 +  (s16)(11.37 * angle);
  st.SyncWritePosEx(ID, SERVO_NUM, Pos, Speed, ACC);
}

void processCommand(String command) {
  command.trim();
  if(command.startsWith("SERVO:")) {
    int angle = command.substring(6).toInt();
    set_angle(angle);
    Serial.printf("🔧 Web控制舵机角度: %d°\n", angle);
    return;
  }
  // 兼容原有命令
  command.toUpperCase();
  if(command == "IDLE") {
    set_angle(0);
    Serial.println("🔧 舵机回中");
    return;
  }
  if(command == "DEMO_START") {
    demo_mode = true;
    Serial.println("🎭 演示模式启动 - 开始随机角度开合");
    return;
  }
  if(command == "DEMO_STOP") {
    demo_mode = false;
    set_angle(0);
    Serial.println("🎭 演示模式停止 - 嘴巴闭合");
    return;
  }
}

void webSocketEvent(uint8_t num, WStype_t type, uint8_t * payload, size_t length){
  switch(type){
    case WStype_DISCONNECTED:
      websocket_connected = false;
      break;
    case WStype_CONNECTED:
      websocket_connected = true;
      break;
    case WStype_TEXT:{
      String cmd = String((char*)payload, length);
      processCommand(cmd);
      break;}
    default: break;
  }
}

void initWebSocket(){
  webSocket.begin();
  webSocket.onEvent(webSocketEvent);
}



static esp_err_t index_handler(httpd_req_t *req){
  const char *html = "<!DOCTYPE html><html><head><meta charset='utf-8'><title>shitbro WebServo API</title></head><body>"
                     "<h2>shitbro WebServo API</h2>"
                     "<h3>舵机控制</h3>"
                     "<input type='range' id='servo' min='0' max='80' value='0' oninput='updateServo()'> "
                     "<span id='angle'>0</span>° "
                     "<div style='margin-top:10px;'>"
                     "<button onclick='setAngle(0)'>0°</button> "
                     "<button onclick='setAngle(40)'>40°</button> "
                     "<button onclick='setAngle(80)'>80°</button>"
                     "</div>"
                     "<h3>🎭 演示模式</h3>"
                     "<div style='margin-top:10px;'>"
                     "<button onclick='startDemo()' style='background: #4CAF50; color: white; padding: 10px; margin: 5px;'>开始演示</button> "
                     "<button onclick='stopDemo()' style='background: #f44336; color: white; padding: 10px; margin: 5px;'>停止演示</button>"
                     "</div>"
                     "<p><em>演示模式会随机控制嘴巴开合角度 (5-50度)</em></p>"
                     "<h3>API 接口</h3>"
                     "<p><strong>设置舵机角度:</strong> GET /api/servo?angle=角度值</p>"
                     "<p><strong>获取舵机状态:</strong> GET /api/status</p>"
                     "<p><strong>舵机回中:</strong> GET /api/servo/center</p>"
                     "<p><strong>启动演示:</strong> GET /api/demo/start</p>"
                     "<p><strong>停止演示:</strong> GET /api/demo/stop</p>"
                     "<div style='margin-top:20px;'>"
                     "<h4>测试API:</h4>"
                     "<button onclick='testAPI(0)'>API设置0°</button> "
                     "<button onclick='testAPI(40)'>API设置40°</button> "
                     "<button onclick='testAPI(80)'>API设置80°</button> "
                     "<button onclick='getStatus()'>获取状态</button>"
                     "</div>"
                     "<div id='apiResult' style='margin-top:10px; padding:10px; background:#f0f0f0;'></div>"
                     "<script>\n"
                     "let ws=new WebSocket('ws://'+location.hostname+':81');\n"
                     "let lastAngle = 0;\n"
                     "let updateTimer = null;\n"
                     "function updateServo(){\n"
                     "  let angle = document.getElementById('servo').value;\n"
                     "  document.getElementById('angle').textContent = angle + '°';\n"
                     "  if(updateTimer) clearTimeout(updateTimer);\n"
                     "  updateTimer = setTimeout(() => {\n"
                     "    if(angle != lastAngle){\n"
                     "      ws.send('SERVO:' + angle);\n"
                     "      lastAngle = angle;\n"
                     "    }\n"
                     "  }, 100);\n"
                     "}\n"
                     "function setAngle(angle){\n"
                     "  document.getElementById('servo').value = angle;\n"
                     "  document.getElementById('angle').textContent = angle + '°';\n"
                     "  ws.send('SERVO:' + angle);\n"
                     "  lastAngle = angle;\n"
                     "}\n"
                     "function startDemo(){\n"
                     "  ws.send('DEMO_START');\n"
                     "  document.getElementById('apiResult').innerHTML = '🎭 演示模式已启动';\n"
                     "}\n"
                     "function stopDemo(){\n"
                     "  ws.send('DEMO_STOP');\n"
                     "  document.getElementById('apiResult').innerHTML = '🎭 演示模式已停止';\n"
                     "}\n"
                     "async function testAPI(angle){\n"
                     "  try{\n"
                     "    const response = await fetch('/api/servo?angle=' + angle);\n"
                     "    const result = await response.text();\n"
                     "    document.getElementById('apiResult').innerHTML = 'API响应: ' + result;\n"
                     "  }catch(e){\n"
                     "    document.getElementById('apiResult').innerHTML = 'API错误: ' + e;\n"
                     "  }\n"
                     "}\n"
                     "async function getStatus(){\n"
                     "  try{\n"
                     "    const response = await fetch('/api/status');\n"
                     "    const result = await response.text();\n"
                     "    document.getElementById('apiResult').innerHTML = '状态: ' + result;\n"
                     "  }catch(e){\n"
                     "    document.getElementById('apiResult').innerHTML = 'API错误: ' + e;\n"
                     "  }\n"
                     "}\n"
                     "</script>"
                     "</body></html>";
  httpd_resp_set_type(req, "text/html");
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  return httpd_resp_send(req, html, strlen(html));
}

/****************** API 处理函数 *****************/
static esp_err_t servo_api_handler(httpd_req_t *req) {
  char query[50];
  char param[10];
  
  // 获取查询参数
  if (httpd_req_get_url_query_len(req) > 0) {
    httpd_req_get_url_query_str(req, query, sizeof(query));
    if (httpd_query_key_value(query, "angle", param, sizeof(param)) == ESP_OK) {
      int angle = atoi(param);
      set_angle(angle);
      Serial.printf("🔧 API设置舵机角度: %d°\n", angle);
      
      // 返回JSON响应
      char response[100];
      snprintf(response, sizeof(response), "{\"status\":\"success\",\"angle\":%d,\"message\":\"舵机角度设置为%d度\"}", angle, angle);
      httpd_resp_set_type(req, "application/json");
      httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
      return httpd_resp_send(req, response, strlen(response));
    }
  }
  
  // 如果没有角度参数，返回错误
  const char* error_response = "{\"status\":\"error\",\"message\":\"缺少angle参数\"}";
  httpd_resp_set_type(req, "application/json");
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  return httpd_resp_send(req, error_response, strlen(error_response));
}

static esp_err_t servo_center_handler(httpd_req_t *req) {
  set_angle(0);
  Serial.println("🔧 API舵机回中");
  
  const char* response = "{\"status\":\"success\",\"angle\":0,\"message\":\"舵机已回中\"}";
  httpd_resp_set_type(req, "application/json");
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  return httpd_resp_send(req, response, strlen(response));
}

static esp_err_t status_api_handler(httpd_req_t *req) {
  char response[200];
  snprintf(response, sizeof(response), 
    "{\"status\":\"success\",\"data\":{\"current_angle\":%d,\"wifi_connected\":%s,\"ip_address\":\"%s\",\"servo_count\":%d,\"demo_mode\":%s}}", 
    current_servo_angle, 
    WiFi.status() == WL_CONNECTED ? "true" : "false",
    device_ip.c_str(),
    SERVO_NUM,
    demo_mode ? "true" : "false"
  );
  
  httpd_resp_set_type(req, "application/json");
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  return httpd_resp_send(req, response, strlen(response));
}

static esp_err_t demo_start_handler(httpd_req_t *req) {
  demo_mode = true;
  Serial.println("🎭 API启动演示模式 - 开始随机角度开合");
  
  const char* response = "{\"status\":\"success\",\"demo_mode\":true,\"message\":\"演示模式已启动\"}";
  httpd_resp_set_type(req, "application/json");
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  return httpd_resp_send(req, response, strlen(response));
}

static esp_err_t demo_stop_handler(httpd_req_t *req) {
  demo_mode = false;
  set_angle(0);
  Serial.println("🎭 API停止演示模式 - 嘴巴闭合");
  
  const char* response = "{\"status\":\"success\",\"demo_mode\":false,\"message\":\"演示模式已停止\"}";
  httpd_resp_set_type(req, "application/json");
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  return httpd_resp_send(req, response, strlen(response));
}

void startWebServer(){
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = 80;
  config.max_uri_handlers = 8;
  config.stack_size = 16384;
  config.task_priority = 5;
  config.core_id = 0;
  config.max_open_sockets = 4;
  config.lru_purge_enable = true;
  if(httpd_start(&camera_httpd, &config) == ESP_OK){
    httpd_uri_t index_uri      = { .uri="/",              .method=HTTP_GET, .handler=index_handler,      .user_ctx=NULL };
    httpd_uri_t servo_api_uri  = { .uri="/api/servo",     .method=HTTP_GET, .handler=servo_api_handler,  .user_ctx=NULL };
    httpd_uri_t center_api_uri = { .uri="/api/servo/center", .method=HTTP_GET, .handler=servo_center_handler, .user_ctx=NULL };
    httpd_uri_t status_api_uri = { .uri="/api/status",    .method=HTTP_GET, .handler=status_api_handler, .user_ctx=NULL };
    httpd_uri_t demo_start_uri = { .uri="/api/demo/start", .method=HTTP_GET, .handler=demo_start_handler, .user_ctx=NULL };
    httpd_uri_t demo_stop_uri  = { .uri="/api/demo/stop",  .method=HTTP_GET, .handler=demo_stop_handler,  .user_ctx=NULL };
    
    httpd_register_uri_handler(camera_httpd, &index_uri);
    httpd_register_uri_handler(camera_httpd, &servo_api_uri);
    httpd_register_uri_handler(camera_httpd, &center_api_uri);
    httpd_register_uri_handler(camera_httpd, &status_api_uri);
    httpd_register_uri_handler(camera_httpd, &demo_start_uri);
    httpd_register_uri_handler(camera_httpd, &demo_stop_uri);
  } else {
    Serial.println("[HTTP] start failed");
  }
}



/****************** 主程序 *****************/
void setup(){
  Serial.begin(115200);
  delay(300);
  Serial.println("🔧 shitbro_webservo 启动中...");
  
  // 初始化随机数种子
  randomSeed(analogRead(0));
  
  // 舵机串口初始化
  Serial.println("🔧 初始化舵机串口...");
  Serial1.begin(1000000, SERIAL_8N1, S_RXD, S_TXD);
  st.pSerial = &Serial1;
  
  // 舵机自检
  Serial.println("🔍 检查舵机连接状态...");
  for (int i = 0; i < SERVO_NUM; i++) {
    if (st.Ping(ID[i]) != -1) {
      Serial.printf("✅ 舵机ID%d 连接正常\n", ID[i]);
    } else {
      Serial.printf("❌ 舵机ID%d 无响应\n", ID[i]);
    }
  }
  
  // WiFi连接
  Serial.println("📶 连接WiFi...");
  if(connectWiFi()) {
    Serial.printf("✅ WiFi连接成功! IP地址: %s\n", device_ip.c_str());
    Serial.printf("📡 WiFi信号强度: %ddBm\n", WiFi.RSSI());
  } else {
    Serial.println("❌ WiFi连接失败，离线模式");
  }
  
  // HTTP + WebSocket服务器
  if(WiFi.status()==WL_CONNECTED){
    Serial.println("🌐 启动Web服务器...");
    startWebServer();
    initWebSocket();
    Serial.println("✅ Web服务器启动成功");
    Serial.printf("📱 访问地址: http://%s\n", device_ip.c_str());
  }
  
  // 舵机回中
  Serial.println("🔧 舵机回中...");
  set_angle(0);
  
  Serial.println("🎉 系统初始化完成!");
  Serial.println("----------------------------------------");
  Serial.printf("📱 Web控制界面: http://%s\n", device_ip.c_str());
  Serial.println("🔧 舵机控制范围: 0-80度");
  Serial.println("🎭 演示模式: 随机角度开合");
  Serial.println("----------------------------------------");
}

void loop(){
  webSocket.loop();
  runDemoMode(); // 运行演示模式
  vTaskDelay(10 / portTICK_PERIOD_MS);
} 

/****************** 演示模式逻辑 *****************/
void runDemoMode() {
  if (!demo_mode) return;
  
  unsigned long current_time = millis();
  if (current_time - last_demo_time >= demo_interval) {
    // 生成随机嘴巴开合角度 (5-50度，模拟说话时的开合)
    int random_angle = random(5, 51);
    set_angle(random_angle);
    
    Serial.printf("🎭 演示模式 - 嘴巴角度: %d°\n", random_angle);
    
    last_demo_time = current_time;
  }
} 