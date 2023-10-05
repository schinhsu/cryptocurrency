from .transforms import columns

from .get_transfer import get_transfer_tron_desc,get_transfer_tron_asc
from .lookup_details import lookup_details_tron

import datetime
import pandas

def trace_tx_tron(tronObj,txinfo,traceType='From',traceLimit=1000,traceTolerance=0.01,debugMode=False):
    targetUTCTime = txinfo['Date(UTC+8)']-datetime.timedelta(hours=8)
    #依token類型自動判斷使用哪個transType
    if txinfo['Token'] == 'TRX':
        transType = 'TRC10'
    elif txinfo['Token'] == 'USDT':
        transType = 'TRC20'
    else:
        token_info = tronObj.get_contract_info(txinfo['Contract'])
        transType = token_info['data'][0]['tokenInfo']['tokenType'].upper()

    # 下載追蹤錢包資訊
    if traceType == 'From':
        tmp = get_transfer_tron_desc(tronObj,txinfo[traceType],transType=transType,
                                          limit=traceLimit,end=targetUTCTime,debugMode=debugMode)
        if debugMode:
            print(f'***已下載{len(tmp)}筆{transType}交易紀錄')
        tmp2 = get_transfer_tron_desc(tronObj,txinfo[traceType],transType='Internal',
                                          limit=traceLimit,end=targetUTCTime,debugMode=debugMode)
        if debugMode:
            print(f'***已下載{len(tmp2)}筆Internal交易紀錄')
        tmp.loc[:,['tx_type']]=[transType for _ in range(len(tmp))]
        tmp2.loc[:,['tx_type']]=['Internal' for _ in range(len(tmp2))]
    else:
        tmp = get_transfer_tron_asc(tronObj,txinfo[traceType],transType=transType,
                                          limit=traceLimit,start=targetUTCTime,debugMode=debugMode)
        if debugMode:
            print(f'***已下載{len(tmp)}筆{transType}交易紀錄')
        tmp2 = get_transfer_tron_asc(tronObj,txinfo[traceType],transType='Internal',
                                          limit=traceLimit,start=targetUTCTime,debugMode=debugMode)
        if debugMode:
            print(f'***已下載{len(tmp2)}筆Internal交易紀錄')
        tmp.loc[:,['tx_type']]=[transType for _ in range(len(tmp))]
        tmp2.loc[:,['tx_type']]=['Internal' for _ in range(len(tmp2))]
    check = pandas.concat([tmp,tmp2])
    check = check.sort_values(by=['Date(UTC+8)'],ascending=(traceType=='To'))

    start = False
    amount = 0
    result = pandas.DataFrame(columns=columns)

    for _,row in check.iterrows():
        # 過濾幣別、合約
        if row['Token'] != txinfo['Token']:
            continue
        #internal交易的合約位址會寫觸發的智能合約(和一般trc10交易不同)
        if row['tx_type'] != 'Internal' and row['Contract'] != txinfo['Contract']:
            continue
        if start:
            if row[traceType] != txinfo[traceType]:
                amount += row['Value']
                #加入手續費
                if traceType == 'To' and transType == 'TRC10':
                    amount += row['TxFee']
                #result.loc[len(result)] = row.tolist()[:len(columns)]
                result = pandas.concat([result,pandas.DataFrame([row.values],columns=row.index)])
                if row['tx_type'] == 'Internal':
                    tx_details = lookup_details_tron(tronObj,row)
                    if traceType == 'From':
                        #只追Log第一筆
                        result = pandas.concat([result,tx_details.iloc[:1]])
                    else:
                        #只追log最後一筆
                        result = pandas.concat([result,tx_details.iloc[-1:]])
                if amount >= txinfo['Value']:
                    break
                if txinfo['Value'] - amount < traceTolerance:
                    break
        if row['TxID'] == txinfo['TxID']:
            start = True
    if debugMode and not start:
        print(f'***下載資料不含原TXID交易!!!')
    return result