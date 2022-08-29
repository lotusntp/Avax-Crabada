from __future__ import print_function
from web3 import Web3
import json
import time
from multiprocessing import Process
from datetime import datetime
from pycoingecko import CoinGeckoAPI
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
import requests
import os
from rich.console import Console
from rich.table import Column, Table
from tkinter import *
from line import LINE
import threading


# API CoinGecko
cg = CoinGeckoAPI()
# Console
console = Console()
table = Table(show_header=True, header_style="bold magenta")
table.add_column("Date", style="dim", width=23)
table.add_column("Game Info", width=24)
table.add_column("Gas", justify="right")
table.add_column("Status", justify="right")
table.add_column("Nexttime", justify="right")

# GUI
# GUI = Tk()
# GUI.mainloop()

# Config API Google Sheel
SERVICE_ACCOUNT_FILE = 'keys.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SAMPLE_SPREADSHEET_ID = '' # Sheet ID
credentials = None
credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
creds = None
data_path = '/'
try:
    with open(os.path.join(data_path, "sheets_discovery.json")) as jd:
        service = build.build_from_document(json.load(jd), htcredentialstp=credentials)
except:
    DISCOVERY_SERVICE_URL = 'https://sheets.googleapis.com/$discovery/rest?version=v4'
    service = build('sheets', 'v4', credentials=credentials, discoveryServiceUrl=DISCOVERY_SERVICE_URL)          
sheet = service.spreadsheets()
# End Config API Google Sheel


# Load Json
f = open('setting.json')
a = open('abi.json')
data = json.load(f)
# End load json
ABI_LOAD = json.load(a)
ABI = ABI_LOAD["abi"]
# Setting
ACCOUNT = data['account']
PRIVATE_KEY = data['privateKey']
CONTRACT = data['contract']
TOKEN_LINE = data['tokenLine']
PROVIDER  = data['provider']
GAS_PRICE = data['gasPrice'] * 10 ** 9
GAS_PRICE_SETTLE = data['GasSettlePrice'] * 10 ** 9
GAS_LIMIT = data['gasLimit']
LOW_DEFENSE = data['lowdefensePoint']
LOW_GAS = data['lowGas']
TEMA_ID_1 = data['teamFirst']
TEMA_ID_2 = data['teamSecond']
# End setting

# Line notify
line = LINE(TOKEN_LINE)

# Web3 Provider
web3 = Web3(Web3.HTTPProvider(PROVIDER))
contract = web3.eth.contract(address=CONTRACT,abi= ABI)

def addTable(txn_receipt,gameId,function,status,name):
    try:
        if status == True:
            effectiveGasPrice = txn_receipt['effectiveGasPrice'] / (10 ** 18)
            gas = effectiveGasPrice * txn_receipt['gasUsed'] * 110.742
            sum = "{:.2f}".format(gas)
            gasPrice = "Gas Price :: %s$" % sum
            statusSettle = f'{function} success'
            nextTime = int(datetime.timestamp(datetime.now()) + 3600)
            nextTime = datetime.fromtimestamp(nextTime).strftime('%Y-%m-%d %H:%M:%S')
            lineMessage = f'Crabara info {name} :: {gameId} {function} success!'
            line.sendtext(lineMessage)
            message = f'{name} :: {gameId} {function}'
            time = str(datetime.now())
            table.add_row(
                time[0:19],
                str(message),
                gasPrice,
                str(statusSettle),
                nextTime,
            )
        elif status == False:
            effectiveGasPrice = txn_receipt['effectiveGasPrice'] / (10 ** 18)
            gas = effectiveGasPrice * txn_receipt['gasUsed'] * 110.742
            sum = "{:.2f}".format(gas)
            gasPrice = "Gas Price :: %s$" % sum
            statusAttack = f'{function} fail'
            message = f'{name} :: {gameId} {function}'
            nextTime = '0'
            lineMessage = f'Crabara info {name} :: {gameId} {function} fail!'
            line.sendtext(lineMessage)
            time = str(datetime.now())
            table.add_row(
                time[0:19],
                str(message),
                gasPrice,
                str(statusAttack),
                nextTime,
            )
        
    except:
        print("Can't add Table data!")
        
def addTableFail(txn_receipt,gameId,function):
    effectiveGasPrice = txn_receipt['effectiveGasPrice'] / (10 ** 18)
    gas = effectiveGasPrice * txn_receipt['gasUsed'] * 110.742
    sum = "{:.2f}".format(gas)
    gasPrice = "Gas Price :: %s$" % sum
    statusAttack = f'{function} fail'
    message = f'gameId :: {gameId} {function}'
    nextTime = '0'
    lineMessage = f'Crabara info gameId :: {gameId} {function} fail!'
    line.sendtext(lineMessage)
    time = str(datetime.now())
    table.add_row(
        time[0:19],
        str(message),
        gasPrice,
        str(statusAttack),
        nextTime,
    )
    
def getGasPrice():
    try:
        
        response = requests.get("https://api.debank.com/chain/gas_price_dict_v2?chain=avax")
        data = response.json()
    except:
        print('Not find api gas price')
        
    return int(data['data']['normal']['price'] / 10 ** 9)

def getTeamAttack():
    try:
        
        response = requests.get("https://idle-api.crabada.com/public/idle/mines?page=1&status=open&looter_address=0x4185185d0328ac80e937b8bbab64869a5cb989aa&can_loot=1&limit=10")
        data = response.json()
    except:
        print('Not find api team attack')
    
    return data    
        
def getPo(page):
    try:

        for i in range(page):
            if i == 0:
                i = i + 1
            response = requests.get("https://api.crabada.com/public/crabada/selling?limit=20&page=%d&from_breed_count=0&to_breed_count=5&from_legend=0&to_legend=6&from_pure=0&to_pure=6&from_price=0&stage=1&orderBy=price&order=asc" %i )
            data = response.json()
            
            for key in data['result']['data']:
                armor = key['armor']
                hp = key['hp']
                damage = key['damage']
                id = key['id']
                power = hp + damage + armor
                price = int(key['price'] / 10 ** 18)
                if power >= 210 and power <= 300:
                    print(f'Id :: {id}  Power :: {power}  Price :: {price} Page :: {i}')
            
            
    except:
        print('Not find api team attack')
    
    return {"da": 'sad'}         

def sendTran(gameId,teamId,name):
    
    status = False
    print(f'Please wait attacking gameId :: {gameId}')
    nonce = web3.eth.getTransactionCount(ACCOUNT)
    tx = {
        'chainId': 43114,
        'nonce': nonce,
        'value': 0,
        'gas': GAS_LIMIT,
        'gasPrice': GAS_PRICE,
        'from': ACCOUNT,
        'to': CONTRACT,
        'data': contract.encodeABI(fn_name='attack',args=[gameId, teamId])
    }
    signed_tx = web3.eth.account.signTransaction(tx,PRIVATE_KEY)
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    try:
        txn_receipt = web3.eth.waitForTransactionReceipt(web3.toHex(tx_hash), timeout=30)
    except Exception:
        status = False
        message = f'{name} ::  {gameId} attack'
        nextTime = int(datetime.timestamp(datetime.now()) + 3600)
        time = str(datetime.now())
        table.add_row(
            time[0:19],
            str(message),
            '0',
            'Attack fail',
            '0',
        )
        
        return status
    else:
        if txn_receipt['status'] == 1:
            status = True
            addTable(txn_receipt,gameId,'attack',status,name)
            
            
        else:
            status = False
            addTable(txn_receipt,gameId,'attack',status,name)
            
        return status

def settle(gameId,name):
    
    status = False
    print(f'Please wait settleing gameId :: {gameId}')
    nonce = web3.eth.getTransactionCount(ACCOUNT)
    tx = {
        'chainId': 43114,
        'nonce': nonce,
        'value': 0,
        'gas': GAS_LIMIT,
        'gasPrice': GAS_PRICE_SETTLE,
        'from': ACCOUNT,
        'to': CONTRACT,
        'data': contract.encodeABI(fn_name='settleGame',args=[gameId])
    }
    signed_tx = web3.eth.account.signTransaction(tx,PRIVATE_KEY)
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    try:
        txn_receipt = web3.eth.waitForTransactionReceipt(web3.toHex(tx_hash), timeout=30)
    except Exception:
        status = False
        message = f'Crabara info gameId :: {gameId} settle'
        time = str(datetime.now())
        table.add_row(
            time[0:19],
            str(message),
            '0',
            'Settle fail',
            '0',
        )
        return status
    else:
        
        if txn_receipt['status'] == 1:
            status = True
            addTable(txn_receipt,gameId,'settle',status,name)
            
        else:
            status = False 
            addTable(txn_receipt,gameId,'settle',status,name)
              
        return status
      
def getTimeAttack(teamId):
    # print('Check Time')
    checkTime = False
    getStamina = contract.functions.getTeamInfo(teamId).call()
    nextAttack = int(getStamina[7])
    nowTime = datetime.timestamp(datetime.now())
    sum = int(nextAttack - nowTime)
    # print(f'sum :: {sum}')
    obj = {}
    if sum < 0:
        checkTime = True
        obj = {
            "checkTime": checkTime,
            "currentGameId": getStamina[6]
        }
    else:
        obj = {
        "checkTime": checkTime,
        "currentGameId": getStamina[6]
        }
        print("Next time ::",datetime.fromtimestamp(nextAttack).strftime('%Y-%m-%d %H:%M:%S'))
        time.sleep(sum)
        
    return obj
    
def main(teamId,power,name):
    
    while True:
        t = threading.currentThread()
        data = getTimeAttack(teamId)
        gasPrice = 0
        if data['checkTime'] == True:
            loop = True
            
            gasPrice = getGasPrice()
            if gasPrice <= LOW_GAS:
                print(f'Gas Low {LOW_GAS}  Gas Price :: {gasPrice}')
                
                currentGameId = int(data['currentGameId'])
                if currentGameId != 0:
                    logStatus = settle(currentGameId,name)
                    # print(f'logStatus :: {logStatus}')
                    if logStatus == False:
                        loop = False
                    else:
                        loop = True
                
                      
                while loop:
                    respo = getTeamAttack()
                    
                    if respo['result']['data'] != None:
                        for key in respo['result']['data']:
                            gameId = key['game_id']
                            defensePoint = key['defense_point']
                            if defensePoint < power and defensePoint > LOW_DEFENSE:
                                print(f'GameId :: {gameId} Power :: {defensePoint}')
                                result = sendTran(gameId,teamId,name)
                                # print(f'result :: {result}')
                                if result == True:
                                    loop = False
                                    # print(f'attack loop :: {loop}')
                                    break
                                else:
                                    time.sleep(3)
                                    loop = False
                                    break
                    else:
                        print('Data is none')
                        loop = False
                # print('Exic loop attack')
                console.print(table)
            else:
                print(f'Gas Hight 120  Gas :: {gasPrice}' )
                time.sleep(3)                
        else:
            print('Cooldown please wait! :)')
            
        # print('Next new loop ')
        # console.print(table)
    
              
                   
def apiCoinCrabada():
    
    try:
        
        while True:
        
            crabada = cg.get_price(ids='Crabada', vs_currencies='thb')
            values = [[crabada['crabada']['thb']]]
            treasure_under_sea = cg.get_price(ids='treasure-under-sea', vs_currencies='thb')
            tus = [[treasure_under_sea['treasure-under-sea']['thb']]]
            request =  sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                        range="Mine!Q2",valueInputOption="USER_ENTERED",body={"values": values}).execute()
            request =  sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                        range="Mine!P2",valueInputOption="USER_ENTERED",body={"values": tus}).execute()
            time.sleep(60)
    except:
        print('API not find coin price')

if __name__ == '__main__':
        
        pCoin = threading.Thread(target=apiCoinCrabada, args=())
        pCoin.start()
        t1 = threading.Thread(target=main, args=(TEMA_ID_1,659,"One"))
        t1.start()
        t2 = threading.Thread(target=main, args=(TEMA_ID_2,652,"Two"))
        t2.start()
        # p = Process(target=getPo,args=(21,))
        # p.start()

        
        
