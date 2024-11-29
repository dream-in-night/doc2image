import copy
import os
import time

from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2
import random
import chardet
from pathlib import Path

from tqdm import tqdm

# 判断当前系统是否为Windows
is_windows = os.name == 'nt'


def is_hanzi(c):
	return c >= '\u4e00' and c <= '\u9fa5'


def detect_encoding(file_path):
	# 以二进制模式打开文件，读取文件内容
	with open(file_path, 'rb') as file:
		raw_data = file.read()
		result = chardet.detect(raw_data)  # 使用chardet检测编码
		return result['encoding']

# 背景图片的路径
if is_windows:
	background_dir = [r'D:\SCJT\code\doc2image\data\明星_predict_remake_box_False',
	                 r'D:\SCJT\code\doc2image\data\狗_predict_remake_box_False',
	                 r'D:\SCJT\code\doc2image\data\猫_predict_remake_box_False']
else:
	background_dir = []
background_files = []
for bg_dir in background_dir:
	background_files += [str(x) for x in Path(bg_dir).rglob('*.*') if x.suffix.lower() in ['.jpg', '.png']]
	
def get_font_size(font_paths_2):
	font_size = {}
	for font_path in font_paths_2:
		font = ImageFont.truetype(font_path, 30)
		im = Image.new('L', (100, 100))
		draw = ImageDraw.Draw(im)
		draw.text((0, 0), '你好，今天的天气怎么样', (114), font=font)
		im = np.array(im)
		# 从高度为0处，逐渐增加高度，直到这一行像素不全部一致,代表一个字符的高度的起始位置
		font_h1 = 0
		for h in range(1, 15):
			if np.any(im[h] != im[h - 1]):
				font_h1 = h
				break
		font_h1 = 0 if font_h1 == 1 else font_h1
		# 从高度为30处，逐渐增加高度，直到这一行像素全部一致,代表一个字符的高度
		font_h2 = 30
		for h in range(25, 100):
			if np.all(im[h] == im[h - 1]):
				font_h2 = h
				break
		# print(f'font_h1: {font_h1}, {float(font_h1) / 30}')
		font_size[Path(font_path).stem] = [float(font_h1) / 30, float(font_h2) / 30]
	return font_size


# 判断字符是不是中文字体
if is_windows:
	font_fangsong = r'D:\font\fangsong_downcc.com\fangsongziti_downcc.com\仿宋_GB2312.ttf'  # Windows
	font_root = r'D:\font'
else:
	font_fangsong = '/mnt/liyaze/dataset/Detect/font/fangsong_downcc.com/fangsongziti_downcc.com/仿宋_GB2312.ttf'
	font_root = '/mnt/liyaze/dataset/Detect/font'
font_paths = list(Path(font_root).rglob('*.ttf'))
font_paths = [str(x) for x in font_paths if x.suffix == '.ttf']
font_info = ImageFont.truetype(font_fangsong, 20)
# 实际字体高度与字体大小比例的字典
font_size_ratio = get_font_size(font_paths)
# 随机的选取一个中文字体
if is_windows:
	f = open('ppocr_keys_v1.txt', 'r', encoding='utf-8')
else:
	f = open(
		'/data/liyaze/tail_ocr-master-bc8cdc31f634b8b6a7feed57be7522fd02d0a585/app/ppocr/paddleocr/ppocr/utils/ppocr_keys_v1.txt',
		'r', encoding='utf-8')
pp_char_dict = f.read().split('\n')
f.close()
# 所有的英文字母
en_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
pp_char_dict_zh = [x for x in pp_char_dict if is_hanzi(x)]


def is_supported_char(font, char):
	try:
		# 尝试加载字符的字体渲染，如果不能渲染则返回 False
		mask = font.getmask(char)
		return True
	except Exception as e:
		return False


def 制作封面():
	# 随机选取一个中文字体
	font_path = random.choice(font_paths)
	# 随机选取汉字
	ss = ''
	l = random.randint(3, 5)
	while len(ss) < l:
		c = random.choice(pp_char_dict_zh)
		if is_hanzi(c):
			ss += c
	# 随机的宽高
	w, h = random.randint(300, 600), random.randint(800, 1000)
	# 随机选取一个比较浅的颜色作为背景
	b, g, r = random.randint(180, 255), random.randint(180, 255), random.randint(180, 255)
	im = Image.new('RGB', (w, h), (b, g, r))
	font_size = random.randint(10, 60)
	deltah = random.randint(font_size, int(font_size * 1.5))
	font = ImageFont.truetype(font_path, font_size)
	draw = ImageDraw.Draw(im)
	# 写入文本,竖行,作为标题
	# 位置一般是三分之一或三分之二处,宽高都是这样
	x, y = random.randint(w // 3, w - w // 3), random.randint(h // 3, h - h // 3)
	# 逐个字的写入
	# 如果超出下边界,修改y值
	y = min(y, h - font_size * len(ss) - deltah * (len(ss) - 1))
	for i in range(len(ss)):
		draw.text((x, y), ss[i], (255 - b, 255 - g, 255 - r), font=font)
		y += deltah
	# im.save('cover.jpg')
	return im


def 生成新页(paste_image:bool=False) -> (Image, int, int, int, int, ImageFont, ImageFont, int, int, int, int, int, int, int, str, list):
	# 随机选取一个中文字体
	font_path = random.choice(font_paths)
	# 随机的宽高
	w, h = random.randint(600, 1000), random.randint(600, 1000)
	# 随机选取一个比较浅的颜色作为背景
	b, g, r = random.randint(180, 255), random.randint(180, 255), random.randint(180, 255)
	im = Image.new('RGB', (w, h), (b, g, r))
	font_size = random.randint(20, 30)
	deltah = random.randint(int(font_size), int(font_size * 1.5))
	ratio = font_size_ratio[Path(font_path).stem] if Path(font_path).stem in font_size_ratio.keys() else [1, 1]
	font = ImageFont.truetype(font_path, font_size)
	font2 = ImageFont.truetype(font_fangsong, font_size)
	font_size_delta = int(font_size * ratio[0]) # 文字y坐标与字体大小之差的比例
	# print(f'font_size_delta: {font_size_delta}')
	font_size = int(font_size * ratio[1])  # 实际字体高度与字体大小比例
	# 设置页边距
	x_offset = 30
	y_offset = 60
	# 首行缩进2字符
	x_end = w - x_offset
	y_end = h - y_offset
	time.sleep(1)
	paste_box = []
	if paste_image:
		background_file = random.choice(background_files)
		im2 = Image.open(background_file).convert('RGB')
		ww = random.randint(int(w / 4), int(w / 2))
		hh = random.randint(int(h / 4), int(h / 2))
		# im_w, im_h = im2.size
		im2 = im2.resize((ww, hh))
		# 颜色与背景颜色相反, 调试
		# b1, g1, r1 = 255 - b, 255 - g, 255 - r
		# im2 = Image.new('RGB', (ww, hh), (b1, g1, r1))
		# 选择插入的位置,不能超出图片边界
		x, y = random.randint(x_offset, x_end - ww), random.randint(y_offset, y_end - hh)
		im.paste(im2, (x, y))
		paste_box = [x, y, x + ww, y + hh]
		
	draw = ImageDraw.Draw(im)
	return im, draw, x_offset, y_offset, deltah, font, font2, font_size, font_size_delta, x_end, y_end, w, h, b, g, r, font_path, paste_box


def 制作内容(txt_path, save: Path, paste_image:bool=True, debug=False):
	# paste_image: 粘贴图片到随机的位置
	encoding = detect_encoding(txt_path)
	ff = open(txt_path, 'r', encoding=encoding, errors='ignore')
	lines = ff.read().split('\n')
	ff.close()
	stem = Path(txt_path).stem
	
	im, draw, x_offset, y_offset, deltah, font, font2, font_size, font_size_delta, x_end, y_end, w, h, b, g, r, font_path, paste_box = 生成新页(paste_image)
	y = y_offset
	page_num, row_num, col_num = 0, 0, 0
	text_in_paste_image = False
	unsupported_char_in_line = False
	line_string = ''  # 行
	line_boxes = [] # 行里内个字的框
	box_left_string = ''

	log_p = save.joinpath('log.txt')
	line_i = 0
	if log_p.exists() and not is_windows:
		try:
			f = open(log_p, 'r', encoding='utf-8')
			line_i, page_num = f.read().split('\n')[:2]
			line_i = int(line_i)
			page_num = int(page_num)
			f.close()
		except:
			pass
	
	tar_txt = save.joinpath(f'{page_num:08d}.txt').__str__()
	tar_img = save.joinpath(f'{page_num:08d}.jpg').__str__()
	f_txt = open(tar_txt, 'w', encoding='utf-8')
	
	bar = tqdm(total=len(lines), desc=f'{stem} page {page_num}')
	for i, ss in enumerate(lines):
		if i < line_i:
			continue
		bar.update(1)
		new_string = ''  # 段落
		for s in ss:
			if s not in pp_char_dict:
				continue
			new_string += s
		new_string = new_string.replace(' ', '')
		new_string = new_string.replace('\t', '')
		new_string = new_string.strip()
		if len(new_string) > 0:
			for j in range(len(new_string)):
				if row_num == 0:
					x = (col_num + 2) * font_size + x_offset
				else:
					x = col_num * font_size + x_offset
				if paste_image:
					# 如果文字落入paste_box内
					x1, x2, y1, y2 = x, x + font_size, y, y + font_size
					if (paste_box[0] < x1 < paste_box[2] or paste_box[0] < x2 < paste_box[2]) and (paste_box[1] < y1 < paste_box[3] or paste_box[1] < y2 < paste_box[3]):
						box_left_string = copy.deepcopy(line_string)
						text_in_paste_image = True
					while (paste_box[0] < x1 < paste_box[2] or paste_box[0] < x2 < paste_box[2]) and (paste_box[1] < y1 < paste_box[3] or paste_box[1] < y2 < paste_box[3]):
						col_num += 1
						if row_num == 0:
							x = (col_num + 2) * font_size + x_offset
						else:
							x = col_num * font_size + x_offset
						x1, x2 = x, x + font_size
				# 如果超出页面宽度,或者段落结束, 换行,写标签
				if x >= x_end or j==len(new_string)-1:
					# 画框,测试
					if row_num == 0:
						x1 = 2 * font_size + x_offset
					else:
						x1 = x_offset
					x2 = x - (len(line_string) - len(line_string.rstrip())) * font_size
					font_size_delta2 = 0 if unsupported_char_in_line else font_size_delta
					if len(line_string)>0:
						if text_in_paste_image: # and len(box_left_string)<len(line_string):# 如果在paste_box内
							# print('='*100) # 都是空
							# print(line_string)
							# print(box_left_string)
							# print(line_boxes)
							if len(box_left_string.strip()) == 0:  # 如果框的左侧没有字
								color = 'red'
								box = [[line_boxes[0], y + font_size_delta2, x2, y + font_size, line_string]]
							else: # 左侧有字
								# 右侧没有字
								if len(line_string)==len(box_left_string):
									color = 'black'
									box = [[x1, y + font_size_delta2, min(line_boxes[-1]+font_size, x2), y + font_size,
									        line_string]]
								else:
									color = 'green'
									box = [[x1, y + font_size_delta2, min(line_boxes[len(box_left_string)-1]+font_size, x2), y + font_size, box_left_string],
								       [line_boxes[len(box_left_string)], y + font_size_delta2, x2, y + font_size, line_string[len(box_left_string):]]]
						else:
							box = [[x1, y + font_size_delta2, x2, y + font_size, line_string]]
							color = 'gray'
					else:
						color = 'blue'
						box = [[x1, y + font_size_delta, x2, y + font_size, '']]
					# 获取标签
					for box_ in box:
						f_txt.write(f'{box_}\n')
						if is_windows:
							if not debug:
								color = 'red'
							draw.rectangle(box_[:4], fill=None, outline=color, width=1)
							if debug:
								draw.text((box_[0], box_[1]-font_size), f"{text_in_paste_image} , s:{len(line_string)}", color, font=font_info)
					y += font_size + deltah
					row_num += 1
					col_num = 0
					line_string = ''
					line_boxes = []
					box_left_string = ''
					text_in_paste_image = False
					unsupported_char_in_line = False
					continue
				# 如果超出页面高度,换页
				if y >= y_end:
					im.save(tar_img)
					if is_windows:
						print(tar_img)
					f_txt.close()
					page_num += 1
					tar_txt = save.joinpath(f'{page_num:08d}.txt').__str__()
					tar_img = save.joinpath(f'{page_num:08d}.jpg').__str__()
					f_txt = open(tar_txt, 'w', encoding='utf-8')
					im, draw, x_offset, y_offset, deltah, font, font2, font_size, font_size_delta, x_end, y_end, w, h, b, g, r, font_path, paste_box = 生成新页(paste_image)
					row_num, col_num = 0, 0
					y = y_offset
					line_string = ''
					box_left_string = ''
					text_in_paste_image = False
					unsupported_char_in_line = False
					line_boxes = []
					# 写入缓存
					f = open(log_p, 'w', encoding='utf-8')
					f.write(f'{i}\n')
					f.write(f'{page_num}')
					f.close()
				else:
					if is_supported_char(font, new_string[j]):
						draw.text((x, y), new_string[j], (255 - b, 255 - g, 255 - r), font=font)
					else:
						draw.text((x, y), new_string[j], (255 - b, 255 - g, 255 - r), font=font2)
					# 判断字体区域是不是纯色,如果是,就是写字失败了
					im_crop = np.array(im.crop((x, y, x + font_size, y + font_size)))
					im_r, im_g, im_b = im_crop[:, :, 0], im_crop[:, :, 1], im_crop[:, :, 2]
					im_r = np.unique(im_r)
					im_g = np.unique(im_g)
					im_b = np.unique(im_b)
					if len(im_r) == 1 and len(im_g) == 1 and len(im_b) == 1:
						draw.text((x, y), new_string[j], (255 - b, 255 - g, 255 - r), font=font2)
						unsupported_char_in_line = True
					line_string += new_string[j]
					line_boxes.append(x)
					col_num += 1
					if is_windows and debug:
						# 调试使用, 有的框穿过了图像,有的框是正常的,原因是因为最外层的for循环,每个段落开始都会重置text_in_paste_image为False
						draw.text((x, y-20), str(text_in_paste_image)[0], (255 - b, 255 - g, 255 - r), font=font_info)
						# 对每个字画框
						draw.rectangle([x, y, x + font_size, y + font_size], fill=None, outline=(0, 0, 255))
	bar.close()


if __name__ == '__main__':
	# 制作封面()
	if is_windows:
		root = r'D:\SCJT\data\pdf\小说\txts'
	else:
		root = '/mnt/liyaze/dataset/Detect/印刷体/txts'
	save = Path(root)
	save = save.parent.joinpath(save.stem + '_img')
	files = list(Path(root).rglob('*.txt'))
	for file in files:
		save.joinpath(Path(file).stem).mkdir(parents=True, exist_ok=True)
		制作内容(str(file), save.joinpath(Path(file).stem), paste_image=True, debug=False)
