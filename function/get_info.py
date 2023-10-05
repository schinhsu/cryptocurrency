from requests_html import HTMLSession
from lxml import html
import time


class WebCrawler:
    def __init__(self,sessionVerify=False):
        self.session = HTMLSession(verify=sessionVerify)

    def get_eth_addr_info(self,addr):
        res = self.session.get(f'https://etherscan.io/address/{addr}')
        if res.url == 'https://etherscan.io/busy':
            print('**Fetching Address Info from Web Busy(sleep 5 seconds)**')
            time.sleep(5)
            return self.get_eth_addr_info(addr)

        tree = html.fromstring(res.content)

        labels = tree.xpath('//section[@id="ContentPlaceHolder1_divSummary"]/div/div/a[@data-bs-toggle="tooltip"]/div/span/text()')+tree.xpath('//div[@id="ContentPlaceHolder1_divLabels"]/span/div/span/text()')
        labels = [label.strip() for label in labels]
        addrLabel = ''
        if len(labels) > 0:
            addrLabel = labels[0]
        otherLabel = ''
        if len(labels) > 1:
            otherLabel = ' '.join(labels[1:])

        addrInfo = tree.xpath('//h1[@class="h5 mb-0"]/text()')
        for addrType in addrInfo:
            addrType = addrType.strip()
            if len(addrType) > 0:
                break
        #Etherscan的類別是['Address','Contract'];Tronscan的類別是['Account','Contract']
        addrType = 'Account' if addrType == 'Address' else addrType
        return {'type':addrType,'label':addrLabel,'other_labels':otherLabel}


    def get_eth_contract_info(self,addr):
        res = self.session.get(f'https://etherscan.io/token/{addr}')
        if res.url == 'https://etherscan.io/busy':
            print('**Fetching Address Info from Web Busy(sleep 5 seconds)**')
            time.sleep(5)
            return self.get_eth_contract_info(addr)
        #print(res.url)
        tree = html.fromstring(res.content)
        try:
            tokenName = tree.xpath('//head/title/text()')[0]
            pt1 = tokenName.find('(')
            pt2 = tokenName.find(')')
            token = tokenName[pt1+1:pt2]
        except IndexError:
            token = ''
        try:
            protocols = tree.xpath('//section[@id="ContentPlaceHolder1_divSummary"]/div/div/span/text()')[0]
            tokenType = protocols.strip().replace('-','')
        except IndexError:
            tokenType = ''
        return token,tokenType