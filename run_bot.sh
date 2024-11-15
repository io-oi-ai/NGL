#!/bin/bash

# 设置日志文件路径
LOG_FILE="/path/to/your/bot.log"

# 确保日志文件存在
touch $LOG_FILE

# 定义启动bot的函数
start_bot() {
    echo "$(date): 启动bot..." >> $LOG_FILE
    /path/to/your/python /path/to/your/bot.py >> $LOG_FILE 2>&1
}

# 检查bot是否在运行
is_bot_running() {
    pgrep -f "python /path/to/your/bot.py" > /dev/null
}

# 主循环
while true; do
    if ! is_bot_running; then
        echo "$(date): Bot不在运行状态,重新启动..." >> $LOG_FILE
        start_bot &
    fi
    sleep 60
done