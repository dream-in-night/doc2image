import copy
import shutil

import requests
import os
from tqdm import tqdm
import time
import numpy as np
from ultralytics.utils.plotting import colors, Annotator
import sys
import os.path as osp
import cv2
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from io import BytesIO
from ultralytics.utils.plotting import colors, Annotator
from PIL import Image
import json
# 设置中文字体
font_path = '/data/liyaze/Fonts/STSONG.TTF'  # 替换为你电脑上的中文字体路径
font_path = r'c:/Fonts/STSONG.TTF'  # 替换为你电脑上的中文字体路径
fm.fontManager.addfont(font_path)
plt.rcParams['font.family'] = 'STSONG' 

headers = {"Authorization": "Bearer dcg-MTQ2MDRkYWRmNzRjMDg0ZjZmNTc3YTliMWM0YzYwYmVlZDE="}

labels = ["正文","标题","插图","插图注释","表格","表格注释","页眉","页脚","参考文献","公式","文本注释","章节标题","目录","作者信息","题目","二维码","广告","封面","序言","出版信息", "题型", "后记", "附录", "答案","侧边"]

def layout(file_path, repost=False):
    assert osp.exists(file_path), file_path
    layout_file_path = Path(file_path).with_suffix('.json')
    if layout_file_path.exists() and repost:
        f = open(layout_file_path, 'r')
        js = eval(f.read())
        f.close()
        return js
    else:
        params = {
        "userid": "dcg-kb",
        "client_id": "dcg-red-list"
        }  
        file = open(file_path, "rb")
        layout_response = requests.post("http://122.9.78.254:30020/v1/dcg_layout", files={"file": file}, data=params, headers=headers, timeout=100)
        if layout_response.status_code != 200:
            print(f"版面分析请求失败, file_path: {file_path}")
            return None
        js = layout_response.json()
        f = open(layout_file_path, 'w')
        json.dump(js, f, ensure_ascii=False, indent=4)
        f.close()
        return js
def create_image_with_text_and_latex(text, size_h):
    size_h = min(size_h,30)
    # 创建一个新的图形
    plt.figure(figsize=(len(text)*0.5, 1))  # 调整大小以适应文本
    # 绘制文本和公式
    plt.text(0, 0.5, f"{text}", fontsize=size_h, ha='center', va='center')
    plt.axis('off')  # 隐藏坐标轴
    # 将图形保存到内存中的字节流
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    buf.seek(0)  # 将指针移动到字节流的开始位置
    # 使用 OpenCV 读取字节流
    img_array = np.frombuffer(buf.getvalue(), np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    plt.close()  # 关闭图形窗口以释放内存
    return img

OCR_API_URL0 = "http://116.63.46.175:38080/v1/dcg_tailocr_v1" # v0
OCR_API_URL1 = "http://116.63.46.175:38081/v1/dcg_tailocr_v1" # v1
OCR_API_URL_test = "http://116.63.46.175:38090/v1/dcg_tailocr_v1" # v1
def remake_boxes(dt_boxes, pagew:int, pageh:int):
    # 正文里，一行字没有检测好, 本来是一个框，检测为了左右两三个框， 需要合并为1个框
    if len(dt_boxes)<=1:
        return dt_boxes
    dt_boxes_all = copy.deepcopy(dt_boxes)
    dt_boxes_all2 = []
    while len(dt_boxes_all)>0:
        dt_box = dt_boxes_all.pop(0)
        boxes = [dt_box]
        b1_y1, b1_y2, b1_h, b1_yc = dt_box[1], dt_box[3], dt_box[3]-dt_box[1], (dt_box[3]+dt_box[1])/2
        del_inds = []
        for i in range(len(dt_boxes_all)):
            dt_box_ = dt_boxes_all[i]
            b2_y1, b2_y2, b2_h, b2_yc = dt_box_[1], dt_box_[3], dt_box_[3]-dt_box_[1], (dt_box_[3]+dt_box_[1])/2
            if max(b1_h, b2_h)/min(b1_h, b2_h)>3:
                continue
            if b2_yc<b1_y1 or b2_yc>b1_y2:
                continue
            if b1_yc<b2_y1 or b1_yc>b2_y2:
                continue
            if b2_y2<b1_y1 or b1_y2<b2_y1:
                continue
            boxes.append(dt_box_)
            del_inds.append(i)
        dt_boxes_all = [x for i,x in enumerate(dt_boxes_all) if i not in del_inds]
        boxes2 = []
        if len(boxes)>1:
            xs = [dt_box[0] for dt_box in boxes]
            x_inds = np.argsort(xs)
            boxes = [boxes[i] for i in x_inds]
            boxes2 = [boxes[0]]
            num = 1
            for box in boxes[1:]:
                width = box[2]-box[0]
                pre_width = boxes2[-1][2]-boxes2[-1][0]
                interval = box[0]-boxes2[-1][2]
                if interval<min(pre_width, width)*4:
                    boxes2[-1][1] = min(boxes2[-1][1], box[1])
                    boxes2[-1][3] = max(boxes2[-1][3], box[3])
                    boxes2[-1][2] = box[2]
                    num += 1
                else:
                    boxes2.append(box)
        if len(boxes2)>0:
            for b in boxes2:
                if pagew-b[2]<30:
                    b[2] = pagew
                dt_boxes_all2.append(b)
        else:
            dt_boxes_all2.append(dt_box)
    return dt_boxes_all2
def rec(file_path, remake_box_ch=False, url=OCR_API_URL1):
    params = {
    "userid": "dcg-kb",
    "client_id": "dcg-red-list",
    "sort_line": True,
    "return_box": True,
    "remake_box_ch":remake_box_ch,
    }
    im_ori = Image.open(file_path).convert('RGB')
    annotator0 = Annotator(im_ori, line_width=2, pil=True, font_size=20, example='中午')
    file2 = open(file_path, "rb")
    ocr_response = requests.post(url, files={"file": file2}, data=params, headers=headers, timeout=80)
    if ocr_response.status_code == 200:
        ocr_res_json = ocr_response.json()
        ocr_text = ocr_res_json['data']
        dt_boxes = ocr_res_json['boxes']
        has_text = False
        for i, (box_line, text) in enumerate(zip(dt_boxes, ocr_text)):
            if len(box_line)==0:
                continue
            has_text = True
            break
            box_line = list(map(int, box_line))
            annotator0.box_label(tuple(box_line), label=f'{text}', color=colors(0, True))
        # return annotator0.result()[:,:,::-1]
        if not has_text:
            return im_ori
    else:
        print(f'{url} ocr error: ',ocr_response.status_code)
def rec_layout(file_path, remake_box_ch=False, url=OCR_API_URL_test):
    params = {
    "userid": "dcg-kb",
    "client_id": "dcg-red-list",
    "sort_line": True,
    "return_box": True,
    "remake_box_ch":remake_box_ch,
    }  
    layout_data = layout(file_path)
    im_ori = cv2.imread(file_path)
    im_gray = np.zeros(im_ori.shape) + 255
    annotator0 = Annotator(im_ori, line_width=2, pil=True, font_size=20, example='中午')
    if not layout_data:
        return im_ori
    # {'errorCode': 0, 'msg': '识别成功', 
    # 'data': {'Ids_Scores_boxes': [[[17], 0.5592268109321594, [0.0, 26.150877247419537, 807.1222331115198, 1353.9595463215821]]], 'boxes_num': 1, 'reader_circle': [0], 'ocr_info': ['封面'], 'struc_info': {'text': {'text_0': {'title': [], 'text': [0]}}}}}
    if not 'data' in layout_data:
        return im_ori
    output_text = ''
    for k, data in enumerate(layout_data['data']['Ids_Scores_boxes']):
        lb = labels[data[0][0]]
        # if lb not in ['正文', '标题', '页眉', '页脚']:
        if lb not in ['正文']:
            continue
        print(f'lb: {lb}')
        output_text += lb + '\n'
        box_struct = data[2]
        box_struct = list(map(int, box_struct))
        annotator0.box_label(box_struct, label=f'{lb}', color=colors(data[1], True))
        im_crop = im_ori[box_struct[1]:box_struct[3], box_struct[0]:box_struct[2], :]
        tar = f"tmp/{lb}_{k}.jpg"
        cv2.imwrite(tar, im_crop)
        file2 = open(tar, "rb")
        ocr_response = requests.post(url, files={"file": file2}, data=params, headers=headers, timeout=800)
        ch, cw, _ = im_crop.shape
        im_crop = np.zeros((ch+20, cw, 3)) + 255
        im_crop = np.uint8(im_crop)
        if ocr_response.status_code == 200:
            annotator1 = Annotator(im_crop, line_width=2, pil=True, font_size=15, example='中午')
            ocr_res_json = ocr_response.json()
            ocr_text = ocr_res_json['data']
            output_text += '\n'.join(ocr_text) + '\n'
            dt_boxes = ocr_res_json['boxes']
            for i, (box_line, text) in enumerate(zip(dt_boxes, ocr_text)):
                if len(box_line)==0:
                    print(f'box: {box_line}, ocr: {text}')
                    continue
                box_line = list(map(int, box_line))
                box_line_on_page = copy.deepcopy(box_line)
                box_line_on_page[0] += box_struct[0]
                box_line_on_page[2] += box_struct[0]
                box_line_on_page[1] += box_struct[1]
                box_line_on_page[3] += box_struct[1]
                annotator0.box_label(box_line_on_page, label='', color=colors(1, True))
                box_line[0] = 20 if box_line[0]<20 else box_line[0]
                box_line[3] = box_line[3] - (box_line[3]-box_line[1]) // 5
                box_line[1] = box_line[3] - 1
                annotator1.box_label(box_line, label=f'{text}', color=colors(0, True))
            im2 = annotator1.result()
            h2, w2 = im2.shape[:2]
            if box_struct[1]+h2>im_gray.shape[0]:
                box_struct[1] = im_gray.shape[0] - h2
            if box_struct[0]+w2>im_gray.shape[1]:
                box_struct[0] = im_gray.shape[1] - w2
            im_gray[box_struct[1]:box_struct[1]+h2, box_struct[0]:box_struct[0]+w2, :] = im2
        else:
            print(f'{OCR_API_URL1} ocr error: ',ocr_response.status_code)
    # return annotator0.result()
    im = np.concatenate([annotator0.result(), im_gray], axis=1)
    im = np.array(im, dtype=np.uint8)
    return Image.fromarray(im), output_text
    # return annotator0.result()
    # return im0
if __name__=='__main__':
    # root = '/data/liyaze/tail_ocr-master-bc8cdc31f634b8b6a7feed57be7522fd02d0a585/struct_crop_images'
    # root = '/data/liyaze/tail_ocr-master-bc8cdc31f634b8b6a7feed57be7522fd02d0a585/some_tools/tmp'
    root = '/data/liyaze/dataset/test/带拼音的'
    root = r'D:\迅雷下载\秒懂中国史-北宋'
    root = r'D:\SCJT\code\pachong\明星'
    root = r'D:\SCJT\code\pachong\猫'
    root = r'D:\SCJT\data\正文\2024-11'
    remake_box_ch = False

    files = Path(root).rglob('*.*')
    files = [file for file in files if file.suffix.lower() in ['.jpg', '.png']] 
    # files = sorted(files, key=lambda x:int(str(x).split('_')[-1].split('.')[0]))
    save = f'data/{Path(root).name}_predict_remake_box_{remake_box_ch}'
    os.makedirs(save, exist_ok=True)
    # file_path = '/data/liyaze/dataset/test/带拼音的/西游记之误入小雷音寺/西游记之误入小雷音寺_14.jpg'
    # root = osp.dirname(osp.dirname(file_path))
    # files = [file_path]
    is_book = True
    for i, file in enumerate(files):
        file = Path(file)
        tar = f'{save}/{i:03d}.jpg' if is_book else f'{save}/{file.name}'
        tar_txt = f'{save}/{i:03d}.txt' if is_book else f'{save}/{file.stem}.txt'
        # if '034.jpg' not in tar:
        #     continue
        # while True:
        im_ori, output_text = rec_layout(str(file), remake_box_ch, url=OCR_API_URL1)
        print(type(im_ori))
        im_ori.save(tar)
        print(f'tar: {tar}')
        print(f'tar_txt: {tar_txt}')
        f = open(tar_txt, 'w', encoding='utf-8')
        f.write(output_text)
        f.close()
        # cv2.imwrite(tar, im2)