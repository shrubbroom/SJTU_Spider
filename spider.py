# -*- coding: UTF-8 -*-
import requests
import re
from bs4 import BeautifulSoup
import sqlio as sql
from textrank4zh import TextRank4Keyword, TextRank4Sentence


class spider:
    """ This class is the spider which collects news from: Undergraduate Education Information Net, SEIEE,
    Zhiyuan College and SMSE. It consists of local data storage with SqLite and page parsering via BeautifulSoup and
    Textrank4zh. the methods 'Refresh' is the out-put."""
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0'}
        self.db = sql.SqlIO('past.db')
        self.seiee = {'target': 'http://bjwb.seiee.sjtu.edu.cn/bkjwb/index.htm',
                      'prefix': 'http://bjwb.seiee.sjtu.edu.cn',
                      'rurl': r'/bkjwb/info/[0-9]{5,}.htm'}
        self.jwc = {'target': 'http://www.jwc.sjtu.edu.cn/web/sjtu/198001.htm',
                    'prefix': 'http://www.jwc.sjtu.edu.cn/web/sjtu/',
                    'rurl': r'[0-9]+-[0-9]+\.htm'}
        self.zhiyuan = {'target': 'https://zhiyuan.sjtu.edu.cn/category/%E6%95%99%E5%AD%A6%E9%80%9A%E7%9F%A5',
                        'prefix': 'https://zhiyuan.sjtu.edu.cn',
                        'rurl': r'/articles/[0-9]+'}
        self.SMSE = {'target': 'http://smse.sjtu.edu.cn/ggao-list.asp',
                     'prefix': 'http://smse.sjtu.edu.cn/',
                     'rurl': r'ggao-content.asp\?id\=[0-9]+'}
        self.table_name = 'pasts'
        if not self.db.SqlTableExists(self.table_name):
            self.db.SqlMake(self.table_name, 'url', 40, ['tag', 'date', 'text'], 10000)

    def __enter__(self):
        print('spider: entering refreshing process...')
        return self.Refresh()

    def __exit__(self, type, value, traceback):
        if type is not None:
            print('spider: you must deal with this error')
            print("ERRORtype:", type)
            print("ERRORvalue:", value)
            print("ERRORtrace:", traceback)
            return False
        else:
            print('spider: refresh complete!')
            return True

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

    def Refresh(self):
        news = []
        old_news = self.MPAPI(self.jwc)
        for i in old_news:
            if not (self.db.SqlPrimaryExists(self.table_name, 'url', i[0])):
                result = page_parser('jwc', i[0], i[1])
                self.db.SqlInsert(self.table_name, {'url': result.url,
                                                    'date': result.date,
                                                    'text': result.text})
                news.append(result)
        old_news = self.MPAPI(self.seiee)
        for i in old_news:
            if not (self.db.SqlPrimaryExists(self.table_name, 'url', i[0])):
                result = page_parser('seiee', i[0], i[1])
                self.db.SqlInsert(self.table_name, {'url': result.url,
                                                    'date': result.date,
                                                    'text': result.text})
                news.append(result)
        old_news = self.MPAPI(self.zhiyuan)
        for i in old_news:
            if not (self.db.SqlPrimaryExists(self.table_name, 'url', i[0])):
                result = page_parser('zhiyuan', i[0], i[1])
                self.db.SqlInsert(self.table_name, {'url': result.url,
                                                    'date': result.date,
                                                    'text': result.text})
                news.append(result)
        old_news = self.MPAPI(self.SMSE)
        for i in old_news:
            if not (self.db.SqlPrimaryExists(self.table_name, 'url', i[0])):
                result = page_parser('SMSE', i[0], i[1])
                self.db.SqlInsert(self.table_name, {'url': result.url,
                                                    'date': result.date,
                                                    'text': result.text})
                news.append(result)
        return news


class page_parser:
    def __init__(self, tag, url, head=''):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0'}
        self.tag = tag
        self.url = url
        self.head = head
        try:
            if tag is 'seiee':
                pars = self.SeieePP()
                self.date = pars['date']
                self.abstracts = pars['abstracts']
                self.keywords = pars['keywords']
                self.text = pars['text']
            if tag is 'jwc':
                pars = self.JwcPP()
                self.date = pars['date']
                self.abstracts = pars['abstracts']
                self.keywords = pars['keywords']
                self.text = pars['text']
            if tag is 'zhiyuan':
                pars = self.ZhiyuanPP()
                self.date = pars['date']
                self.abstracts = pars['abstracts']
                self.keywords = pars['keywords']
                self.text = pars['text']
            if tag is 'SMSE':
                pars = self.SMSEPP()
                self.date = pars['date']
                self.abstracts = pars['abstracts']
                self.keywords = pars['keywords']
                self.text = pars['text']
        except AttributeError as e:
            print('spider: trivial error \'' + str(e) + '\'')
            self.date = 'null'
            self.abstracts = 'null'
            self.keywords = 'null'
            self.text = 'null'
        if tag not in {'seiee', 'jwc', 'zhiyuan', 'SMSE'}:
            raise AttributeError('No such tag :' + tag)

    def KeyExtractor(self, text):
        tr4w = TextRank4Keyword()
        tr4w.analyze(text=text, lower=True, window=2)
        KeyWords = []
        for phrase in tr4w.get_keyphrases(keywords_num=20, min_occur_num=2):
            KeyWords.append(str(phrase))
        tr4s = TextRank4Sentence()
        tr4s.analyze(text=text, lower=True, source='all_filters')
        Abstract = []
        for item in tr4s.get_key_sentences(num=3):
            Abstract.append(str(item.sentence))
        return {'keywords': KeyWords,
                'abstracts': Abstract}

    def SeieePP(self):
        response = requests.get(self.url, self.headers)
        soup = BeautifulSoup(response.content, 'lxml')
        date = str(soup.find('div', align='right').text).replace('[', '').replace(']', '')
        text = re.sub(r'\$\(function[\s\S]*', '',
                      re.sub(r'[\n\r]+', '\n', str(soup.find('div', class_='article_content').text.strip())))
        keys = self.KeyExtractor(text)
        return {'date': date,
                'keywords': keys['keywords'],
                'abstracts': keys['abstracts'],
                'text': text}

    def JwcPP(self):
        response = requests.get(self.url, self.headers)
        soup = BeautifulSoup(response.content, 'lxml')
        date = str(re.match(re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}'),
                            soup.find('td', class_='main_r_list_left_m').text).group())
        text = re.sub(r'\s+', ' ', soup.find('td', class_='font_cont1').text.strip())
        keys = self.KeyExtractor(text)
        return {'date': date,
                'keywords': keys['keywords'],
                'abstracts': keys['abstracts'],
                'text': text}

    def ZhiyuanPP(self):
        response = requests.get(self.url, self.headers)
        soup = BeautifulSoup(response.content, 'lxml')
        with requests.get('https://zhiyuan.sjtu.edu.cn/category/%E6%95%99%E5%AD%A6%E9%80%9A%E7%9F%A5',
                          self.headers) as main_pg:
            tail = str(re.search(re.compile(r'/articles/[0-9]+'), self.url).group())
            date = BeautifulSoup(main_pg.content, 'lxml').find('a', href=tail).parent.find('span',
                                                                                           class_='pull-right').text
        text = re.sub(r'[\n\r]+', '\n', re.sub(r's+', ' ', soup.find('div', class_='page').text.strip()))
        keys = self.KeyExtractor(text)
        return {'date': date,
                'keywords': keys['keywords'],
                'abstracts': keys['abstracts'],
                'text': text}

    def SMSEPP(self):
        with requests.get(self.url, self.headers) as response:
            soup = BeautifulSoup(response.content, 'lxml')
        date = soup.find('span', class_='faburiqi').text.replace('/', '-')
        text = re.sub(r's+', ' ', re.sub(r'[\n\r]+', '\n', soup.find('div', class_='new-neirong-height').text.strip()))
        keys = self.KeyExtractor(text)
        return {'date': date,
                'keywords': keys['keywords'],
                'abstracts': keys['abstracts'],
                'text': text}

    def __str__(self):
        return ','.join([str(self.url), str(self.tag),str(self.head), str(self.date), str(self.keywords), str(self.abstracts)])