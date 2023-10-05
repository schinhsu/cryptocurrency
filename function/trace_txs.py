from .trace_tx import trace_tx_tron
from .lookup_details import lookup_details_tron
from .transforms import columns

import os
import pandas


def trace_txs_tron(tronObj,txs,layerNum=3,traceType='From',ignoreAmount=1,traceLimit=10000,storeEachLayer=False,storePath='tmp//',debugMode=False):
    if 'Layer' in txs.columns and 'TxNo' in txs.columns:
        traceResults = txs[columns+['Layer','TxNo']].copy()
        layerCount = int(txs['Layer'].max())
    else:
        traceResults = txs[columns].copy()
        traceResults['Layer'] = 0
        traceResults['TxNo'] = [f'{i+1}' for i in range(len(traceResults))]
        layerCount = 0

    if storeEachLayer and not os.path.exists(storePath):
        os.makedirs(storePath)
        
    while layerCount < layerNum:
        print(f'Tracing Layer {layerCount}...')
        toTrace = traceResults[traceResults['Layer'] == layerCount]
        toTrace = toTrace.reset_index(drop=True)
    
        layerCount += 1
        # 追查internal交易會導致同一筆txid可能會有兩筆以上不同的交易內容
        # 追查相同錢包也會導致同一筆txid有兩筆以上相同的交易內容
        for i,(txid,grouped) in enumerate(toTrace.groupby(by=['TxID'])):
            grouped = grouped.drop_duplicates(subset=['From','To','Contract','Value'])
            row = grouped.iloc[-1] #追查最後一筆
            addrInfo = tronObj.get_account_info(row[traceType])
            addrType = ''
            if addrInfo['accountType'] == 0:
                addrType = 'Account'
            elif addrInfo['accountType'] == 2:
                addrType = 'Contract'
            if addrInfo.get('addressTag') is None:
                addrInfo['addressTag'] = ''
            # 交易所
            if addrType == 'Account' and len(addrInfo['addressTag']) > 0:
                print('***交易所***',addrType,row[traceType])
                continue
            if addrType == 'Contract':
                print('***智能合約***',addrType,row[traceType])
                lookups = lookup_details_tron(tronObj,row)
                lookups.loc[lookups['Token']=='TRX','Contract'] = 'trc10'
                if traceType == 'From':
                    lookup_trace = lookups.iloc[0]
                else:
                    lookup_trace = lookups.iloc[-1]
                if debugMode:
                    print(lookup_trace)
                traceResults = pandas.concat([traceResults,lookups])
                res = trace_tx_tron(tronObj,lookup_trace,traceType=traceType,
                                             traceLimit=traceLimit,traceTolerance=ignoreAmount,debugMode=debugMode)
            else:
                res = trace_tx_tron(tronObj,row,traceType=traceType,
                                             traceLimit=traceLimit,traceTolerance=ignoreAmount,debugMode=debugMode)
            print(f">第{layerCount}層-第{i+1}筆:{row[traceType]};追蹤結果:{len(res[res['Value']>=ignoreAmount])}/{len(res)}筆")
            if len(res) == 0:
                continue
    
            res = res[res['Value'] >= ignoreAmount]
            res.loc[:,['Layer']] = [layerCount for _ in range(len(res))]
            ## 因為internal交易所以相同的txid可能會有多筆，就必須用去除重複的交易序號來編號
            txids = res['TxID'].drop_duplicates().tolist()
            res.loc[:,['TxNo']] = res['TxID'].apply(lambda txid: f"{row['TxNo']}_{txids.index(txid)+1}")
            #print(res)
            traceResults = pandas.concat([traceResults,res])

        if storeEachLayer:
            traced = traceResults[traceResults['Layer'] == layerCount]
            traced.to_excel(f'{storePath}layer{layerCount}.xlsx',index=False)
        
    return traceResults