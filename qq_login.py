# Generated by Selenium IDE
import subprocess
import webbrowser

import win32api
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from config import *
from log import logger, color
from update import get_netdisk_addr


class LoginResult(ConfigInterface):
    def __init__(self, uin="", skey="", openid="", p_skey="", vuserid="", qc_openid="", qc_k=""):
        super().__init__()
        # 使用炎炎夏日活动界面得到
        self.uin = uin
        self.skey = skey
        # 登录QQ空间得到
        self.p_skey = p_skey
        # 使用心悦活动界面得到
        self.openid = openid
        # 使用腾讯视频相关页面得到
        self.vuserid = vuserid
        # 登录电脑管家页面得到
        self.qc_openid = qc_openid
        self.qc_k = qc_k


class QQLogin():
    login_mode_normal = "normal"
    login_mode_xinyue = "xinyue"
    login_mode_qzone = "qzone"
    login_mode_guanjia = "guanjia"
    login_mode_wegame = "wegame"

    bandizip_executable_path = os.path.realpath("./bandizip_portable/bz.exe")
    chrome_driver_executable_path = os.path.realpath("./chromedriver_87.exe")
    chrome_binary_7z = os.path.realpath("./chrome_portable_87.7z")
    chrome_binary_directory = os.path.realpath("./chrome_portable_87")
    chrome_binary_location = os.path.realpath("./chrome_portable_87/chrome.exe")

    def __init__(self, common_config):
        self.cfg = common_config  # type: CommonConfig
        self.driver = None  # type: WebDriver

    def prepare_chrome(self, login_type):
        logger.info(color("fg_bold_cyan") + "正在初始化chrome driver，用以进行【{}】相关操作".format(login_type))
        caps = DesiredCapabilities().CHROME
        # caps["pageLoadStrategy"] = "normal"  #  Waits for full page load
        caps["pageLoadStrategy"] = "none"  # Do not wait for full page load

        options = Options()
        if not self.cfg._debug_show_chrome_logs:
            options.add_experimental_option("excludeSwitches", ["enable-logging"])
        if self.cfg.run_in_headless_mode:
            logger.warning("已配置使用headless模式运行chrome")
            options.headless = True

        inited = False

        try:
            if not self.cfg.force_use_portable_chrome:
                # 如果未强制使用便携版chrome，则首先尝试使用系统安装的chrome
                self.driver = webdriver.Chrome(executable_path=self.chrome_driver_executable_path, desired_capabilities=caps, options=options)
                logger.info("使用自带chrome")
                inited = True
        except:
            pass

        if not inited:
            # 如果找不到，则尝试使用打包的便携版chrome
            # 先判定本地是否有便携版压缩包，若无则提示去网盘下载
            if not os.path.isfile(self.chrome_binary_7z):
                msg = (
                    "当前电脑未发现合适版本chrome浏览器版本，且当前目录无便携版chrome浏览器的压缩包({zip_name})\n"
                    "请在稍后打开的网盘页面中下载[{zip_name}]，并放到小助手的exe所在目录（注意：是把这个压缩包原原本本地放到这个目录里，而不是解压后再放过来！！！），然后重新打开程序~\n"
                    "如果之前版本已经下载过这个文件，可以直接去之前版本复制过来~不需要再下载一次~\n"
                ).format(zip_name=os.path.basename(self.chrome_binary_7z))
                win32api.MessageBox(0, msg, "出错啦", win32con.MB_ICONERROR)
                webbrowser.open(get_netdisk_addr(self.cfg))
                os.system("PAUSE")
                exit(-1)

            # 先判断便携版chrome是否已解压
            if not os.path.isdir(self.chrome_binary_directory):
                logger.info("自动解压便携版chrome到当前目录")
                subprocess.call([self.bandizip_executable_path, "x", "-target:auto", self.chrome_binary_7z])

            # 然后使用本地的chrome来初始化driver对象
            options.binary_location = self.chrome_binary_location
            # you may need some other options
            options.add_argument('--no-sandbox')
            options.add_argument('--no-default-browser-check')
            options.add_argument('--no-first-run')
            self.driver = webdriver.Chrome(executable_path=self.chrome_driver_executable_path, desired_capabilities=caps, options=options)
            logger.info("使用便携版chrome")

        self.cookies = self.driver.get_cookies()

    def destroy_chrome(self):
        if self.driver is not None:
            # 最小化网页
            self.driver.minimize_window()
            threading.Thread(target=self.driver.quit, daemon=True).start()

    def login(self, account, password, login_mode="normal"):
        """
        自动登录指定账号，并返回登陆后的cookie中包含的uin、skey数据
        :param account: 账号
        :param password: 密码
        :rtype: LoginResult
        """
        logger.info("即将开始自动登录，无需任何手动操作，等待其完成即可")
        logger.info("如果出现报错，可以尝试调高相关超时时间然后重新执行脚本")

        def login_with_account_and_password():
            # 选择密码登录
            self.driver.find_element(By.ID, "switcher_plogin").click()
            # 输入账号
            self.driver.find_element(By.ID, "u").send_keys(account)
            # 输入密码
            self.driver.find_element(By.ID, "p").send_keys(password)
            # 发送登录请求
            logger.info("等待一会，确保登录键可以点击")
            time.sleep(3)
            self.driver.find_element(By.ID, "login_button").click()

        return self._login("账密自动登录", login_action_fn=login_with_account_and_password, need_human_operate=False, login_mode=login_mode)

    def qr_login(self, login_mode="normal"):
        """
        二维码登录，并返回登陆后的cookie中包含的uin、skey数据
        :rtype: LoginResult
        """
        logger.info("即将开始扫码登录，请在弹出的网页中扫码登录~")
        return self._login("扫码登录", login_mode=login_mode)

    def _login(self, login_type, login_action_fn=None, need_human_operate=True, login_mode="normal"):
        for idx in range(self.cfg.login.max_retry_count):
            idx += 1
            try:
                self.login_mode = login_mode
                login_fn = self._login_real
                suffix = ""
                if login_mode == self.login_mode_xinyue:
                    login_fn = self._login_xinyue_real
                    suffix += "-心悦"
                elif login_mode == self.login_mode_qzone:
                    login_fn = self._login_qzone
                    suffix += "-QQ空间业务（如抽卡等需要用到）（不启用QQ空间系活动就不会触发本类型的登录）"
                elif login_mode == self.login_mode_guanjia:
                    login_fn = self._login_guanjia
                    suffix += "-电脑管家（如电脑管家蚊子腿需要用到）"
                elif login_mode == self.login_mode_wegame:
                    login_fn = self._login_wegame
                    suffix += "-wegame（获取wegame相关api需要用到）"

                ctx = login_type + suffix
                self.prepare_chrome(ctx)

                return login_fn(ctx, login_action_fn=login_action_fn, need_human_operate=need_human_operate)
            except Exception as e:
                logger.exception("第{}/{}次尝试登录出错，等待{}秒后重试".format(idx, self.cfg.login.max_retry_count, self.cfg.login.retry_wait_time), exc_info=e)
                time.sleep(self.cfg.login.retry_wait_time)
            finally:
                self.destroy_chrome()

    def _login_real(self, login_type, login_action_fn=None, need_human_operate=True):
        """
        通用登录逻辑，并返回登陆后的cookie中包含的uin、skey数据
        :rtype: LoginResult
        """

        def switch_to_login_frame_fn():
            logger.info("打开活动界面")
            self.driver.get("https://dnf.qq.com/lbact/a20200716wgmhz/index.html")

            self.set_window_size()

            logger.info("等待登录按钮#dologin出来，确保加载完成")
            WebDriverWait(self.driver, self.cfg.login.load_page_timeout).until(expected_conditions.visibility_of_element_located((By.ID, "dologin")))

            logger.info("点击登录按钮")
            self.driver.find_element(By.ID, "dologin").click()

            logger.info("等待#loginIframe显示出来并切换")
            WebDriverWait(self.driver, self.cfg.login.load_login_iframe_timeout).until(expected_conditions.visibility_of_element_located((By.ID, "loginIframe")))
            loginIframe = self.driver.find_element_by_id("loginIframe")
            self.driver.switch_to.frame(loginIframe)

        def assert_login_finished_fn():
            logger.info("请等待#logined的div可见，则说明已经登录完成了...")
            WebDriverWait(self.driver, self.cfg.login.login_finished_timeout).until(expected_conditions.visibility_of_element_located((By.ID, "logined")))

        self._login_common(login_type, switch_to_login_frame_fn, assert_login_finished_fn, login_action_fn, need_human_operate)

        # 从cookie中获取uin和skey
        return LoginResult(uin=self.get_cookie("uin"), skey=self.get_cookie("skey"),
                           p_skey=self.get_cookie("p_skey"), vuserid=self.get_cookie("vuserid"))

    def _login_qzone(self, login_type, login_action_fn=None, need_human_operate=True):
        """
        通用登录逻辑，并返回登陆后的cookie中包含的uin、skey数据
        :rtype: LoginResult
        """

        def switch_to_login_frame_fn():
            logger.info("打开活动界面")
            self.driver.get("https://act.qzone.qq.com/")

            self.set_window_size()

            logger.info("等待登录按钮#dologin出来，确保加载完成")
            WebDriverWait(self.driver, self.cfg.login.load_page_timeout).until(expected_conditions.visibility_of_element_located((By.LINK_TEXT, "[登录]")))

            logger.info("点击登录按钮")
            self.driver.find_element(By.LINK_TEXT, "[登录]").click()

            logger.info("等待#loginIframe显示出来并切换")
            time.sleep(1)
            self.driver.switch_to.frame(0)

        def assert_login_finished_fn():
            logger.info("请等待【欢迎你，】的文字可见，则说明已经登录完成了...")
            self.driver.get("https://act.qzone.qq.com/")
            WebDriverWait(self.driver, self.cfg.login.login_finished_timeout).until(expected_conditions.text_to_be_present_in_element((By.CSS_SELECTOR, ".tit_text"), "欢迎你，"))

        self._login_common(login_type, switch_to_login_frame_fn, assert_login_finished_fn, login_action_fn, need_human_operate)

        # 从cookie中获取uin和skey
        return LoginResult(p_skey=self.get_cookie("p_skey"),
                           uin=self.get_cookie("uin"), skey=self.get_cookie("skey"), vuserid=self.get_cookie("vuserid"))

    def _login_guanjia(self, login_type, login_action_fn=None, need_human_operate=True):
        """
        通用登录逻辑，并返回登陆后的cookie中包含的uin、skey数据
        :rtype: LoginResult
        """

        def switch_to_login_frame_fn():
            logger.info("打开活动界面")
            self.driver.get("http://guanjia.qq.com/act/cop/202012dnf/")

            self.set_window_size()

            logger.info("等待登录按钮#dologin出来，确保加载完成")
            WebDriverWait(self.driver, self.cfg.login.load_page_timeout).until(expected_conditions.visibility_of_element_located((By.ID, "dologin")))

            logger.info("点击登录按钮")
            self.driver.find_element(By.ID, "dologin").click()

            logger.info("等待#login_ifr显示出来并切换")
            WebDriverWait(self.driver, self.cfg.login.load_login_iframe_timeout).until(expected_conditions.visibility_of_element_located((By.ID, "login_ifr")))
            loginIframe = self.driver.find_element_by_id("login_ifr")
            self.driver.switch_to.frame(loginIframe)

            logger.info("等待#login_ifr#ptlogin_iframe加载完毕并切换")
            WebDriverWait(self.driver, self.cfg.login.load_login_iframe_timeout).until(expected_conditions.visibility_of_element_located((By.ID, "ptlogin_iframe")))
            ptlogin_iframe = self.driver.find_element_by_id("ptlogin_iframe")
            self.driver.switch_to.frame(ptlogin_iframe)

        def assert_login_finished_fn():
            logger.info("请等待#logined的div可见，则说明已经登录完成了...")
            WebDriverWait(self.driver, self.cfg.login.login_finished_timeout).until(expected_conditions.visibility_of_element_located((By.ID, "logined")))

        self._login_common(login_type, switch_to_login_frame_fn, assert_login_finished_fn, login_action_fn, need_human_operate)

        # 从cookie中获取uin和skey
        return LoginResult(qc_openid=self.get_cookie("__qc__openid"), qc_k=self.get_cookie("__qc__k"),
                           uin=self.get_cookie("uin"), skey=self.get_cookie("skey"), p_skey=self.get_cookie("p_skey"), vuserid=self.get_cookie("vuserid"))

    def _login_wegame(self, login_type, login_action_fn=None, need_human_operate=True):
        """
        通用登录逻辑，并返回登陆后的cookie中包含的uin、skey数据
        :rtype: LoginResult
        """

        def switch_to_login_frame_fn():
            logger.info("打开活动界面")
            self.driver.get("https://www.wegame.com.cn/")

            self.set_window_size()

            logger.info("等待登录按钮#dologin出来，确保加载完成")
            time.sleep(self.cfg.login.open_url_wait_time)
            WebDriverWait(self.driver, self.cfg.login.load_page_timeout).until(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, ".widget-header-login-btn")))

            logger.info("点击登录按钮")
            self.driver.find_element(By.CSS_SELECTOR, ".widget-header-login-btn").click()

            logger.info("等待#loginIframe显示出来并切换")
            time.sleep(self.cfg.login.load_login_iframe_timeout)
            self.driver.switch_to.frame(self.driver.find_element_by_css_selector("div.widget-login-item.widget-login-item--qq > iframe"))

        def assert_login_finished_fn():
            logger.info("请等待【登录头像】可见，则说明已经登录完成了...")
            # self.driver.get("https://www.wegame.com.cn/")
            WebDriverWait(self.driver, self.cfg.login.login_finished_timeout).until(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, ".widget-header-login-info")))

        self._login_common(login_type, switch_to_login_frame_fn, assert_login_finished_fn, login_action_fn, need_human_operate)

        # 从cookie中获取uin和skey
        return LoginResult(uin=self.get_cookie("uin"), skey=self.get_cookie("skey"), p_skey=self.get_cookie("p_skey"))

    def _login_xinyue_real(self, login_type, login_action_fn=None, need_human_operate=True):
        """
        通用登录逻辑，并返回登陆后的cookie中包含的uin、skey数据
        :rtype: LoginResult
        """

        def switch_to_login_frame_fn():
            logger.info("打开活动界面")
            self.driver.get("https://xinyue.qq.com/act/a20181101rights/index.html")

            self.set_window_size()

            logger.info("等待#loginframe加载完毕并切换")
            WebDriverWait(self.driver, self.cfg.login.load_login_iframe_timeout).until(expected_conditions.visibility_of_element_located((By.CLASS_NAME, "loginframe")))
            login_frame = self.driver.find_element_by_class_name("loginframe")
            self.driver.switch_to.frame(login_frame)

            logger.info("等待#loginframe#ptlogin_iframe加载完毕并切换")
            WebDriverWait(self.driver, self.cfg.login.load_login_iframe_timeout).until(expected_conditions.visibility_of_element_located((By.ID, "ptlogin_iframe")))
            ptlogin_iframe = self.driver.find_element_by_id("ptlogin_iframe")
            self.driver.switch_to.frame(ptlogin_iframe)

        def assert_login_finished_fn():
            logger.info("请等待#btn_wxqclogin可见，则说明已经登录完成了...")
            WebDriverWait(self.driver, self.cfg.login.login_finished_timeout).until(expected_conditions.invisibility_of_element_located((By.ID, "btn_wxqclogin")))

            logger.info("等待1s，确认获取openid的请求完成")
            time.sleep(1)

            # 确保openid已设置
            for t in range(3):
                t += 1
                if self.driver.get_cookie('openid') is None:
                    logger.info("第{}/3未在心悦的cookie中找到openid，等一秒再试".format(t))
                    time.sleep(1)
                    continue
                break

        self._login_common(login_type, switch_to_login_frame_fn, assert_login_finished_fn, login_action_fn, need_human_operate)

        # 从cookie中获取openid
        return LoginResult(openid=self.get_cookie("openid"))

    def _login_common(self, login_type, switch_to_login_frame_fn, assert_login_finished_fn, login_action_fn=None, need_human_operate=True):
        """
        通用登录逻辑，并返回登陆后的cookie中包含的uin、skey数据
        :rtype: LoginResult
        """
        switch_to_login_frame_fn()

        logger.info("等待#loginframe#ptlogin_iframe#switcher_plogin加载完毕")
        WebDriverWait(self.driver, self.cfg.login.load_login_iframe_timeout).until(expected_conditions.visibility_of_element_located((By.ID, 'switcher_plogin')))

        if need_human_operate:
            logger.info("请在{}s内完成{}操作".format(self.cfg.login.login_timeout, login_type))

        # 实际登录的逻辑，不同方式的处理不同，这里调用外部传入的函数
        logger.info("开始{}流程".format(login_type))
        if login_action_fn is not None:
            login_action_fn()

        self.try_auto_resolve_captcha()

        logger.info("等待登录完成（也就是#loginIframe#login登录框消失）")
        # 出验证码的时候，下面这个操作可能会报错 'target frame detached\n(Session info: chrome=87.0.4280.88)'
        # 这时候等待一下好像就行了
        for i in range(3):
            try:
                WebDriverWait(self.driver, self.cfg.login.login_timeout).until(expected_conditions.invisibility_of_element_located((By.ID, "login")))
                break
            except Exception as e:
                logger.error("出错了，等待两秒再重试", exc_info=e)
                time.sleep(2)

        logger.info("回到主iframe")
        self.driver.switch_to.default_content()

        assert_login_finished_fn()

        logger.info("登录完成")

        self.cookies = self.driver.get_cookies()

        if self.login_mode == self.login_mode_normal:
            # 普通登录额外获取腾讯视频的vqq_vuserid
            logger.info("转到qq视频界面，从而可以获取vuserid，用于腾讯视频的蚊子腿")
            self.driver.get("https://m.film.qq.com/magic-act/110254/index.html")
            for i in range(5):
                vuserid = self.driver.get_cookie('vuserid')
                if vuserid is not None:
                    break
                time.sleep(1)
            self.add_cookies(self.driver.get_cookies())
        elif self.login_mode == self.login_mode_qzone:
            pass
            # logger.info("QQ空间登录类型额外访问一下征集令活动界面，然后还得刷新一遍浏览器，不然不刷新次数（什么鬼）")
            # logger.info("第一次访问，并停留5秒")
            # self.driver.get("https://act.qzone.qq.com/vip/2020/dnf1126")
            # time.sleep(5)
            # logger.info("第二次访问，并停留5秒")
            # self.driver.get("https://act.qzone.qq.com/vip/2020/dnf1126")
            # time.sleep(5)
            # logger.info("OK，理论上次数应该刷新了")

        return

    def try_auto_resolve_captcha(self):
        if not self.cfg.login.auto_resolve_captcha:
            logger.info("未启用自动处理拖拽验证码的功能")
            return

        captcha_try_count = 0
        try:
            WebDriverWait(self.driver, self.cfg.login.open_url_wait_time).until(expected_conditions.visibility_of_element_located((By.ID, "tcaptcha_iframe")))
            tcaptcha_iframe = self.driver.find_element_by_id("tcaptcha_iframe")
            self.driver.switch_to.frame(tcaptcha_iframe)

            drag_tarck_width = self.driver.find_element_by_id('slide').size['width']  # 进度条轨道宽度
            drag_block_width = self.driver.find_element_by_id('slideBlock').size['width']  # 缺失方块宽度
            delta_width = drag_block_width // 4  # 每次尝试多移动1/4个缺失方块的宽度

            drag_button = self.driver.find_element_by_id('tcaptcha_drag_button')  # 进度条按钮

            logger.info("先release滑块一次，以避免首次必定失败的问题")
            ActionChains(self.driver).release(on_element=drag_button).perform()

            # 根据经验，缺失验证码大部分时候出现在右侧，所以从右侧开始尝试
            xoffset = drag_tarck_width - drag_block_width - delta_width
            logger.info("开始拖拽验证码，轨道宽度为{}，滑块宽度为{}，首次尝试偏移量为{}".format(drag_tarck_width, drag_block_width, xoffset))
            while xoffset > 0:
                captcha_try_count += 1
                logger.info("开始尝试第{}次拖拽验证码，本次尝试偏移量为{}".format(captcha_try_count, xoffset))

                ActionChains(self.driver).click_and_hold(on_element=drag_button).perform()  # 左键按下
                time.sleep(0.2)
                ActionChains(self.driver).move_by_offset(xoffset=xoffset, yoffset=0).perform()  # 将滑块向右滑动指定距离
                time.sleep(0.2)
                ActionChains(self.driver).release(on_element=drag_button).perform()  # 左键放下，完成一次验证尝试
                time.sleep(0.2)

                xoffset -= delta_width
                time.sleep(1)

            self.driver.switch_to.parent_frame()
        except StaleElementReferenceException as e:
            logger.info("成功完成了拖拽验证码操作，总计尝试次数为{}".format(captcha_try_count))
        except TimeoutException as e:
            logger.info("看上去没有出现验证码")

    def set_window_size(self):
        logger.info("浏览器设为1936x1056")
        self.driver.set_window_size(1936, 1056)

    def add_cookies(self, cookies):
        to_add = []
        for cookie in cookies:
            if self.get_cookie(cookie['name']) == "":
                to_add.append(cookie)

        self.cookies.extend(to_add)

    def get_cookie(self, name):
        for cookie in self.cookies:
            if cookie['name'] == name:
                return cookie['value']
        return ''

    def print_cookie(self):
        for cookie in self.cookies:
            print("{:20s} {:20s} {}".format(cookie['domain'], cookie['name'], cookie['value']))


if __name__ == '__main__':
    # 读取配置信息
    load_config("config.toml", "config.toml.local")
    cfg = config()

    ql = QQLogin(cfg.common)
    account = cfg.account_configs[0]
    acc = account.account_info
    logger.warning("测试账号 {} 的登录情况".format(account.name))
    lr = ql.login(acc.account, acc.password, login_mode=ql.login_mode_normal)
    # lr = ql.qr_login()
    ql.print_cookie()
    print(lr)
