from selenium import webdriver
import requests
import random

salt = random.randint(1000, 9999)
client_id = ""  # 此处输入你 AAD 的客户端ID
req_link = ""  # 此处输入你已经在AAD应用注册的重定向链接

oauth_link = f"https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize?client_id={client_id}&response_type=token&redirect_uri={req_link}&scope=XboxLive.signin+offline_access&state={salt}&response_mode=fragment"


driver = webdriver.Firefox()  # 使用Firefox作为调试终端，你也可以使用其他浏览器，配置略有不同
driver.get(oauth_link)
while(True):
    if(driver.current_url.startswith(req_link)):
        break  # 循环检测地址栏，检测到重定向后开始处理
if(driver.current_url.startswith(req_link+"#error=")):
    print("调用Microsoft OAuth服务异常:\n")
    error_info = driver.current_url.split("&")[0].replace(
        f"{req_link}#error=", "")
    print(f"错误信息:{error_info}")
    exit()

access_token = driver.current_url.split("&")[0].replace(
    f"{req_link}#access_token=", "")
print("已取得OAuth令牌")
driver.quit()  # 自动销毁调试终端

xbl_link = "https://user.auth.xboxlive.com/user/authenticate"
json_headers = {"Content-Type": "application/json",
                "Accept": "application/json"}

xbl_body = {
    "Properties": {
        "AuthMethod": "RPS",
        "SiteName": "user.auth.xboxlive.com",
        "RpsTicket": f"d={access_token}"
    },
    "RelyingParty": "http://auth.xboxlive.com",
    "TokenType": "JWT"
}  # 获取XBL令牌步骤


xbl_req = requests.post(xbl_link, json=xbl_body, headers=json_headers)
xbl_dict = eval(xbl_req.text)
print("已取得XBL令牌")

xsts_link = "https://xsts.auth.xboxlive.com/xsts/authorize"

xsts_body = {
    "Properties": {
        "SandboxId": "RETAIL",
        "UserTokens": [
            f"{xbl_dict['Token']}"
        ]
    },
    "RelyingParty": "rp://api.minecraftservices.com/",
    "TokenType": "JWT"
}  # 获取XSTS令牌步骤

xsts_req = requests.post(xsts_link, json=xsts_body, headers=json_headers)
xsts_dict = eval(xsts_req.text)
if(xsts_req.status_code == 401):
    print(f"警告:XSTS授权失败\n错误代码: {xsts_dict['XErr']}")
    print(f"{xsts_dict['Message']}\n获取更多帮助: {xsts_dict['Redirect']}")
    quit()

print("已取得XSTS令牌")
userhash = xsts_dict["DisplayClaims"]["xui"][0]["uhs"]

mc_body = {

    "identityToken": f"XBL3.0 x={userhash};{xsts_dict['Token']}"
}

mc_link = "https://api.minecraftservices.com/authentication/login_with_xbox"

mc_req = requests.post(mc_link, json=mc_body,
                       headers=json_headers)  # 获得Minecraft服务器授权

mc_dict = eval(mc_req.text)
print("已通过Minecraft服务认证")

json_headers["Authorization"] = f"Bearer {mc_dict['access_token']}"
mc_api_link = "https://api.minecraftservices.com/minecraft/profile"  # 取得Minecraft个人账户个人信息

mc_api = requests.get(mc_api_link, headers=json_headers)
user_dict = eval(mc_api.text)

print("访问Minecraft用户资料中...")
try:
    print(f"您的用户名是: {user_dict['name']}\nUUID是: {user_dict['id']}")
except:
    print("该玩家未持有Minecraft资产!")