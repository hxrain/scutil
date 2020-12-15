import imgui
import glfw
import OpenGL.GL as gl

import os


class imgui_mod:
    'imgui应用app的功能逻辑模块'

    def on_mod(self, im):
        '''
            进行具体的应用逻辑绘制处理:im为imgui环境对象;返回值告知程序是否继续.
            此方法应该被子类重载,完成具体的功能逻辑
        '''
        running = True
        # 判断是否有ctrl+Q按下,结束app
        if im.is_ctrl_key('Q'):
            return False

        # 绘制主菜单条
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

        # 显示内置demo窗口与调试窗口
        imgui.show_demo_window()
        imgui.show_metrics_window()

        # 显示测试窗口
        imgui.begin("测试Window")

        imgui.begin_child("region", 150, 50, border=True)
        imgui.text("inside region")
        imgui.end_child()

        imgui.text("中hello英world文rain字test符sky串")
        imgui.text_colored("Eggs", 0.2, 1., 0.)
        imgui.text('pyimgui ver:' + imgui.__version__)
        imgui.text('imgui ver:' + imgui.get_version())
        imgui.end()
        return running


class imgui_app:
    'imgui应用程序基类'

    def __init__(self):
        self.mods = []
        pass

    def on_init(self, im):
        'app初始化:im为imgui环境对象'

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

    def on_step(self, im):
        '应用绘制的主逻辑:im为imgui环境对象;返回值告知程序是否继续.'
        return self.on_app(im)

    def on_app(self, im):
        '进行具体的应用逻辑绘制处理:im为imgui环境对象;返回值告知程序是否继续.'
        for m in self.mods:
            if not m.on_mod(im):
                return False
        return True

    def append_mod(self, mod_class):
        '创建mod_class对象并放入内部模块链表'
        self.mods.append(mod_class())

    def append_modobj(self, mod):
        '将mod对象放入内部模块链表'
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
        imgui.new_frame()
        # 调用实际app逻辑,进行ui绘制
        if not self.app.on_step(self):
            self.set_stop()
        # 对imgui绘制的虚拟帧进行逻辑渲染
        imgui.render()
        # imgui窗口虚拟帧绘制结束
        imgui.end_frame()
        # 使用imgui后端进行实际窗口帧的渲染
        self.imgui_bk.render(imgui.get_draw_data())
        # 切换gl窗口的显示缓存,将最新渲染结果真实呈现在gl窗口中
        glfw.swap_buffers(self.main_win.window)

    def need_stop(self):
        '判断gl窗口是否需要关闭'
        return glfw.window_should_close(self.main_win.window)

    def set_stop(self):
        '设置,停止应用循环'
        glfw.set_window_should_close(self.main_win.window, 1)

    def is_ctrl_key(self, char):
        '检查是否有ctrl+字母键组合被按下'
        if not imgui.get_io().key_ctrl:
            return False
        char = char.upper()
        return imgui.get_io().keys_down[ord(char)]

    def loop(self):
        '进行imgui的主体循环,让gui真正的跑起来'
        while not self.need_stop():
            self.step()

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
