# xihu_demo

Jetson AGX ORIN (Ubuntu 22.04 + ROS2 Humble) 场景下的最小闭环工程：

- 前端统一管理页面（模型开关 + 阈值 + 文本 + 状态）
- 后端统一 API（检测决策 + 语音播报 + 停止 + 状态）
- 后端内部调用本地常驻 YOLO 服务

## 目录结构

```text
backend/
  app/
    main.py
    models.py
    services/
      decision.py
      yolo_caller.py
      speech_adapter.py
frontend/
  index.html
  main.js
  styles.css
```

## 启动

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

浏览器访问：

- `http://127.0.0.1:8000/`

## API 清单

- `POST /api/detect/person-decision`
- `POST /api/speech/play`
- `POST /api/speech/stop`
- `GET /api/speech/status`
- `POST /api/arm/run-trajectory`

## 环境变量

- `YOLO_SERVICE_URL`：本地 YOLO 服务地址（默认 `http://127.0.0.1:8090`）

## 集成说明

- `SpeechModuleAdapter._do_speak_once` 目前是模拟播报耗时；实际部署时替换为机器人语音模块调用。
- `YoloServiceCaller.fetch_latest_detections` 默认调用 `GET /detect/latest`；按你们已有 YOLO 服务协议改造即可。
- 新增机械臂轨迹控制接口：后端通过 socket 连接前端输入的机械臂 IP/端口，并发送  
  `{"command":"set_run_trajectory_file","name":"轨迹名"}`。
