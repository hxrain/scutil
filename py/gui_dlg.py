import io
from tkinter.simpledialog import *

from PIL import ImageTk, Image

#显示给定的图片,得到输入的验证码字符
def input_validcode(img):
    root = Tk()
    root.title('输入验证码')
    root.wm_attributes('-topmost', 1)  # 窗口置顶
    root.resizable(width=False, height=False)  # 禁止改变窗口大小

    # 准备图像对象
    if isinstance(img, bytes):
        img_file = io.BytesIO(img)
    else:
        img_file = Image.open(img)
    img_file = Image.open(img_file)

    # 转换图像对象为标准照片对象
    img_photo = ImageTk.PhotoImage(img_file)
    # 生成图像标签并绑定照片对象
    img_lbl = Label(root, image=img_photo)
    img_lbl.grid(row=0, column=0)

    # 定义输入框回调函数
    ret = ''

    def submit(ev=None):
        nonlocal ret
        ret = edt_in.get()
        root.destroy()

    # 创建输入框对象
    edt_in = Entry(root, insertbackground='blue', highlightthickness=0, width=20)
    edt_in.grid(row=0, column=1)
    edt_in.bind("<Return>", submit)
    edt_in.focus_set()

    # 调整窗口位置,居中
    root.update()
    screenwidth = root.winfo_screenwidth()
    screenheight = root.winfo_screenheight()
    width = root.winfo_width()
    height = root.winfo_height()
    root.geometry('+%d+%d' % ((screenwidth - width) / 2, (screenheight - height) / 2))

    # 进行UI事件循环,等待输入
    root.mainloop()

    # 返回最终输入结果
    return ret


if __name__ == '__main__':
    print('first:%s' % input_validcode())
    print('second:%s' % input_validcode())
