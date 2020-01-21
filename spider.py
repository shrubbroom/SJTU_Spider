import requests
import re
from bs4 import BeautifulSoup
import sqlio as sql


class spider:
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0'}
        self.db = sql.SqlIO('past.db')
        self.Seieexsb = {'target': 'http://bjwb.seiee.sjtu.edu.cn/bkjwb/index.htm',
                         'prefix': 'http://bjwb.seiee.sjtu.edu.cn',
                         'rurl': r'/bkjwb/info/[0-9]{5,}.htm'}
        self.Jwc = {'target': 'http://www.jwc.sjtu.edu.cn/web/sjtu/198001.htm',
                    'prefix': 'http://www.jwc.sjtu.edu.cn/web/sjtu/',
                    'rurl': r'[0-9]+-[0-9]+\.htm'}
        self.Zhiyuan = {'target' : 'https://zhiyuan.sjtu.edu.cn/category/%E6%95%99%E5%AD%A6%E9%80%9A%E7%9F%A5',
                        'prefix' : 'https://zhiyuan.sjtu.edu.cn',
                        'rurl' : r'/articles/[0-9]+'}
        self.Seieexsbdb = 'seieexsb'
        self.Electsysdb = 'electsys'
        if not self.db.SqlTableExists('seiee'):
            self.db.SqlMake('seiee', 'url', 40, [], 0)
        if not self.db.SqlTableExists('jwc'):
            self.db.SqlMake('jwc', 'url', 40, [], 0)

    def MPAPI(self, target):
        return self.MainParser(target['target'], target['rurl'], target['prefix'])

    def MainParser(self, target, rurl, prefix):
        response = requests.get(target, headers=self.headers)
        data = []
        heads = []
        for i in BeautifulSoup(response.content, 'lxml').find_all('a', href=re.compile(rurl)):
            heads.append(i.text)
        for i in re.findall(re.compile(rurl), response.text):
            data.append(prefix + i)
        filt = []
        result = []
        for i in list(zip(data, heads)):
            if i[0] not in filt:
                filt.append(i[0])
                result.append(i)
        return result

    def SeieeMainParser(self):
        response = requests.get(self.Seieexsb, headers=self.headers)
        rurl = r'/bkjwb/info/[0-9]{5,}.htm'
        data = []
        heads = []
        for i in BeautifulSoup(response.content, 'lxml').find_all('a', href=re.compile(rurl)):
            heads.append(i.text)
        for i in re.findall(re.compile(rurl), response.text):
            data.append('http://bjwb.seiee.sjtu.edu.cn' + i)
        filt = []
        result = []
        for i in list(zip(data, heads)):
            if i[0] not in filt:
                filt.append(i[0])
                result.append(i)
        return result

    def JwcMainParser(self):
        response = requests.get(self.Jwc, headers=self.headers)
        rurl = r'[0-9]+-[0-9]+\.htm'
        data = []
        heads = []
        for i in BeautifulSoup(response.content, 'lxml').find_all('a', href=re.compile(rurl)):
            heads.append(i.text)
        for i in re.findall(re.compile(rurl), response.text):
            data.append('http://www.jwc.sjtu.edu.cn/web/sjtu/' + i)
        filt = []
        result = []
        for i in list(zip(data, heads)):
            if i[0] not in filt:
                filt.append(i[0])
                result.append(i)
        print(result)
        return result

    def ZhiyuanMainParser(self):
        response = requests.get(self.Zhiyuan, headers=self.headers)
        rurl = r'/articles/[0-9]+'
        data = []
        heads = []
        for i in BeautifulSoup(response.content, 'lxml').find_all('a', href=re.compile(rurl)):
            heads.append(i.text)
        for i in re.findall(re.compile(rurl), response.text):
            data.append('https://zhiyuan.sjtu.edu.cn' + i)
        filt = []
        result = []
        for i in list(zip(data, heads)):
            if i[0] not in filt:
                filt.append(i[0])
                result.append(i)
        print(result)
        return result

    def SeieePageParser(self, url):
        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.content, 'lxml')
        return {'text': soup.find('div', class_="article_content").text,
                'html': soup.find('div', class_="article_content")}

    def JwcPageParser(self, url):
        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.content, 'lxml')
        try:
            return {'head': soup.find('td', class_='main_list_content_line').find(style="font-size:16px;").string,
                    'text': soup.find('table', class_='main_r_co_fo').text,
                    'html': soup.find('table', class_='main_r_co_fo')}
        except AttributeError:
            return {"html": ''}

    def ParserFilte(self, field, current):
        left_over = list(filter((lambda x: x not in set(self.db.SqlReader(field, 'url'))), current))
        for i in left_over:
            self.db.SqlInsert(field, {'url': i})
        self.db.SqlCommit()
        return left_over

    def MakePast(self):
        self.ParserFilte('seiee', self.SeieeMainParser())
        self.ParserFilte('jwc', self.JwcMainParser())

    def Refresh(self):
        print('this is a test text')
        seiee = self.ParserFilte('seiee', self.SeieeMainParser())
        jwc = self.ParserFilte('jwc', self.JwcMainParser())
        result = []
        for i in seiee:
            a = self.SeieePageParser(i)
            try:
                result.append(
                    {'source': 'seiee', 'url': i, 'head': 'Message From Seiee', 'text': a['text'], 'html': a['html']})
            except KeyError as e:
                print(e)
                continue
        for i in jwc:
            a = self.JwcPageParser(i)
            if not a['html'] == '':
                result.append({'source': 'jwc', 'url': i, 'head': a['head'], 'text': a['text'], 'html': a['html']})
        return result


if __name__ == '__main__':
    tmp = spider()
    print(tmp.MPAPI(tmp.Seieexsb))
    print(tmp.MPAPI(tmp.Zhiyuan))
    print(tmp.MPAPI(tmp.Jwc))
