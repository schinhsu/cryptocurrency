import datetime
import time
from requests_html import HTMLSession
import traceback
from pprint import pprint

# API連線管理，檢查回覆資料內容是否完整需重送
class ReqManagement:
    def __init__(self,includes=[],excludes=[],debugMode=False,sessionVerify=False):
        self.count = 0
        self.call_times = []
        self.base_rate = 20

        self.includes = includes
        self.excludes = excludes
        self.debugMode = debugMode
        
        self.session = HTMLSession(verify=sessionVerify)
        
    def update_call_rate(self):
        if len(self.call_times) <= 1:
            self.base_rate = max(self.base_rate-1,1)
        else:
            interval = (datetime.datetime.now()-self.call_times[0]).total_seconds()
            rate = (self.count-1)/interval
            #self.base_rate = rate
        self.count = 0
        self.call_times = []
        if self.debugMode:
            print(f'***Sleep 2 seconds to avoid exception...')
        time.sleep(2)
    
    def adjust_call_rate(self):
        if len(self.call_times) == 1:
            return
        interval = (self.call_times[-1]-self.call_times[0]).total_seconds()
        rate = self.count/interval
        if rate > self.base_rate:
            wait_time = max(int(rate-self.base_rate*interval),1)
            if self.debugMode:
                print(f'***Adjusting Call Rate for Sleep {wait_time} seconds...')
            time.sleep(wait_time)
    
    def send_requests(self,method,url,params={},headers={}):
        if method == 'post':
            res = self.session.post(url,params=params,headers=headers)
        elif method == 'get':
            res = self.session.get(url,params=params,headers=headers)
        self.count += 1
        self.call_times.append(datetime.datetime.now())
        self.adjust_call_rate()

        # 檢查res是否回傳json格式
        try:
            check = res.json()
        except:
            #錯誤判斷的關鍵字待改
            print('**Unknown Exception',traceback.format_exc())
            #Tronscan API回覆內容是text非json
            if res.text.find('suspended for ') >= 0:
                res_text = res.text
                pt = res_text.find('suspended for ')
                pt2 = res_text[pt+len('suspended for '):].find(' ')
                sus_seconds = res_text[pt++len('suspended for '):pt+len('suspended for ')+pt2]
                try:
                    sus_seconds = int(sus_seconds)
                except ValueError:
                    sus_seconds = 0
                if self.debugMode:
                    print('**Get Response Text: SUSPEND FOR ',sus_seconds,'SECONDS...')
                time.sleep(sus_seconds)
            elif res.text.find('currently unavailable') >= 0:
                if self.debugMode:
                    print('**Get Response Text: CURRENTLY UNAVAILBALE!!')
                self.update_call_rate()
            else:
                res_text = res.text
                if self.debugMode:
                    print('**Get Response Text Undefined:',res.url)
                    pprint(res_text)
                    print('------------------------------')
                self.update_call_rate()
                
            return self.send_requests(method,url,params,headers)
        
        # 檢查res.json()內的key值
        resNormal = True
        if isinstance(self.includes,list):
            for keyword in self.includes:
                if res.json().get(keyword) is None:
                    if self.debugMode:
                        print('**Get Response Json Without:',keyword)
                        pprint(res.json())
                        print('------------------------------')
                    resNormal = False
                    break
        elif isinstance(self.includes,dict):
            for key,value in self.includes.items():
                if res.json().get(key) is None or (not res.json().get(key) is None and res.json()[key] != value):
                    if self.debugMode:
                        print('**Get Response Without:',key,'=',value)
                        pprint(res.json())
                        print('------------------------------')
                    resNormal = False
                    break
        if isinstance(self.excludes,list):
            for keyword in self.excludes:
                if not res.json().get(keyword) is None:
                    if self.debugMode:
                        print('**Get Response Json With:',keyword)
                        pprint(res.json())
                        print('------------------------------')
                    resNormal = False
                    break
        elif isinstance(self.excludes,dict):
            for key,value in self.excludes.items():
                if not res.json().get(key) is None and res.json()[key] == value:
                    if self.debugMode:
                        print('**Get Response With:',key,'=',value)
                        pprint(res.json())
                        print('------------------------------')
                    resNormal = False
                    break
        if not resNormal:
            print('**Re-sending request:',url)
            pprint(params)
            self.update_call_rate()
            return self.send_requests(method,url,params,headers)
        
        return res