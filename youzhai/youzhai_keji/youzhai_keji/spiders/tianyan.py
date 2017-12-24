# -*- coding: utf-8 -*-
import scrapy
import re, requests, json
from copy import deepcopy


class TianyanSpider(scrapy.Spider):
    name = 'tianyan'
    allowed_domains = ['www.tianyancha.com']
    start_urls = ['https://www.tianyancha.com/']

    def __init__(self):
        company = '******有限公司'      # 这里可加入列表，通过遍历列表方式可查询多个目标公司
        self.company = company

    def start_requests(self):       # 重新登录
        cookies = 'aliyungf_tc=AQAAAK30BRsp1A4AhLFYtMUCRy9/wazu; csrfToken=G76AtDSCduG4KsxI6dwQCY3B; TYCID=b8dc1dc0cd3a11e7a4b49534d12a873e; undefined=b8dc1dc0cd3a11e7a4b49534d12a873e; ssuid=6343178670; tyc-user-info=%257B%2522token%2522%253A%2522eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxNzc0NjU2ODU2NSIsImlhdCI6MTUxMTEwMzgxOSwiZXhwIjoxNTI2NjU1ODE5fQ.NgzcRGCmGxppYMxy5fI-XfI6aYOpBF0En1Ws7bVtRUNUPwpsopKBhChZjOp_0pQn069YMnmYqPns3sNB_v0xnw%2522%252C%2522integrity%2522%253A%25220%2525%2522%252C%2522state%2522%253A%25220%2522%252C%2522vnum%2522%253A%25220%2522%252C%2522onum%2522%253A%25220%2522%252C%2522mobile%2522%253A%252217746568565%2522%257D; auth_token=eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxNzc0NjU2ODU2NSIsImlhdCI6MTUxMTEwMzgxOSwiZXhwIjoxNTI2NjU1ODE5fQ.NgzcRGCmGxppYMxy5fI-XfI6aYOpBF0En1Ws7bVtRUNUPwpsopKBhChZjOp_0pQn069YMnmYqPns3sNB_v0xnw; _csrf=VJqibSUNLoQ/Q1xmygPDRA==; OA=csasZ61xHOCljaU6ZXsGWSfLJvcixh/bknL5cyUK/Ds=; _csrf_bk=59b4e57ef8522aa2429dc1c7847dd04c; Hm_lvt_e92c8d65d92d534b0fc290df538b4758=1511104117; Hm_lpvt_e92c8d65d92d534b0fc290df538b4758=1511104163'
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse,
                cookies={i.split("=")[0]: i.split("=")[-1] for i in cookies.split("; ")}
            )

    def parse(self, response):
        print(re.findall('177****8565', response.body.decode()))    # 检查是否登录
        f_url = 'https://www.tianyancha.com/search?key={}&checkFrom=searchBox'.format(requests.utils.quote(self.company))
        yield scrapy.Request(
            f_url,
            callback=self.parse_f
        )

    def parse_f(self, response):
        div_list = response.xpath("//div[@class='b-c-white search_result_container']/div")
        for div in div_list:
            item = dict()
            item["company_href"] = div.xpath(".//div[@class='search_right_item']/div[1]/a/@href").extract_first()    # 列表页公司链接
            item["company_time"] = div.xpath(".//div[@class='search_right_item']/div[2]/div[1]/div[3]/span/text()").extract_first()  # 注册时间
            item["company_location"] = div.xpath(".//div[@class='search_right_item']//div[4]/span[1]/text()").extract_first()  # 列表页公司所在地
            item["company_goal"] = div.xpath(".//div[@class='search_right_item']//div[4]/span[2]/text()").extract_first()  # 列表页评价分数
            item["company_names"] = div.xpath(".//div[@class='search_right_item']/div[2]/div[2]/div/span[3]/text()").extract()  # 列表页公司曾用名
            item["company_number"] = re.search(r'\d+', item["company_href"]).group()    # 获取关键的与公司一一对应的数字
            # print(item["company_number"])
            yield scrapy.Request(
                item["company_href"],
                callback=self.parse_m,
                meta={"item": deepcopy(item)}
            )

    def parse_m(self, response):
        item = response.meta["item"]
        item["company_phone"] = response.xpath("//div[@class='f14 sec-c2 mt10']/div[1]/span[2]/text()").extract_first()  # 公司电话
        item["company_link"] = response.xpath("//div[@class='f14 sec-c2 mt10']/div[2]/span[2]/text()").extract_first() # 公司网址
        item["company_in"] = response.xpath("//script[@id='company_base_info_detail']/text()").extract()  # 公司简介
        item["company_in"] = [i.replace('\n', '').strip() for i in item["company_in"]]
        js_url = 'https://www.tianyancha.com/equity/equitydetail.json?id={}'.format(int(item["company_number"]))    # 获取公司股东部分信息
        yield scrapy.Request(
            js_url,
            callback=self.parse_e,
            meta={"item": deepcopy(response.meta["item"])}
        )

    def parse_e(self, response):
        item = response.meta["item"]
        js_str = json.loads(response.text)
        item["company_name"] = js_str['data']['baseInfo']['name']   # 公司名称
        item['company_ld_name'] = js_str['data']['baseInfo']['legal_person_name']   # 公司法人
        item["company_status"] = js_str['data']['baseInfo']['regStatus']    # 公司状态
        item['company_money'] = js_str['data']['baseInfo']['reg_capital']   # 注册资金
        item["company_part"] = {i['name']: i['percent'] for i in js_str['data']['holderList']}  # 股东股权部分
        item["company_pte"] = {i['name']: i['typeJoin'][0] for i in js_str['data']['staffList']}  # 管理层部分
        try:
            item["company_exe"] = [i['name'] for i in js_str['data']['inverstList']]    # 对外投资部分
        except Exception as e:
            item["company_exe"] = None
        risk_url = 'https://www.tianyancha.com/risk/riskInfo.html?id={}'.format(int(item["company_number"]))    # 获取天眼风险请求地址
        # print(item)
        yield scrapy.Request(
            risk_url,
            callback=self.parse_r,
            meta={"item": deepcopy(response.meta["item"])}
        )

    def parse_r(self, response):
        item = response.meta["item"]
        item["itself_risk"] = response.xpath("//div[@id='riskPopupInternal']//span/em/text()").extract()    # 自身风险
        item["outself_risk"] = response.xpath("//div[@id='riskPopupExternal']//span/em/text()").extract()    # 周边风险
        item["risk_num_d"] = response.xpath("//div/@onclick").extract()
        temp = re.findall(r'\d{5,20}', str(item["risk_num_d"]))
        item["risk_num_d"] = temp
        print(item, '__' * 30)
        if len(temp) > 0:
            item["risk_num_d"] = temp

            for i in temp:      # 遍历risk_num_d发起请求获取风险的详情信息，这里因vip限制原因只针对一家公司发起请求获取详情信息
                risk_detail_url = 'https://www.tianyancha.com/risk/riskDetail.html?id={}'.format(i)
                yield scrapy.Request(
                    risk_detail_url,
                    callback=self.parse_r_d,
                    meta={"item": deepcopy(response.meta["item"])}
                )

    def parse_r_d(self, response):
        item = response.meta["item"]
        item["risk_date"] = response.xpath("//td[1]/span/text()").extract_first()
        item["risk_name"] = response.xpath("//td[2]/a/text()").extract_first()
        item["risk_type"] = response.xpath("//td[3]/span/text()").extract_first()
        item["risk_num"] = response.xpath("//td[4]/span/text()").extract_first()
        yield item

