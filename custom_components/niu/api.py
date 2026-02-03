from datetime import datetime, timedelta
import hashlib
import json

# from homeassistant.util import Throttle
from time import gmtime, strftime

import requests

from .const import *


class NiuApi:
    def __init__(self, username, password, scooter_id) -> None:
        self.username = username
        self.password = password
        self.scooter_id = int(scooter_id)

        self.dataBat = None
        self.dataMoto = None
        self.dataMotoInfo = None
        self.dataTrackInfo = None
        self.token = None
        self.sn = None
        self.sensor_prefix = None

        self.ver = "1.0.2024012503"

    def initApi(self):
        self.token = self.get_token()
        api_uri = MOTOINFO_LIST_API_URI
        vehicles_data = self.get_vehicles_info(api_uri)
        
        # 增加一些基本的错误检查，防止崩坏
        if not vehicles_data or "data" not in vehicles_data or "items" not in vehicles_data["data"]:
            raise Exception("Failed to get vehicle info from NIU API")
            
        self.sn = vehicles_data["data"]["items"][self.scooter_id]["sn_id"]
        self.sensor_prefix = vehicles_data["data"]["items"][self.scooter_id]["scooter_name"]
        
        self.updateBat()
        self.updateMoto()
        self.updateMotoInfo()
        self.updateTrackInfo()

    def get_token(self):
        username = self.username
        password = self.password

        url = ACCOUNT_BASE_URL + LOGIN_URI
        md5 = hashlib.md5(password.encode("utf-8")).hexdigest()
        data = {
            "account": username,
            "password": md5,
            "grant_type": "password",
            "scope": "base",
            "app_id": "niu_ktdrr960",
        }
        try:
            r = requests.post(url, data=data)
        except BaseException as e:
            print(e)
            return False
        
        try:
            data = json.loads(r.content.decode())
            return data["data"]["token"]["access_token"]
        except Exception:
            return False

    def get_vehicles_info(self, path):
        token = self.token
        url = API_BASE_URL + path
        headers = {"token": token}
        try:
            r = requests.get(url, headers=headers, data=[])
        except ConnectionError:
            return False
        if r.status_code != 200:
            return False
        data = json.loads(r.content.decode())
        return data

    def get_info(self, path):
        sn = self.sn
        token = self.token
        url = API_BASE_URL + path

        params = {"sn": sn}
        headers = {
            "token": token,
            "user-agent": "manager/4.10.4 (android; IN2020 11);lang=zh-CN;clientIdentifier=Domestic;timezone=Asia/Shanghai;model=IN2020;deviceName=IN2020;ostype=android",
        }
        try:
            r = requests.get(url, headers=headers, params=params)

        except ConnectionError:
            return False
        if r.status_code != 200:
            return False
        data = json.loads(r.content.decode())
        if data["status"] != 0:
            return False
        return data

    def post_info(self, path):
        sn, token = self.sn, self.token
        url = API_BASE_URL + path
        params = {}
        headers = {"token": token, "Accept-Language": "en-US"}
        try:
            r = requests.post(url, headers=headers, params=params, data={"sn": sn})
        except ConnectionError:
            return False
        if r.status_code != 200:
            return False
        data = json.loads(r.content.decode())
        if data["status"] != 0:
            return False
        return data

    def post_info_track(self, path):
        sn, token = self.sn, self.token
        url = API_BASE_URL + path
        params = {}
        headers = {
            "token": token,
            "Accept-Language": "en-US",
            "User-Agent": "manager/1.0.0 (identifier);clientIdentifier=identifier",
        }
        try:
            r = requests.post(
                url,
                headers=headers,
                params=params,
                json={"index": "0", "pagesize": 10, "sn": sn},
            )
        except ConnectionError:
            return False
        if r.status_code != 200:
            return False
        data = json.loads(r.content.decode())
        if data["status"] != 0:
            return False
        return data

    # [新增核心功能] 发送控制指令 (从改版B移植)
    def send_command(self, command_type: str):
        """
        发送控制命令到电动车。
        :param command_type: 命令类型，例如 "acc_on", "acc_off", "cushion_lock_on"
        """
        sn = self.sn
        token = self.token
        # 如果 token 丢失，尝试重新获取
        if not token:
            self.token = self.get_token()
            token = self.token
            if not token: return False

        # 注意：这里使用的是发送指令专用的 URL，和获取数据的不同
        url = API_BASE_URL + "/v5/cmd/creat"
        headers = {
            "token": token,
            "Content-Type": "application/json; charset=utf-8",
            # 使用更通用的 User-Agent 模拟手机端
            "User-Agent": "manager/5.12.4 (iPhone; iOS 18.5; Scale/3.00);deviceName=iPhone;timezone=Asia/Shanghai;model=iPhone13,4;lang=zh-CN;ostype=iOS;clientIdentifier=Domestic"
        }
        payload = json.dumps({"sn": sn, "type": command_type})

        try:
            r = requests.post(url, headers=headers, data=payload)
            if r.status_code != 200:
                return False
            response_data = r.json()
            if response_data.get("status") == 0:
                return True
            else:
                return False
        except Exception:
            return False

    def getDataBat(self, id_field):
        return self.dataBat["data"]["batteries"]["compartmentA"][id_field]

    def getDataMoto(self, id_field):
        return self.dataMoto["data"][id_field]

    def getDataDist(self, id_field):
        return self.dataMoto["data"]["lastTrack"][id_field]

    def getDataPos(self, id_field):
        return self.dataMoto["data"]["postion"][id_field]

    def getDataOverall(self, id_field):
        return self.dataMotoInfo["data"][id_field]

    def getDataTrack(self, id_field):
        if id_field == "startTime" or id_field == "endTime":
            return datetime.fromtimestamp(
                (self.dataTrackInfo["data"][0][id_field]) / 1000
            ).strftime("%Y-%m-%d %H:%M:%S")
        if id_field == "ridingtime":
            return strftime("%H:%M:%S", gmtime(self.dataTrackInfo["data"][0][id_field]))
        if id_field == "track_thumb":
            thumburl = self.dataTrackInfo["data"][0][id_field].replace(
                "app-api.niucache.com", "app-api.niu.com"
            )
            return thumburl
        return self.dataTrackInfo["data"][0][id_field]

    def updateBat(self):
        self.dataBat = self.get_info(MOTOR_BATTERY_API_URI)

    def updateMoto(self):
        self.dataMoto = self.get_info(MOTOR_INDEX_API_URI)

    def updateMotoInfo(self):
        self.dataMotoInfo = self.post_info(MOTOINFO_ALL_API_URI)

    def updateTrackInfo(self):
        self.dataTrackInfo = self.post_info_track(TRACK_LIST_API_URI)
