import logging

class LogHandler():
    logger = None
    name: str = None

    def __init__(self, name):

        self.name = name
        # 로그 생성
        self.nameReplace()
        self.logger = logging.getLogger(self.name)

        # 로그의 출력 기준 설정
        self.logger.setLevel(logging.DEBUG)

        # log 출력 형식
        formatter = logging.Formatter('%(name)s - %(asctime)s - %(levelname)s - %(message)s')

        # log를 console에 출력
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)

        # log를 파일에 출력
        file_handler = logging.FileHandler("C:\\Dev\\Test\\" + 'macro4dia.log')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def debug(self, *args):
        self.logger.debug(self.messageConvert(args))

    def info(self, *args):
        self.logger.info(self.messageConvert(args))

    def warn(self, *args):
        self.logger.warn(self.messageConvert(args))

    def error(self, *args):
        self.logger.error(self.messageConvert(args))

    def messageConvert(self, *args):
        message = str()
        # 버그인가
        args = args[0]

        for param in args:
            dType = type(param)
            if not dType == "str":
                # print("TYPE:" ,type(param))
                if dType == "dict":
                    pDict: dict = dict(param)

                else:
                    param = str(param)

            message += param + " "

        return message

    # def getLogger(self):
    #   return self.logger
    def nameReplace(self):
        self.name = self.name.replace("__", "")