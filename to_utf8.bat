@echo off
setlocal enabledelayedexpansion

rem 检查是否传递了目录路径参数
if "%1"=="" (
    echo 请提供文件夹路径作为参数!
    echo 例如: convert_to_utf8.bat C:\path\to\txt\files
    pause
    exit /b
)

rem 设置编码页为 UTF-8
chcp 65001

rem 获取传入的文件夹路径
set "folderPath=%1"

rem 遍历指定目录及其所有子目录下的所有 .txt 文件
for /r "%folderPath%" %%f in (*.txt) do (
    echo 正在转换 %%f 到 UTF-8...
    type "%%f" > "%%f.new"
    move /Y "%%f.new" "%%f"
)

echo 转换完成!
pause
