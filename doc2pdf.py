import subprocess
import os
import os.path as osp
def convert_docx_to_pdf(docx_path, pdf_path):
    print(docx_path)
    subprocess.run(["C:\Program Files\LibreOffice\program\soffice.exe", '--headless', '--convert-to', 'pdf', docx_path, '--outdir', pdf_path])

# 使用示例
docx_path = '陈青云 病书生.docx'
doc_path = r'D:\SCJT\data\pdf\小说\docxs'  # 输出 PDF 文件的目录
pdf_dir = r'D:\SCJT\data\pdf\小说\pdfs'  # 输出 PDF 文件的目录
for file in os.listdir(doc_path):
    docx_path = osp.join(doc_path, file)
    pdf_path = osp.join(pdf_dir, file.replace('.docx', '.pdf'))
    if not osp.exists(pdf_path):
        convert_docx_to_pdf(docx_path, pdf_dir)
