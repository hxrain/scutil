# -*- coding: utf-8 -*-

import imgui_env as imenv
import imgui
from PIL import Image
import io
import base64
import re
from imgui_env import imgui_mod_base, imgui_app_base


class imgui_dlg(imgui_mod_base):
    'imgui应用app的功能逻辑模块基类'

    def __init__(self, img):
        self.value = ''
        self.value2 = ''

        # 准备图像对象
        if isinstance(img, bytes):
            img_file = io.BytesIO(img)
        elif isinstance(img, str) and img.startswith('data:image/'):
            data = re.findall(r';base64,(.*)', img)[0]
            imgdata = base64.decodebytes(data.encode('latin-1'))
            img_file = io.BytesIO(imgdata)
        elif img:
            img_file = Image.open(img)
        else:
            return
        self.img = Image.open(img_file)

    def on_load(self, im):
        self.win_size = im.main_win.get_size()
        self.tex = imenv.imgae_tex(self.img)

    def get_input(self, cln=False):
        ret = True
        # 设置imgui内部窗口位置和样式
        flags = imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_SAVED_SETTINGS | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE

        imgui.push_style_var(imgui.STYLE_WINDOW_PADDING, (30, 2))
        imgui.set_next_window_position(0, 0)
        imgui.set_next_window_size(self.win_size[0], self.win_size[1])

        # 绘制imgui交互窗口
        imgui.begin("1", False, flags)
        imgui.set_window_font_scale(1.5)  # 放大输入的字体
        imgui.image(self.tex.handle, self.img.width, self.img.height, border_color=(0, 0, 1, 1))  # 输出图片
        imgui.set_keyboard_focus_here()  # 要求输入框具有焦点
        if not cln:
            # 文本输入框
            changed, self.value = imgui.input_text('', self.value, 10)  # imgui.INPUT_TEXT_CHARS_UPPERCASE
        else:
            # 为了规避多次实例创建出现的遗留剩余数据的bug,进行一次数据清除
            _, _ = imgui.input_text(' ', '', 10, imgui.INPUT_TEXT_CHARS_UPPERCASE)
            ret = False
        imgui.end()

        imgui.pop_style_var()

        return ret

    def on_mod(self, im, app, isclosing):
        # 如果窗体不是最小化,那么就强制获取焦点
        if not im.main_win.is_minimize() and not imgui.is_any_item_focused():
            im.main_win.set_focus()
            imgui.set_window_focus()

        # 如果发现回车键被按下,则停止程序
        return self.get_input(im.chk_key_down([257, 335]) or isclosing)


def input_validcode(img, title='请输入'):
    """显示图片验证码并等待输入.
       返回值:输入的内容;发生错误返回None
    """

    def env_init_cb(glfw_win):
        """进行imgui环境初始化个性化配置"""
        # 禁止改变窗口尺寸,禁用最大化按钮
        glfw_win.enable_resize(False)
        # 窗口始终置顶
        glfw_win.enable_topmost(True)

        # 调整全局默认样式
        style = imgui.get_style()
        # 禁用窗口圆角
        style.window_rounding = 0
        # 文本颜色
        style.colors[imgui.COLOR_TEXT] = (.2, 1, .8, 1)
        # 窗口背景色
        style.colors[imgui.COLOR_WINDOW_BACKGROUND] = (.86, .86, .865, 1)
        # 容器背景色
        style.colors[imgui.COLOR_FRAME_BACKGROUND] = (.2, .2, .2, 1)

    try:
        # 生成输入对话框对象
        dlg = imgui_dlg(img)
        # 显示对话框,进行事件循环
        imenv.im_env_loop(dlg, title=title, width=max(dlg.img.width, 180), height=dlg.img.height + 36,
                          fullscreen=False, app_class=imgui_app_base, env_init_cb=env_init_cb, bg_color=(.7, .7, .7, 1))
        return dlg.value
    except Exception as e:
        return None

# if __name__ == '__main__':
#     img = 'data:image/png;base64,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'
#     print('vcode:%s' % input_validcode(img))
#
#     import threading
#     import mutex_lock as ml
#
#     locker = ml.lock_t(True)
#
#
#     def work_test():
#         with locker:
#             print('vcode:%s' % input_validcode(img))
#
#
#     thds = []
#     for i in range(4):
#         thds.append(threading.Thread(target=work_test))
#         thds[i].start()
#     for i in range(4):
#         thds[i].join()
#     print('end')
