import requests
import json
import yagmail
import re
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from base64 import b64encode
import urllib.parse


def MsgSend(message_title, message_info):
    print("Entering MsgSend function")
    if os.environ['mail_address']:
        print("Attempting email send")
        mail = yagmail.SMTP(os.environ['mail_address'],
                            os.environ['mail_password'], os.environ['mail_host'])
        try:
            mail.send(os.environ['receive_mail'], message_title, message_info)
            print("Email sent successfully")
        except Exception as e:
            print("推送出错！", str(e))
    if os.environ['sct_ftqq']:
        print("Attempting Server酱 send")
        try:
            requests.get(f'https://sctapi.ftqq.com/{os.environ["sct_ftqq"]}.send?{urllib.parse.urlencode({"title":message_title, "desp":message_info})}')
            print("Server酱 sent successfully")
        except Exception as e:
            print("推送出错！", str(e))

def encrypt(t, e):
    print("Entering encrypt function")
    t = str(t)
    key = e.encode('utf-8')
    cipher = AES.new(key, AES.MODE_ECB)
    padded_text = pad(t.encode('utf-8'), AES.block_size)
    encrypted_text = cipher.encrypt(padded_text)
    print("Encryption completed")
    return b64encode(encrypted_text).decode('utf-8')


# 获取学校ID
def get_school_id(school_name):
    print("Entering get_school_id function")
    headers00 = {
    "accept": "application/json, text/plain, */*",
    "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1 Edg/119.0.0.0"}
    url00 = "https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/getSchoolList"
    response00 = requests.get(url00, headers=headers00)
    data = json.loads(response00.text)['data']
    for school in data:
        if school['name'] == school_name:
            print(f"School ID found: {school['id']}")
            return school['id']
    print("No school ID found")
    return None

def Login(headers, username, password):
    print("Entering Login function")
    key = (str(username) + "0000000000000000")[:16]
    encrypted_text = encrypt(password, key)
    login_url = 'https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/username'
    params = {
        "schoolId": school_id,
        "username": username,
        "password": encrypted_text
    }
    login_req = requests.post(login_url, params=params, headers=headers)
    text = json.loads(login_req.text)
    if text['code'] == 0:
        print(f"{username}账号登陆成功！")
        set_cookie = login_req.headers['Set-Cookie']
        jws = re.search(r'JWSESSION=(.*?);', str(set_cookie)).group(1)
        return jws
    else:
        print(f"{username}登陆失败，请检查账号密码！")
        return False


# 获取我的日志
def GetMySignLogs(headers):
    print("Entering GetMySignLogs function")
    url = 'https://gw.wozaixiaoyuan.com/sign/mobile/receive/getMySignLogs'
    params = {
        'page': 1,
        'size': 10
    }
    data = requests.get(url, headers= headers, params=params).json()['data'][0]
    if int(data['signStatus']) != 1:
        print("用户已打过卡！")
        return False, False, False
    signId, userArea, id, areaData = data['signId'], data['userArea'], data['id'], data['areaList']
    print(f"Sign ID: {signId}, ID: {id}")
    for _ in areaData:
        if userArea == _['name']:
            dataStr = _['dataStr'] if ('dataStr' in _) else ('[{"longitude": %s, "latitude": %s}]' % (_['longitude'], _['latitude']))
            dataJson = {
                "type": 1,
                "polygon": dataStr,
                "id": _['id'],
                "name": _['name'],
            }
            print("Area data found")
            return signId, id, dataJson
    print("No area data matched")
    return False, False, False


def GetPunchData(username, location, tencentKey, dataJson):
    print("Entering GetPunchData function")
    geocode = requests.get("https://apis.map.qq.com/ws/geocoder/v1", params={"address": location, "key": tencentKey})
    geocode_data = json.loads(geocode.text)
    if geocode_data['status'] == 0:
        print("Geocode successful")
        reverseGeocode = requests.get("https://apis.map.qq.com/ws/geocoder/v1", params={"location": f"{geocode_data['result']['location']['lat']},{geocode_data['result']['location']['lng']}", "key": tencentKey})
        reverseGeocode_data = json.loads(reverseGeocode.text)
        if reverseGeocode_data['status'] == 0:
            print("Reverse geocode successful")
            # 将 polygon 从字符串转换为列表
            dataJson['polygon'] = json.loads(dataJson['polygon'])
            location_data = reverseGeocode_data['result']
            PunchData = {
                "latitude": location_data['location']['lat'],
                "longitude": location_data['location']['lng'],
                "nationcode": "",
                "country": "中国",
                "province": location_data['ad_info']['province'],
                "citycode": "",
                "city": location_data['ad_info']['city'],
                "adcode": location_data['ad_info']['adcode'],
                "district": location_data['ad_info']['district'],
                "towncode": location_data['address_reference']['town']['id'],
                "township": location_data['address_reference']['town']['title'],
                "streetcode": "",
                "street": location_data['address_component']['street'],
                "inArea": 1,
                "areaJSON": json.dumps(dataJson, ensure_ascii=False)
            }
            print("Punch data prepared")
            return PunchData
    print("Geocode or reverse geocode failed")
    return None  # 添加返回 None 以处理失败


def Punch(headers, punchData, username, id, signId):
    print("Entering Punch function")
    headers['Referer'] = 'https://servicewechat.com/wxce6d08f781975d91/200/page-frame.html'
    url = 'https://gw.wozaixiaoyuan.com/sign/mobile/receive/doSignByArea'
    params = {
        'id': id,
        'schoolId': school_id,
        'signId': signId
    }
    res = requests.post(url, data=json.dumps(punchData), headers=headers, params=params)
    txt = json.loads(res.text)
    if txt['code'] == 0:
        print(f"{username}打卡成功！\n")
        MsgSend("打卡成功！", f"{username}归寝打卡成功！")
        return True
    else:
        print(f"{username}打卡失败！{str(txt)}\n")
        MsgSend("打卡失败！", f"{username}归寝打卡失败！{str(res.text)}")
        return False


# 蓝牙签到模块开始 By Mudea661
def upload_blue_data(blue1, blue2, headers, id, signid):
    print("Entering upload_blue_data function")
    print(f"Blue data: blue1={blue1}, blue2={blue2}, id={id}, signid={signid}")
    username = os.environ['wzxy_username']
    data = {
        "blue1": blue1,
        "blue2": list(blue2.values())
    }
    response = requests.post(
        url=f"https://gw.wozaixiaoyuan.com/dormSign/mobile/receive/doSignByDevice?id={id}&signId={signid}",
        headers=headers, data=json.dumps(data))
    print(f"Upload response status: {response.status_code}")
    if response.status_code == 200:
        response_data = response.json()
        print(f"Response data: {response_data}")
        if response_data.get("code") == 0:
            MsgSend("蓝牙打卡成功！", f"账号- {username} -蓝牙打卡成功！")
            print(f"账号- {username} -蓝牙打卡成功！")
            return 0
        else:
            print(f"账号- {username} -蓝牙打卡失败！ Code: {response_data.get('code')}")
            MsgSend("蓝牙打卡失败！", f"账号- {username} -蓝牙打卡失败！")
            return 1
    else:
        print("Upload failed with status code not 200")
        return 1


def doBluePunch(headers, username):
    print("Entering doBluePunch function for user: " + username)
    # 获取签到日志
    sign_logs_url = "https://gw.wozaixiaoyuan.com/dormSign/mobile/receive/getMySignLogs"
    sign_logs_params = {
        "page": 1,
        "size": 10
    }
    try:
        print("Attempting to get sign logs")
        response = requests.get(sign_logs_url, headers=headers, params=sign_logs_params)
        print(f"Sign logs response status: {response.status_code}")
        data_ids = response.json()
        print(f"Sign logs data: {json.dumps(data_ids, indent=2)}")
        location_id = data_ids["data"][0]["locationId"]
        sign_id = data_ids["data"][0]["signId"]
        major = data_ids["data"][0]["deviceList"][0]["major"]
        uuid = data_ids["data"][0]["deviceList"][0]["uuid"]
        print(f"Extracted: location_id={location_id}, sign_id={sign_id}, major={major}, uuid={uuid}")
        blue1 = [uuid.replace("-", "") + str(major)]
        blue2 = {"UUID1": uuid}
        print(f"Prepared blue data: blue1={blue1}, blue2={blue2}")
    except Exception as e:
        print(f"Error getting sign logs: {str(e)}")
        MsgSend("获取签到列表出错！", f"账号- {username} -获取签到列表出错！")
        return 0
    print("Calling upload_blue_data")
    return upload_blue_data(blue1, blue2, headers, location_id, sign_id)

# 蓝牙模块结束


def main():
    global school_id
    print("Entering main function")
    username = os.environ['wzxy_username']
    print(f"Username: {username}")
    school_id = get_school_id(os.environ['school_name'])
    print(f"School ID: {school_id}")
    login_headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; WLZ-AN00 Build/HUAWEIWLZ-AN00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/86.0.4240.99 XWEB/4343 MMWEBSDK/20220903 Mobile Safari/537.36 MMWEBID/4162 MicroMessenger/8.0.28.2240(0x28001C35) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64 miniProgram/wxce6d08f781975d91'}
    jws = Login(login_headers, username,
                             os.environ['wzxy_password'])
    print(f"JWS: {jws}")
    if jws:
        print("Login successful, setting headers")
        headers = {
            'Host': 'gw.wozaixiaoyuan.com',
            'Connection': 'keep-alive',
            'Accept': 'application/json, text/plain, */*',
            'jwsession': jws,
            "cookie": f'JWSESSION={jws}',
            "cookie": f'JWSESSION={jws}',
            "cookie": f'WZXYSESSION={jws}',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; WLZ-AN00 Build/HUAWEIWLZ-AN00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/86.0.4240.99 XWEB/4343 MMWEBSDK/20220903 Mobile Safari/537.36 MMWEBID/4162 MicroMessenger/8.0.28.2240(0x28001C35) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64 miniProgram/wxce6d08f781975d91',
            'Content-Type': 'application/json;charset=UTF-8',
            'X-Requested-With': 'com.tencent.mm',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://gw.wozaixiaoyuan.com/h5/mobile/health/0.3.7/health',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        print(f"dorm_sign: {os.environ['dorm_sign']}")
        if os.environ['dorm_sign'] == 'yes':
            print("Starting dorm_sign process")
            signId, id, dataJson = GetMySignLogs(headers)
            print(f"dorm_sign result: signId={signId}, id={id}")
            if signId:
                print("Preparing punch data")
                punchData = GetPunchData(username, os.environ['punch_location'], os.environ['tencentKey'], dataJson)
                if punchData:
                    print("Punching")
                    Punch(headers, punchData, username, id, signId)
        print(f"blue_sign: {os.environ['blue_sign']}")
        if os.environ['blue_sign'] == 'yes':
            print("Starting blue_sign process regardless of dorm_sign result")
            doBluePunch(headers, username)

    else:
        print(f"{username} 登陆失败！")
        MsgSend(f"{username} 登陆失败！", f"{username} 登陆失败！")


if __name__ == "__main__":
    main()
