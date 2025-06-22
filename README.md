# AirStatus for Linux

Check your AirPods battery level on Linux — now in real time via WebSocket!

## 🔍 What is it?

This is a Python 3+ WebSocket server, forked from [`faglo/AirStatus`](https://github.com/faglo/AirStatus), that scans for your AirPods using Bluetooth Low Energy and streams battery and charging information as JSON in real time through a WebSocket connection.

Originally a terminal script, this version was upgraded to serve clients over the web using FastAPI.

---

## 🚀 Features

- 🔋 Real-time AirPods battery and charging status
- 📡 WebSocket endpoint for easy integration with web or mobile apps
- 📦 JSON format output
- ⚙️ Configurable update interval

---

## ⚙️ Requirements

```bash
pip install -r requirements.txt

```
