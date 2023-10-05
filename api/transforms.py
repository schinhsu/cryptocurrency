import pandas

# 統一輸出欄位
columns = ['BlockNo','TxID','Date(UTC+8)','From','To','Value','TxFee','Token','Contract']

def transform_balance(balance,decimalLen=18):
    balance = str(balance)
    integer = '0' if len(balance) <= decimalLen else balance[:len(balance)-decimalLen]
    decimal = balance[len(integer):] if len(balance) > decimalLen else balance.zfill(decimalLen)

    balance = integer+'.'+decimal
    return eval(balance)