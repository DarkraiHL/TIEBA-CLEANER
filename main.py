#!/usr/bin/env python
# -*- coding:utf-8 -*-
import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from requests.utils import cookiejar_from_dict
import lxml
import json
import os
import time
from optparse import OptionParser

import sys

def log(text):
    print text
    '''
    s = '[%s] %s' % (str(datetime.now()), text)
    open('clean_tieba.log', 'a').write(s + '\n')
    p = (str(datetime.now()), text)
    print (text)
    '''

class Tieba:
    user_id = -1
    username = ''
    match = '.*'
    r = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
    }

    def error_check(self, text):
        log(text)
        try:
            _ = json.loads(text)
            if _['err_code'] == 0:
                log('Success')
                return True
            elif _['err_code'] == 220034:
                log('Failed: 您的操作太频繁了')
                return 'exit'
            elif _['err_code'] == 260005:
                log('Failed: Cookies失效')
                return False
            elif _['err_code'] == 230308:
                log('Failed: 据说tbs不对')
                return False
            else:
                log('Failed: 不造啥错误')
                return False

        except json.decoder.JSONDecodeError:
            return False

    def get_tie(self):
        tie_list = []
        page = 1
        while(1):
            url = 'https://tieba.baidu.com/i/%s/my_tie?&pn=%d' % (self.user_id, page)
            log('-->%s' % url)
            _ = self.r.get(url, headers=self.headers)
            my_tie = BeautifulSoup(_.text, 'lxml').select('.simple_block_container')[0].ul
            lis = my_tie.select('li')
            if len(lis) == 0:
                break
            for li in lis:
                a = li.select('a')
                bar_name = a[0].text
                bar_url = 'https://tieba.baidu.com' + a[0]['href']
                tie_name = a[1].text
                tie_url = 'https://tieba.baidu.com' + a[1]['href']
                new_tie = {
                    'bar_name': bar_name,
                    'bar_url': bar_url,
                    'tie_name': tie_name,
                    'tie_url': tie_url
                }
                log('add new tie: [%s][%s]' % (bar_name, tie_name))
                tie_list.append(new_tie)
            page += 1
        return tie_list
        # print(json.dumps(tie_list, ensure_ascii=False, indent=4))


    def del_tie(self, reply):
        print ('---------------------------')
        print reply
        print ('-----------------------------')
        log(json.dumps(reply, ensure_ascii=False, indent=4))
        log('-->%s' % reply['tie_url'])
        _ = self.r.get(reply['tie_url'], headers=self.headers)
        html = _.text
        check = re.findall('该贴已被删除', html)
        if len(check) > 0:
            tid = re.findall('p/(\d+)\?', reply['tie_url'])[0]
            url = 'https://tieba.baidu.com/errorpage/deledErrorInfo?tid=%s' % tid
            error = json.loads(self.r.get(url, headers=self.headers).text)
            type_no = int(error['data']['type'])
            if type_no == 0:
                log('很抱歉，该贴已被删除')
            elif type_no == 1:
                log('小广告太多啦。商品交易贴，度娘建议每天不能超过5条哦')
            elif type_no == 2:
                log('亲，由于您使用机器刷贴，影响了吧友在贴吧的浏览体验，导致贴子被删')
            elif type_no == 3:
                log('亲，由于您的贴子内含有敏感词汇/图片，影响了吧友在贴吧的浏览体验，导致贴子被删')
            elif type_no == 4:
                log('很抱歉，您的贴子已被系统删除')
            elif type_no == 5:
                log('很抱歉，您的贴子已被自己删除')
            elif type_no == 6:
                log('很抱歉，您的贴子已被吧务删除')
            else:
                log('Failed')
                return False
            log('Success')
            return True
        '''
        if '该吧被合并您所访问的贴子无法显示' in html:
            log('该吧被合并您所访问的贴子无法显示')
            log('Success')
            return True
        elif '您访问的贴子被隐藏' in html:
            log('抱歉，您访问的贴子被隐藏，暂时无法访问')
            log('Failed')
            return False
        else:
            pass
        '''
        print ('GAO')
        data = {
            'ie': re.findall('\"?charset\"?\s*:\s*[\'\"]?(.*?)[\'\"]', html)[0].lower(),
            # 'tbs': re.findall('"tbs"  : "([\d\w]+)"', html)[0],
            'tbs': re.findall('\"?tbs\"?\s*:\s*[\'\"]?([\w\d]+)[\'\"]', html)[0],
            'kw': re.findall('name="kw" value="(.*?)"', html)[0],
            'fid': re.findall("fid:'(\d+)'", html)[0],
            'tid': re.findall("tid:'(\d+)'", html)[0],
            'username': self.username,
            'delete_my_post': 1,
            'delete_my_thread' : 0,
            'is_vipdel': 0,
             'pid': re.findall('pid=(\d+)&', reply['tie_url'])[0],
            #'pid': re.findall('cid=(\d+)#', reply['tie_url'])[0],
            'is_finf': 'false'
        }
        print (data['tid'])
        #url ='http://tieba.baidu.com/bawu2/postaudit/audit'
        url = 'https://tieba.baidu.com/f/commit/post/delete'
        log('-->%s' % url)
        log('delete reply')
        _ = self.r.post(url, data=data, headers=self.headers)
        log(_.status_code)
        print('finish')
        print(_.text)
        return self.error_check(_.text)





    def login(self):
        print('这次不用输入前缀`Cookie:`了，直接复制后面的key-value对')
        #cookie = input('give me cookies[xxx=xxx; xxx=xxx]:')
        cookie = 'Cookie:TIEBA_USERTYPE=59831fa6c442e0855c0a494b; bdshare_firstime=1488517940445; rpln_guide=1; FP_UID=dbf4c3588fcb2b02868bbca30e7228bf; __cfduid=d500f62c36a3d56bd1d44461e5e7edabe1496248275; Hm_lvt_287705c8d9e2073d13275b18dbd746dc=1497751470,1497751978,1497753745,1498046460; BAIDUID=643B5AD4CF6A1333547E2C281C81071D:FG=1; BIDUPSID=6AA41DDBFF447915026E1644ADE3DCA7; PSTM=1498548242; MCITY=-%3A; fixed_bar=1; BDRCVFR[mkUqnUt8juD]=mk3SLVN4HKm; BDORZ=FFFB88E999055A3F8A630C64834BD6D0; PSINO=5; H_PS_PSSID=1445_21095; baidu_broswer_setup_%E9%81%A5%E8%BF%9C%E7%9A%84Blade=0; BDUSS=Q1bnFYaFFhdktBTU8xbHlRalR6fjg2M3B1a1d5NHNOYzV-Y3pFdlY3U29WZDVaSVFBQUFBJCQAAAAAAAAAAAEAAABd~zoGwMfAx6Hu0KG~4QAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAKjItlmoyLZZZ3; STOKEN=03de648ac7ebb1c2b7d5664d173561451aa43357eafb633ecd43789ceaac4fde; TIEBAUID=f986682cac14bc52fd7f2efb; FP_LASTTIME=1505151153863'
        q = {k:v for k,v in re.findall(r'([^=]*)=([^;]*);{0,1}\s{0,1}', cookie)}
        self.r.cookies = cookiejar_from_dict(q)
        url = 'https://tieba.baidu.com'
        log('-->%s' % url)
        _ = self.r.get(url)
        self.username = re.findall('"user_name": "(.*?)",', _.text)[0]
        log('get username: %s' % (self.username))
        url = 'https://tieba.baidu.com/home/profile?un=%s' % self.username
        log('-->%s' % url)
        _ = self.r.get(url)
        self.user_id = re.findall('user_id":(\d+)', _.text)[0]

        

    def start(self, input_file=True):
        
        tie_list = self.get_tie()
        print ('start over')
        tie_count = len(tie_list)
        tie_fail = []
        if tie_count == 0 :
            log('done')
            exit()

        tie_is_max = False
        k=u"沙耶之歌吧"
        for i in tie_list :
            status = self.del_tie(i)
            time.sleep(5)
        ''':
            log('tie: %d/%d' % (i + 1, tie_count))
            if tie_is_max:
                tie_fail.append(tie_list[i])
                continue
            if(tie_list[i]['bar_name']!='沙耶之歌'):
                continue
            status = self.del_tie(tie_list[i])
            time.sleep(2)
            if status == 'exit':
                print('达到每日上限，等待下一轮')
                tie_is_max = True
                tie_fail.append(tie_list[i])
            elif status == False:
                tie_fail.append(tie_list[i])
            else:
                pass
        '''
            
       # open('clean_tieba_tie_fail.json', 'w').write(json.dumps(tie_fail, ensure_ascii=False, indent=4))




if __name__ == '__main__':
    
    #reload(sys)
    #sys.setdefaultencoding('utf-8')
    print ('shift')
    tieba = Tieba()
    parser = OptionParser()
    parser.add_option('-m', '--match',
                      help="give me re format, if match in reply, I will delete")
    (options, args) = parser.parse_args()
    if options.match is not None:
        tieba.match = match
        log('match had set: (%s)' % tieba.match)
    else:
        log('match had set: (%s)' % tieba.match)

    tieba.login()
    print ('------------------------------- login clear ------------------------')
    
    tieba.start()


    while(1):
        sleep_hours = 4
        log('will sleep %d hours' % (sleep_hours))
        for i in range(0, sleep_hours, 1):
            log('start after %d hours' % (sleep_hours - i))
            time.sleep(60)
        tieba.start(False)
