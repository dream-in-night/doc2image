import fitz  # PyMuPDF
from pathlib import Path
import os.path as osp
import copy
import numpy as np
from ultralytics.utils.plotting import Annotator, colors
from PIL import Image
import cv2
import json
import os
from pdf2image import convert_from_path
import shutil
def remake_boxes_ch(dt_boxes, text_all:list) -> (list,  list):
    # 正文里，一行字没有检测好, 本来是一个框，检测为了左右两三个框， 需要合并为1个框
    if len(dt_boxes)<=1:
        return dt_boxes, text_all
    dt_boxes_all = copy.deepcopy(dt_boxes)
    text_all2 = []
    dt_boxes_all2 = []
    dt_boxes = np.array(dt_boxes)
    dt_boxes2 = np.array(dt_boxes).reshape(-1, 2)
    box_height_mean = np.mean(np.array(dt_boxes[:,2, 1]-dt_boxes[:,0,1]).reshape(-1))
    box_width_max = np.max(dt_boxes2) - np.min(dt_boxes2)
    font_size = box_height_mean
    box_height = (np.max(np.array(dt_boxes[:,2, 1]-dt_boxes[:,0,1]).reshape(-1))) // 2
    while len(dt_boxes_all)>0:
        dt_box = dt_boxes_all.pop(0)
        de_text = text_all.pop(0)
        boxes, texts = [dt_box], [de_text]
        # b1_y1, b1_y2, b1_h, b1_yc = dt_box[1], dt_box[3], dt_box[3]-dt_box[1], (dt_box[3]+dt_box[1])/2
        b1_y1, b1_y2 = np.min(dt_box[:, 1]), np.max(dt_box[:, 1])
        b1_h, b1_yc = b1_y2-b1_y1, (b1_y1+b1_y2)/2
        del_inds = []
        for i in range(len(dt_boxes_all)):
            dt_box_ = dt_boxes_all[i]
            b2_y1, b2_y2 = np.min(dt_box_[:, 1]), np.max(dt_box_[:, 1])
            b2_h, b2_yc = b2_y2-b2_y1, (b2_y1+b2_y2)/2
            if max(b1_h, b2_h)/min(b1_h, b2_h)>3:
                continue
            if b2_yc<b1_y1 or b2_yc>b1_y2:
                continue
            if b1_yc<b2_y1 or b1_yc>b2_y2:
                continue
            if b2_y2<b1_y1 or b1_y2<b2_y1:
                continue
            boxes.append(dt_box_)
            texts.append(text_all[i])
            del_inds.append(i)
        dt_boxes_all = [x for i,x in enumerate(dt_boxes_all) if i not in del_inds]
        text_all = [x for i,x in enumerate(text_all) if i not in del_inds]
        boxes2, texts2 = [], []
        if len(boxes)>1:
            xs = [b[0,0] for b in boxes]
            x_inds = np.argsort(xs)
            boxes = [boxes[i] for i in x_inds]
            texts = [texts[i] for i in x_inds]
            boxes2 = [boxes[0]]
            texts2 = [texts[0]]
            num = 1
            for box, text in zip(boxes[1:], texts[1:]):
                # width = box[2]-box[0]
                width = np.max(box[:, 0::2]) - np.min(box[:, 0::2])
                pre_width = boxes2[-1][2]-boxes2[-1][0]
                pre_width = np.max(boxes2[-1][:,0::2])-np.min(boxes2[-1][:,0::2])
                interval = np.min(box[:, 0::2])-np.max(boxes2[-1][:,0::2])
                if interval<min(pre_width, width)*4:
                    # 扩张框
                    # 右上角 x,y
                    boxes2[-1][1][0] = max(boxes2[-1][1][0], box[1, 0])
                    boxes2[-1][1][1] = min(boxes2[-1][1][1], box[1, 1])
                    # 右下角 x,y
                    boxes2[-1][2][0] = max(boxes2[-1][2][0], box[1, 0])
                    boxes2[-1][2][1] = max(boxes2[-1][2][1], box[1, 1])
                    num += 1
                    texts2[-1] += text
                else:
                    # 新的框
                    boxes2.append(box)
                    texts2.append(text)
        if len(boxes2)>0:
            for b,t in zip(boxes2, texts2):
                dt_boxes_all2.append(b)
                text_all2.append(t)
        else:
            dt_boxes_all2.append(dt_box)
            text_all2.append(de_text)
    return dt_boxes_all2, text_all2
def convert_pdf_to_images(pdf_path, image_folder):
    # 使用 convert_from_path 方法将 PDF 转换为图像
    print(f'pdf_path: {pdf_path}')
    name = Path(pdf_path).stem
    images = convert_from_path(pdf_path)    
    # 将每一页保存为图片
    for i, image in enumerate(images):
        image_path = f"{image_folder}/{name}_{i:06d}.jpg"
        image.save(image_path, 'PNG')
def pdf2im(pdf_path, ishow=False):
    imroot = Path(pdf_path)
    imroot = imroot.parent.joinpath(imroot.stem)
    image_folder = str(imroot)
    os.makedirs(image_folder, exist_ok=True)
    # 获取 PDF 页数
    pdf_document = fitz.open(pdf_path)
    pdf_page_count = pdf_document.page_count
    # 获取图片文件夹中的图片数量
    image_files = [f for f in os.listdir(image_folder) if f.endswith('.jpg')]
    image_count = len(image_files)
    # 如果图片数量与PDF页数相同，则跳过转换
    if image_count == pdf_page_count:
        print("PDF already converted to images. Skipping conversion.")
    else:
        # 否则，执行转换
        convert_pdf_to_images(pdf_path, image_folder)
    label_file = imroot.joinpath('Label.txt')
    label_file2 = imroot.joinpath('Label2.txt')
    f_label = open(label_file, 'w', encoding='utf-8')
    # 遍历每一页
    if ishow:
        cv2.namedWindow('im', cv2.WINDOW_NORMAL)
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        if '.ppt' in imroot.name:
            im = imroot.joinpath(f'{imroot.name}_{page_num+1:06d}.jpg')
        else:
            im = imroot.joinpath(f'{imroot.name}_{page_num:06d}.jpg')
        label_line = f'{imroot.stem}/{imroot.stem}_{page_num:06d}.jpg\t'
        dict_s = []
        # im = f'西游记之误入小雷音寺/西游记之误入小雷音寺_{page_num:06d}.jpg'
        assert osp.exists(im), im
        im = Image.open(im).convert('RGB')
        if ishow:
            annotator = Annotator(im, line_width=3, font_size=20, pil=True, example='中文')
        # 获取页面的文本和坐标信息
        text_dict = page.get_text("dict")
        # 获取页面的宽度和高度
        page_width = page.rect.width
        page_height = page.rect.height
        im_w, im_h = im.size
        # 遍历文本块
        boxes_all, text_all = [], []
        for block in text_dict["blocks"]:
            # 确保该块是文本块
            if block["type"] == 0:  # 0表示文本块
                for line in block["lines"]:
                    for span in line["spans"]:
                        # 获取文本和坐标
                        text = span["text"]
                        bbox = span["bbox"]  # (x0, y0, x1, y1)
                        bbox = list(bbox)
                        # print(f'字符: \'{text}\', 坐标: {bbox}')
                        句子前的空格数量 = len(text) - len(text.lstrip())
                        句子后的空格数量 = len(text) - len(text.rstrip())
                        bbox[0] = bbox[0] / page_width * im_w
                        bbox[1] = bbox[1] / page_height * im_h
                        bbox[2] = bbox[2] / page_width * im_w
                        bbox[3] = bbox[3] / page_height * im_h
                        # print(span)
                        单个汉字的宽度 = int(span['size'] / page_width * im_w) # 单个汉字的宽度
                        x_offset1, x_offset2 = 0, 0
                        # print(f'句子前的空格数量: {句子前的空格数量}, 单个汉字的宽度:{单个汉字的宽度}')
                        if 句子前的空格数量 > 0:
                            text = text[句子前的空格数量:]
                            x_offset1 = 句子前的空格数量 * 单个汉字的宽度
                        if 句子后的空格数量 > 0:
                            text = text[:-句子后的空格数量]
                            x_offset2 = 句子后的空格数量 * 单个汉字的宽度
                        # 字符: '《西游记》是中国文学史上', 坐标: (342.7200012207031, 262.114990234375) 到 (510.60003662109375, 275.55499267578125)
                        bbox = list(map(int, bbox))
                        bbox[0] += x_offset1
                        bbox[2] -= x_offset2
                        # crop_im = np.array(im.crop(bbox))
                        x1,y1 = bbox[0],bbox[1]
                        x2,y2 = bbox[2],bbox[1]
                        x3,y3 = bbox[2],bbox[3]
                        x4,y4 = bbox[0],bbox[3]
                        box = np.array([[x1,y1],[x2,y2],[x3,y3],[x4,y4],[x1,y1]])
                        boxes_all.append(box)
                        text_all.append(text.strip())
        boxes_all, text_all = remake_boxes_ch(boxes_all, text_all)
        for box, text in zip(boxes_all, text_all):
            box2 = [np.min(box[:,0]), np.min(box[:,1]), np.max(box[:,0]), np.max(box[:,1])]
            box = box.tolist()
            dict_ = {"transcription":text,"points":box}
            dict_s.append(dict_)
            box2 = list(map(int, box2))
            if ishow:
                annotator.box_label(box2, text, color=colors(3, True))
        dict_s = json.dumps(dict_s, ensure_ascii=False)
        label_line = label_line + dict_s + '\n'
        f_label.write(label_line)
        if ishow:
            im = annotator.result()
            cv2.imshow('im', im)
            if cv2.waitKey(0) == ord('q'):
                break
            elif cv2.waitKey(0) == ord('n'):
                pass
            elif cv2.waitKey(0) == ord('s'):
                break
    # 关闭PDF文档
    f_label.close()
    shutil.copy(label_file, label_file2)
    pdf_document.close()
if __name__ == '__main__':
    root = r'D:\SCJT\data\pdf\小说\pdfs'
    pdf_paths = list(Path(root).rglob('*.pdf'))
    pdf_paths.sort(key=lambda x: x.stat().st_size)
    for i,pdf_path in enumerate(pdf_paths):
        # if not '流花剑' in str(pdf_path):
        #     continue
        print(pdf_path)
        pdf2im(str(pdf_path), ishow=False)
        # if i>=2:
        #     break