import imgui
import glfw
import time
import OpenGL.GL as gl

import os


def split(total, segs):
    """根据segs分段权重,对总长度total进行分段划分,得到每段长度列表和定位点列表"""
    t = sum(segs)
    rst = []
    pos = []
    p = 0
    for s in segs:
        v = int(total * s / t)
        rst.append(v)
        pos.append(p)
        p += v
    return rst, pos


def mouse_in(x, y, w, h):
    """判断鼠标是否在指定的位置"""
    px, py = imgui.get_mouse_pos()
    if px < x or px > x + w:
        return False
    if py < y or py > y + h:
        return False
    return True


class imgui_mod:
    'imgui应用app的功能逻辑模块'

    def on_load(self):
        """当前模块被装载的事件"""
        pass

    def _on_menu(self):
        # 绘制并处理主菜单条
        running = True
        if imgui.begin_main_menu_bar():
            # 在主菜单条上增加File菜单
            if imgui.begin_menu("File", True):
                # 在File菜单被点击后显示需要的菜单项
                clicked_quit, selected_quit = imgui.menu_item("Quit", 'CTRL+Q')
                # 如果Quit菜单项被点击,结束App
                if clicked_quit:
                    running = False
                # 结束File菜单的处理
                imgui.end_menu()
            # 结束主菜单条的处理
            imgui.end_main_menu_bar()
        return running

    def on_mod(self, im):
        '''
            进行具体的应用逻辑绘制处理:im为imgui环境对象;返回值告知程序是否继续.
            此方法应该被子类重载,完成具体的功能逻辑
        '''
        # 判断是否有ctrl+Q按下,结束app
        if im.is_key_down('ctrl+Q'):
            return False
        if not self._on_menu():
            return False

        style = imgui.get_style()
        imgui.begin("Color window")
        imgui.columns(4)
        for color in range(0, imgui.COLOR_COUNT):
            imgui.text("Color: {} {}".format(color, imgui.get_style_color_name(color)))
            imgui.color_button("color#{}".format(color), *style.colors[color])
            imgui.next_column()
        imgui.end()

        # 获取当前主窗口尺寸
        win_width, win_height = im.main_win.get_size()
        # 定义菜单条高度
        bar_height = 24
        # 计算横向比例分隔
        widths, hpos = split(win_width, (5, 15, 30))
        # 计算左侧竖向比例分隔
        heights, vpos = split(win_height - bar_height, (10, 30))
        # 左侧列表
        self.do_show_text('样本列表', hpos[0], bar_height, widths[0], win_height - bar_height, 'list')
        # 左上窗口
        self.do_show_text('差异处', hpos[1], bar_height + vpos[0], widths[1], heights[0], 'tmp_text')
        # 左下窗口
        self.do_show_text('新结果', hpos[1], bar_height + vpos[1], widths[1], heights[1], '测试123456')
        # 重新计算右侧竖向比例分隔
        heights, vpos = split(win_height - bar_height, (30, 30))
        # 右上窗口
        self.do_show_text('原文本', hpos[2], bar_height + vpos[0], widths[2], heights[0], '测试1234')
        # 右下窗口
        self.do_show_text('预处理', hpos[2], bar_height + vpos[1], widths[2], heights[1], '测试1234')

        return True

    def do_show_text(self, title, x, y, w, h, text, use_hsbar=False):
        """在指定的位置显示窗口并输出指定的文本"""
        # 子窗口标记:不可移动不可改变
        flags = imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_SAVED_SETTINGS
        # 设置子窗口位置
        imgui.set_next_window_position(x, y)
        imgui.set_next_window_size(w, h)
        # 显示子窗口
        if imgui.begin(title, False, flags)[1]:
            flags = 0
            if use_hsbar:
                flags |= imgui.WINDOW_HORIZONTAL_SCROLLING_BAR
            if text:
                imgui.begin_child("region", imgui.get_window_width() - 16, h - 40, True, flags)
                # 开启子区域,设定文本自动换行范围
                if not use_hsbar:
                    imgui.push_text_wrap_pos(imgui.get_window_width() - 4)
                imgui.text(text)
            imgui.end_child()
        imgui.end()


class imgui_app:
    'imgui应用程序基类'

    def __init__(self):
        self.mods = []
        self.im = None
        pass

    def on_init(self, im):
        'app初始化:im为imgui环境对象'
        self.im = im
        for m in self.mods:
            m.__dict__['im'] = im  # 给每个模块绑定imgui环境

        # 清理默认字体
        imgui.get_io().fonts.clear_fonts()

        # 装载首个字体,使之成为默认字体
        im.load_font('msyh.ttf', 17, im.font_tag_zh)  # 中文雅黑
        # im.load_font('simhei.ttf', 16, im.font_tag_zh)    #中文黑体

        # 再装载其他字体
        # im.load_font('Roboto-Medium.ttf', 16, im.font_tag_en,'./')    #英文字体,Apache License
        im.load_font('consola.ttf', 15, im.font_tag_en)  # 英文控制台字体
        # imgui.get_io().fonts.add_font_default() #内置英文字体
        im.imgui_bk.refresh_font_texture()

    def on_step(self):
        '应用绘制的主逻辑:im为imgui环境对象;返回值告知程序是否继续.'
        return self.on_app()

    def on_app(self):
        '进行具体的应用逻辑绘制处理:im为imgui环境对象;返回值告知程序是否继续.'
        for m in self.mods:
            if not m.on_mod(self.im):
                return False
        return True

    def append_mod(self, mod_class):
        '创建mod_class对象并放入内部模块链表'
        self.append_modobj(mod_class())

    def append_modobj(self, mod):
        '将mod对象放入内部模块链表'
        mod.on_load()
        self.mods.append(mod)


class imgui_env:
    'imgui应用环境对象'

    class glfw_win:
        'glfw环境管理器'

        def __init__(self):
            # 窗口句柄初始化
            self.window = None
            # glfw环境初始化
            if not glfw.init():
                print("glfw Could not initialize OpenGL context")
                exit(1)

            # glfw细节参数设置(OS X supports only forward-compatible core profiles from 3.2)
            glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
            glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
            glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
            glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, 1)

        def open(self, title, width=1024, height=768, fullscreen=False):
            'glfw环境创建应用窗口'
            if self.window is not None:
                return self.window

            # 使用glfw创建窗口句柄
            self.window = glfw.create_window(int(width), int(height), title,
                                             glfw.get_primary_monitor() if fullscreen else None, None)

            if not self.window:
                # 创建失败直接退出
                glfw.terminate()
                print("glfw Could not initialize Window")
                exit(1)

            # 绑定窗口对象为当前绘图环境
            glfw.make_context_current(self.window)
            return self.window

        def set_title(self, title):
            if self.window is None:
                return False
            glfw.set_window_title(self.window, title)
            return True

        def get_size(self):
            """获取窗口尺寸"""
            if self.window is None:
                return None
            return glfw.get_window_size(self.window)

        def set_pos(self, x=None, y=None):
            '设置窗口位置'
            if self.window is None:
                return
            if x is None or x is None:
                ws = glfw.get_window_size(self.window)
                ma = glfw.get_monitor_workarea(glfw.get_primary_monitor())
                if x is None:
                    x = (ma[2] - ws[0]) // 2
                if y is None:
                    y = (ma[3] - ws[1]) // 2
            glfw.set_window_pos(self.window, x, y)

        def close(self):
            '关闭glfw环境,关闭窗口'
            if self.window is not None:
                glfw.destroy_window(self.window)
                self.window = None
            glfw.terminate()

    def __init__(self, app, title='test测试imgui', width=1024, height=768, fullscreen=False):
        '初始化imgui应用环境'
        from imgui.integrations.glfw import GlfwRenderer
        self.keys_stat = {}
        self.fonts = {}
        self.font_tag_zh = '中文b'
        self.font_tag_en = '英文s'

        imgui.create_context()
        self.app = app
        # 生成glfw环境的对象
        self.main_win = self.glfw_win()
        # 创建glfw绘图窗口
        self.main_win.open(title, width, height, fullscreen)
        # 定义绘图窗口背景色
        self.bg_color = (.2, .2, .2, 1)
        # 清空背景
        self.clean()
        # 调整窗口位置
        self.main_win.set_pos()
        # 创建imgui绘图后端
        self.imgui_bk = imgui.integrations.glfw.GlfwRenderer(self.main_win.window)
        # 调用app对象的初始化事件
        self.app.on_init(self)

    def load_font(self, filename, size=14, tagname=None, path=None):
        '装载字体'
        io = imgui.get_io()
        if path is None:
            path = os.getenv('SYSTEMROOT') + "\\Fonts\\"
        path += filename
        if tagname is None:
            tagname = filename
        self.fonts[tagname] = io.fonts.add_font_from_file_ttf(path, size, io.fonts.get_glyph_ranges_chinese_full())

    def use_font(self, tag=None):
        '进行imgui字体的临时引用,用于with语法'
        if tag is None:
            tag = self.font_tag_zh
        return imgui.font(self.fonts[tag])

    def push_font(self, tag):
        '进行imgui字体的临时引用,用于push/pop语法'
        if tag is None:
            tag = self.font_tag_en
        imgui.push_font(self.fonts[tag])

    def clean(self):
        # 清空gl窗口背景
        gl.glClearColor(*self.bg_color)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        # 切换gl窗口的显示缓存,将最新渲染结果真实呈现在gl窗口中
        glfw.swap_buffers(self.main_win.window)

    def step(self):
        '进行imgui一帧窗口内容的绘制'
        # 清空gl窗口背景
        gl.glClearColor(*self.bg_color)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        # 进行前置事件处理
        glfw.poll_events()
        self.imgui_bk.process_inputs()
        # 准备绘制imgui窗口虚拟帧
        try:
            imgui.new_frame()
            # 调用实际app逻辑,进行ui绘制
            if not self.app.on_step():
                self.set_stop()
            # imgui窗口虚拟帧绘制结束
            imgui.end_frame()
            # 对imgui绘制的虚拟帧进行逻辑渲染
            imgui.render()
            # 使用imgui后端进行实际窗口帧的渲染
            self.imgui_bk.render(imgui.get_draw_data())
        except Exception as e:
            print(e)
        # 切换gl窗口的显示缓存,将最新渲染结果真实呈现在gl窗口中
        glfw.swap_buffers(self.main_win.window)

    def need_stop(self):
        '判断gl窗口是否需要关闭'
        return glfw.window_should_close(self.main_win.window)

    def set_stop(self):
        '设置,停止应用循环'
        glfw.set_window_should_close(self.main_win.window, 1)

    def is_key_down(self, keys):
        '检查是否有ctrl+字母等组合键被按下'
        if not keys: return False
        chars = keys.replace(' ', '').split('+')
        for key in chars:
            if key.lower() == 'ctrl':
                if not imgui.get_io().key_ctrl:
                    return False
                continue
            if key.lower() == 'alt':
                if not imgui.get_io().key_alt:
                    return False
                continue
            if key.lower() == 'shift':
                if not imgui.get_io().key_shift:
                    return False
                continue
            if len(key) > 1:
                continue
            char = key.upper()
            if not imgui.get_io().keys_down[ord(char)]:
                return False
        return True

    def is_key_press(self, keys):
        """检查指定的按键组合,是否被按下后又抬起"""
        if self.is_key_down(keys):
            self.keys_stat[keys] = 1
            return False
        else:
            if keys in self.keys_stat:
                del self.keys_stat[keys]
                return True

    def loop(self, delay=0.03):
        '进行imgui的主体循环,让gui真正的跑起来'
        while not self.need_stop():
            self.step()
            if delay:
                time.sleep(delay)

    def shutdown(self):
        '关闭imgui环境,一切都结束了'
        self.imgui_bk.shutdown()
        self.main_win.close()


# 简单运行模块的app与env功能封装函数
def im_env_loop(mod_class, title='测试imgui', width=1024, height=768, fullscreen=False):
    # 定义app对象
    app = imgui_app()
    # 给app对象增加mod模块
    app.append_mod(mod_class)
    # 定义env对象并绑定app
    im_env = imgui_env(app, title, width, height, fullscreen)
    # 进行env的事件循环
    im_env.loop()
    # 程序结束进行收尾
    im_env.shutdown()


if __name__ == "__main__":
    # 进行测试程序的运行
    im_env_loop(imgui_mod)
