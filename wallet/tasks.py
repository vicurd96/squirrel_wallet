from squirrel_wallet.celery import app
from django.conf import settings
from django.utils import timezone
from web3 import Web3, HTTPProvider
from bit import Key, PrivateKeyTestnet
from bit.network import get_fee, get_fee_cached, NetworkAPI
from wallet.models import *
from ethereum.transactions import Transaction as Tranx
from coinbase.wallet.client import Client
from eth_utils import from_wei,to_hex
from rlp import encode

from celery import task

@task()
def update_transactions():
    wallet = Wallet.objects.all()
    network = connect_ether_network()
    for user in wallet.iterator():
        if user.currency.abrev == 'BTC':
            tx_updated = NetworkAPI.get_transactions_testnet(user.address)
            tx = list(BTCTransaction.objects.filter(wallet=user).values_list('txid',flat=True))
            diff = list(set(tx_updated) - set(tx))
            for newtx in diff:
                tx = BTCTransaction(txid=newtx,wallet=user,status=True,type='IN',to=user.address)
                tx.save()
        elif user.currency.abrev == 'ETH':
            tx = ETHTransaction.objects.filter(wallet=user).order_by('-created_at').values_list('txid',flat=True)
            if tx or user.block:
                startblock = user.block if user.block else network.eth.getTransaction(tx.first())['blockNumber']
            else:
                startblock = None
            tx_updated = getTransactionsByAccount(myaccount=user.address,startBlockNumber=startblock,wallet=user)
            tx = list(tx)
            diff = list(set(tx_updated) - set(tx))
            for newtx in diff:
                tx = ETHTransaction(txid=newtx,wallet=user,status=True,type='IN',to=user.address)
                tx.save()

@task()
def update_balances():
    wallet = Wallet.objects.all()
    for user in wallet.iterator():
        if user.currency.abrev == 'BTC':
            key = PrivateKeyTestnet(user.private_key)
            user.balance = key.get_balance('btc')
            user.save()
        else:
            network = connect_ether_network()
            user.balance = from_wei(network.eth.getBalance(user.address),'ether')
            user.save()

def connect_ether_network(api=settings.ETH_API_URL):
    provider = HTTPProvider(api)
    web3 = Web3(provider)
    return web3

@app.task
def process_tx_btc(tx_hex,txmodel):
    try:
        NetworkAPI.broadcast_tx_testnet(tx_hex)
        tx.status = True
    except ConnectionError:
        tx.status = None
    tx.save()

@app.task
def process_all_pending_txs_btc():
    txlist = BTCTransaction.objects.filter(status__isnull=True)
    for tx in txlist.iterator():
        tx_hex = key.sign_transaction(tx.json)
        NetworkAPI.broadcast_tx_testnet(tx_hex)

@app.task
def process_all_pending_txs_eth():
    txlist = ETHTransaction.objects.filter(status=False)
    network = connect_ether_network()
    for tx in txlist.iterator():
        wallet = tx.wallet
        nonce = network.eth.getTransactionCount(wallet.address)

        ''' Definiendo el gas total para la transacción '''
        startgas = network.eth.estimateGas({'to':tx.to,'from':wallet.address,'value':to_wei(tx.amount,'ether')})
        if tx.gas > startgas:
            startgas = tx.gas

        gasprice = network.eth.gasPrice
        data = b''

        if(from_wei(network.eth.getBalance(user.address),'ether') > tx.amount + from_wei(startgas,'ether')):
            txdata = Tranx(
                nonce = nonce,
                gasprice = gasprice,
                startgas = startgas,
                to = tx.to,
                value = to_wei(tx.amount, 'ether'),
                data = data,
            )
            txdata.sign(wallet.private_key)
            raw_tx = encode(txdata)
            raw_tx_hex = web3.toHex(raw_tx)
            tx.txid = network.eth.sendRawTransaction(raw_tx_hex)

            ''' Guardando la transacción '''
            tx.gasPrice = gasprice
            tx.gas = startgas
            tx.status = True
            tx.save()
        else:
            tx.status = None
            tx.save()

@app.task
def update_values():
    client = Client('OCXkM2XY6huUlHVD','6BdthS80bhLETRpTOHYpiMFTvkif2hcQ')
    priceBTC = client.get_buy_price(currency_pair='BTC-USD')
    priceETH = client.get_buy_price(currency_pair='ETH-USD')
    if priceBTC and priceETH:
        value = Value(btcvalue=priceBTC.amount,ethvalue=priceETH.amount)
        value.save()
