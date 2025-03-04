import pytesseract
from PIL import Image
import cv2
import os
import re

# 指定 Tesseract 可执行文件路径和 tessdata 目录
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
tessdata_dir_config = r'--tessdata-dir "C:\Program Files\Tesseract-OCR\tessdata"'


def clean_name(text):
    # 清洗识别结果
    # 1. 去除多余的空格
    cleaned = re.sub(r'\s+', '', text)
    # 2. 将英文句号“.”替换为中文“·”
    cleaned = cleaned.replace('.', '·')
    # 3. 去除其他可能的异常字符（仅保留中文、·和少量英文）
    cleaned = re.sub(r'[^·\u4e00-\u9fa5a-zA-Z]', '', cleaned)
    return cleaned


def crop_player_name_regions(image):
    # 根据图片布局，裁剪中文名字所在的区域
    # 坐标格式：(x_start, y_start, x_end, y_end)，单位是像素
    # 假设图片分辨率约为 720x1280（常见手机截图分辨率）
    player_name_regions = [
        # 2025/03-04 记录下的球员名字
        (130, 510, 375, 550),  # 球员1 左 高度
        (130, 590, 375, 630),  # 球员2
        (130, 670, 375, 710),  # 球员3
        (130, 750, 345, 790),  # 球员4
        (130, 830, 345, 870),  # 球员5
    ]

    cropped_images = []
    for (x, y, w, h) in player_name_regions:
        cropped = image[y:h, x:w]
        # 放大裁剪区域以提高识别准确率
        cropped = cv2.resize(cropped, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        cropped_images.append(cropped)
    return cropped_images


def extract_chinese_names(image_path):
    try:
        # 检查文件是否存在
        if not os.path.exists(image_path):
            return f"错误：图片文件 '{image_path}' 不存在"

        # 读取图片
        image = cv2.imread(image_path)
        if image is None:
            return f"错误：无法加载图片 '{image_path}'"

        # 裁剪中文名字区域
        cropped_images = crop_player_name_regions(image)

        # 识别中文名字
        chinese_names = []
        for i, cropped in enumerate(cropped_images):
            # 仅使用中文语言包
            text = pytesseract.image_to_string(cropped, lang='chi_sim', config=tessdata_dir_config)
            # 清洗结果
            cleaned_text = clean_name(text)
            if cleaned_text:
                chinese_names.append(cleaned_text)
            else:
                chinese_names.append(f"球员{i + 1}：名字未识别")

        return chinese_names

    except Exception as e:
        return f"发生错误: {str(e)}"


# 示例用法
if __name__ == "__main__":
    image_path = r"./1.jpg"  # 替换为你的图片路径
    result = extract_chinese_names(image_path)
    print("识别出的中文球员名字：", result)
