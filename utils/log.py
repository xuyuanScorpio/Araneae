#*-*coding:utf8*-*

import re
import thread
import logging
import inspect

from Araneae.net.rpc import RPCNativeBase
from termcolor import colored

def set_logging(level, filename, fmt, datefmt):
    logging.basicConfig(level=level,
                        format=fmt,
                        datefmt=datefmt,
                        filename=filename)


#更换颜色
def color_string(string, color):
    return colored(string, color)


def Plog(msg, color=None):
    msg = color_string(msg, color=color) if color else msg
    print msg


def debug(msg, color=None):
    msg = color_string(msg, color=color) if color else msg
    logging.debug(msg)


def info(msg, color=None):
    msg = color_string(msg, color=color) if color else msg
    logging.info(msg)


def error(msg, color=None):
    msg = color_string(msg, color=color) if color else msg
    logging.error(msg)


def critical(msg, color=None):
    msg = color_string(msg, color=color) if color else msg
    logging.critical(msg)

#  实现基本的 Logger 类，使用 logging.getLogger(logger_name) 获取对象
#  当构造函数 name 参数字符串以 '.log' 结尾时，写入文件。否则直接打印在 console 上
#  只有打印在 console 上的 message 才根据 logLevel 区分颜色
class BaseLogger(logging.Logger):
    def __init__(self, name):
        logging.Logger.__init__(self, name, logging.DEBUG)

        self.__isLogFile = re.match(r'.+\.log$', name)

        if self.__isLogFile:
            self.__fhandler = logging.FileHandler(name)
        else:
            self.__fhandler = logging.StreamHandler()

        formatter = logging.Formatter("%(asctime)s [%(process)d:%(thread)d] [%(chain)s] %(message)s")
        self.__fhandler.setFormatter(formatter)

        self.addHandler(self.__fhandler)

    def get_class_from_frame(self, fr):
        args, _, _, value_dict = inspect.getargvalues(fr)

        if len(args) and args[0] == 'self':
            instance = value_dict.get('self', None)

            if instance:
                return getattr(instance, '__class__', None)
        return None

    def get_file_name_in_full_path(self, file_path):
        return file_path.split('/')[-1]

    def get_meta_data(self):
        frames = inspect.stack()
        chain_list = []

        for i in range(0, len(frames)):
            _, file_path, _, func_name, _, _ = frames[i]
            file_name = self.get_file_name_in_full_path(file_path)

            try:
                args = re.findall('\((.*)\)', frames[i + 1][-2][0])[0]
            except IndexError, e:
                func_name = self.get_class_from_frame(frames[2][0]).__name__
                args = ''

            current_chain = '%s:%s(%s)' % (file_name, func_name, args)
            chain_list.append(current_chain)
        chain_list.reverse()
        return ' --> '.join(chain_list[:-2])

    def get_simple_meta_data(self):
        frames = inspect.stack()
        obj, file_path, line_no, func_name, _, _ = frames[3]
        return (func_name + ':' + str(line_no))

    def debug(self, msg, *args, **kw):
        chain = self.get_meta_data()

        if self.__isLogFile:
            self.log(logging.DEBUG, "%s" % msg, extra={'chain': chain}, *args, **kw)
        else:
            coloredMsg = colored(msg, color='green')
            self.log(logging.DEBUG, "%s" % coloredMsg, extra={'chain': chain}, *args, **kw)

    def info(self, msg, *args, **kw):
        chain = self.get_simple_meta_data()

        if self.__isLogFile:
            self.log(logging.INFO, "%s" % msg, extra={'chain': chain}, *args, **kw)
        else:
            coloredMsg = colored(msg, color='yellow')
            self.log(logging.INFO, "%s" % coloredMsg, extra={'chain': chain}, *args, **kw)

    def warn(self, msg, *args, **kw):
        chain = self.get_simple_meta_data()

        if self.__isLogFile:
            self.log(logging.WARNING, "%s" % msg, extra={'chain': chain}, *args, **kw)
        else:
            coloredMsg = colored(msg, color='red')
            self.log(logging.WARNING, "%s" % coloredMsg, extra={'chain': chain}, *args, **kw)

    def error(self, msg, *args, **kw):
        chain = self.get_meta_data()

        if self.__isLogFile:
            self.log(logging.ERROR, "%s" % msg, extra={'chain': chain}, *args, **kw)
        else:
            coloredMsg = colored(msg, color='grey')
            self.log(logging.ERROR, "%s" % coloredMsg, extra={'chain': chain}, *args, **kw)

    @classmethod
    def instance(cls, logName):
        logging.setLoggerClass(cls)
        return logging.getLogger(logName)


#  通过修改本地配置文件动态修改 log 级别
class LocalLevelChangeLogger(BaseLogger):
    def __init__(self, name):
        super(LocalLevelChangeLogger, self).__init__(name)

        self.__currentLevel = logging.DEBUG
        thread.start_new_thread(self.__config_checking_loop)

    #  此处要引入 log.conf 配置文件。通过修改 logLevel 配置动态修改打印级别
    def __config_checking_loop(self):
        pass


#  统一对外提供 log 接口和 native 服务
#  目前只支持远程修改 log 级别。未来可以扩展远程写 log 文件等功能
class RPCLoggerManager(RPCNativeBase):
    def __init__(self):
        self.__loggers = dict()

        super(RPCLoggerManager, self).__init__(self, 9090)
        self.startNative()

    def addLogger(self, loggerName, loggerObject):
        self.__loggers[loggerName] = loggerObject

    def setLevel(self, loggerName, levelNum):
        try:
            loggerObject = self.__loggers[loggerName]
            loggerObject.setLevel(levelNum)
        except (BaseException) as e:
            print "loggerName[%s] can not found Exception[%s] ERROR!!" % (loggerName, str(e))

#g_rpcLogManager = RPCLoggerManager()


# 通过 RPC 接口调用动态修改 log 级别
class RPCLevelChangeLogger(BaseLogger):
    def __init__(self, name):
        super(RPCLevelChangeLogger, self).__init__(name)
        g_rpcLogManager.addLogger(name, self)


def test_logger_threadFunction(loggerObject):

    for i in range(100):
        loggerObject.debug('DEBUG Message thread test:%d' % i)
        loggerObject.info('INFO Message thread test:%d' % i)
        loggerObject.warn('WARNING Message thread test:%d' % i)
        loggerObject.error('ERROR Message thread test:%d' % i)
        loggerObject.error('End 2:%d' % i)
        time.sleep(3)


if __name__ == '__main__':

    import time

    bl = BaseLogger.instance('baseSpider.log')
    rl = RPCLevelChangeLogger.instance('rpcSpider.log')
    ll = LocalLevelChangeLogger.instance('localSpider.log')

    bl.debug("DEBUG message")
    rl.info("INFO message2")
    ll.error("ERROR message")

    ##################################################################################

    #  先设置要使用哪个类型的 logger，然后获取该类型的 logger 对象
    logging.setLoggerClass(BaseLogger)
    rrclogger = logging.getLogger("ruleSpider.log")
    rrclogger1 = logging.getLogger("ruleSpider_1.log")

    #  设置 logger 类型，并获取对象
    logging.setLoggerClass(RPCLevelChangeLogger)
    rrclogger2 = logging.getLogger("ruleSpider_2")

    ##################################################################################
    rrclogger.debug("DEBUG message")
    rrclogger1.debug("DEBUG message1")
    rrclogger2.info("INFO message2")
    rrclogger.info("INFO message")
    rrclogger.warn("warning with prefix")
    rrclogger1.warn("warning with prefix1")

    # 测试不同线程写入同一个 .log 文件
    for i in range(4):
        thread.start_new_thread(test_logger_threadFunction, (rrclogger, ))

    #  循环打印，启动 logger_proxy.py 测试 rpc 更改 logLevel
    for i in range(100):
        rrclogger2.debug("DEBUG Message 2:%d" % i)
        rrclogger2.info("INFO Message 2:%d" % i)
        rrclogger2.warn("WARNING Message 2:%d" % i)
        rrclogger2.error("ERROR Message 2:%d" % i)
        rrclogger2.error("End 2:%d" % i)
        time.sleep(3)

    time.sleep(10)
