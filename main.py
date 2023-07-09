//In a demonstration of absolute transparency, Photon Finance has graciously shared the source code of their Copy Trading bot with the community. 
As part of this commitment, we will be providing access to the main.py file, 
allowing individuals to explore the core functionality behind Photon Finance's exceptional copy trading system.//

'''
Binance copy trading bot

Made by Steinyyy 

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an 'as is' basis,
without warranties or conditions of any kind, either express or implied.
'''




from watch_trader import WatchedTrader
from client import TradeClient, TradeExchange
from common import *
import asyncio
import json



#manages all watchable traders and the exchange
class BinanceBot:
    exchange : TradeExchange
    #dictionary of all all traders; format {name:trader}
    traders : Dict[str, WatchedTrader]
    #list of all clients
    clients : List[TradeClient]
    
    def __init__(self) -> None:
        self.traders = {}
        self.clients = []
        self.exchange = TradeExchange()

    async def initialize(self, master_api_key, base_url):
        await self.exchange.initialize(master_api_key, base_url)

    #create a new trader to the list and update his positions for the first time
    async def newTrader(self, name : str, trader_uid : str):
        self.traders[name] = WatchedTrader(name, trader_uid)
        await self.traders[name].initialize()

    #make the client copy a trader with a given ratio. Trader will notify client when his positions have changed. Does not update client positions automatically.
    def watchTrader(self, client : TradeClient, trader_name : str, ratio : float):
        t = self.traders[trader_name]
        client.addTrader(t, ratio)
        t.addClient(client)

    #create a new client, with his public and secret api keys, and make him watch all listed traders (given as a list of tuples (name, ratio))
    async def newClient(self, client_name : str, api_key : str, secret_key : str, base_url : str, watched_traders : List[Tuple[str, float]]):
        cl = TradeClient(client_name, self.exchange)
        #make the client watch all the traders he wants to
        for name, ratio in watched_traders: self.watchTrader(cl, name, ratio)
        #update his positions - this also sells everything he had until now, if the traders don't own it as well
        await cl.initialize(self.exchange, api_key, secret_key, base_url)
        self.clients.append(cl)
        
    async def addTraders(self, traders):
        await asyncio.gather(*[self.newTrader(t["name"], t["uid"]) for t in traders])
        
    async def addClients(self, clients, base_url):
        await asyncio.gather(*[self.newClient(c["name"], c["public_key"], c["private_key"], base_url, [(t["name"], t["ratio"]) for t in c["copy_traders"]]) for c in clients])

    #close connections of all traders and stop all their tasks
    async def destroy(self):
        await asyncio.gather(*[c.destroy() for c in self.clients])
        
        for t in self.traders.values(): t.destroy()
        #wait for all trader tasks to finish
        await asyncio.gather(*[t.run_task for t in self.traders.values()])
        


SETTINGS_FILE = "settings.json"
async def main():
    #load settings as a json
    settings = json.loads(open(SETTINGS_FILE).read())
    
    #create a bot
    bot = BinanceBot()
    #initialize the bot and the underlying exchange
    await bot.initialize(settings["master_public_api_key"], settings["binance_base_url"])
    #add all traders from settings
    await bot.addTraders(settings["traders"])
    #add all clients from settings
    await bot.addClients(settings["clients"], settings["binance_base_url"])
    
    #just sleep for eternity - this will give control to the other async methods and let them do their job
    #when the service is done, it might be good to have a mechanic for shutting down the bot here = it should wait until it is shutdown time
    await asyncio.sleep(float("inf"))

    #destroy all connections
    await bot.destroy()

    
   
#this line of code avoids errors when the bot would end
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
#run the bot
asyncio.run(main())


