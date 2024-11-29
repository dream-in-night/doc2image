#!/bin/bash
# 判断参数数量
if [ $# -eq 1 ]; then
  im=$1
  echo $im
else
  echo "请输入图像或url路径作为参数"
  exit 1
fi

# 判断是不是网络图像,网络图像必须包含http
if echo "$im" | grep -q "http"; then
  # 网络图像
  im=$im
else
  # 本地图像
  im=$(cygpath -w "$im")

echo "本地图片识别"
curl -X POST \
  http://116.63.46.175:38081/v1/dcg_tailocr_v1 \
  -H "Authorization: Bearer dcg-MTQ2MDRkYWRmNzRjMDg0ZjZmNTc3YTliMWM0YzYwYmVlZDE=" \
  -F "userid=dcg-kb" \
  -F "client_id=dcg-red-list" \
  -F "return_box=False" \
  -F "sort_line=False" \
  -F "remake_box_ch:True" \
  -F "file=@${im}"
echo ""


echo "网络图片识别"
imurl=https://pic2.zhimg.com/v2-050caf7c63d8ca0a1cbd744cfd664c8d_r.jpg
curl -X POST \
  http://116.63.46.175:38081/v1/dcg_tailocr_v1_url \
  -H "Authorization: Bearer dcg-MTQ2MDRkYWRmNzRjMDg0ZjZmNTc3YTliMWM0YzYwYmVlZDE=" \
  -d "userid=dcg-kb" \
  -d "return_box=False" \
  -d "client_id=dcg-red-list" \
  -d "sort_line=False" \
  -d "image_url=${im}"
echo ""
