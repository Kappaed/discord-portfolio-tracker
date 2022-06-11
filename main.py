import discord
import os
import re
import json
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth

ZAPPER_PUBLIC_API_KEY = "96e0cc51-a62e-42ca-acee-910ea7d2a241"
ZAPPER_BASE_API_URL = "https://api.zapper.fi/v2/"
AVAILABLE_NETWORKS = ["ethereum", "polygon", "optimism", "gnosis", "binance-smart-chain", "fantom", "avalanche", "arbitrum", "celo", "harmony", "moonriver", "bitcoin", "cronos", "aurora", "evmos"]
ARGUMENTS = {"set_main":".set_main_address"}
AUTH_PAYLOAD = HTTPBasicAuth(ZAPPER_PUBLIC_API_KEY, "")

def extract_token_info(token_dict, storedIn="wallet"):
    try:
      token_network = token_dict["network"]
      if storedIn == "wallet":
        context = token_dict["context"]
      else:
        #storedIn == "defi-app"
        context = token_dict["breakdown"][0]["context"]
      token_symbol = context["symbol"]
      token_supply = context["balance"]  
      token_balance = int(token_dict["balanceUSD"])
    except KeyError as e:
      msg = f'{e.args[0]} not found in {token_dict}: Real key hierarchy in {",".join(find_key_hierarchy(token_dict, e.args[0])) if find_key_hierarchy(token_dict, e.args[0]) != None else "unable to be found."}'
      raise KeyError(msg) from e
    output = {"network": token_network, "symbol": token_symbol, "supply": token_supply, "balance": token_balance}
    if storedIn != "wallet":
      output["vault"] = token_dict["appId"]
    return output


def find_key_hierarchy(obj, to_find_key):

  def dfs(currKey, currObj, chain):
    if currKey == to_find_key:
      return chain
    if isinstance(currObj, dict):
      for key in currObj:
        ans = dfs(key, currObj[key], chain+[key])
        if ans:
          return ans
    if isinstance(currObj, list):
      for item in currObj:
        if isinstance(item, (list, dict)):
          ans = dfs(currKey, item, chain)
          if ans:
            return ans
    return None

  return dfs(None, obj, [])
  

    
    

class MainClient(discord.Client):
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))
        #await client.user.edit(avatar="")
    async def on_message(self, message):
        # print('Message from {0.author}: {0.content}'.format(message))
        split_msg = message.content.split()
        if split_msg[0] == ARGUMENTS["set_main"] and len(split_msg) > 1:
          main_addr = split_msg[1]
          channel = client.get_channel(message.channel.id)
          get_req = ZAPPER_BASE_API_URL + "balances"
          payload = {"addresses[]":[main_addr], "networks[]": AVAILABLE_NETWORKS, "useNewBalancesFormat": "true", "bundled": "false"}
          try:
            r = requests.get(get_req, auth=AUTH_PAYLOAD, params=payload)
            if r.status_code == 200:
              msg = f"Setting bot to track {main_addr}..."
              print(msg)
              await channel.send(msg)
            else:
              msg = f"Invalid status code: {r.status_code}"
              print(msg)
              await channel.send(msg)
          except requests.exceptions.RequestException as e:
            msg = f"{r.status_code}: request exception\n{e}"
            print(msg)
            await channel.send(msg)
          total_balance = 0
          parsed_arr = [json.loads(item.strip()) for item in re.split(r"event:\s+\w+\s+data:\s+", r.text) if item.startswith("{")]
          for item in parsed_arr:
            try:
              # print("wallet")
              balanceObj = item["balance"]
              if item['appId'] == "tokens":
                tokens = balanceObj["wallet"]
                token_type = "wallet"
              else:
                # print("defi")
                tokens = balanceObj["claimable"]
                token_type = "defi-app"          
              for key in tokens:
                token_info = extract_token_info(tokens[key], token_type)
                if token_type == "wallet":
                   print(f'network {token_info["network"]}: adding {token_info["supply"]} {token_info["symbol"]} (${token_info["balance"]} USD) to total balance.')
                else:
                  print(f'network {token_info["network"]} from app {token_info["vault"]}: adding {token_info["supply"]} {token_info["symbol"]} (${token_info["balance"]} USD) to total balance.')
                total_balance += token_info["balance"]
            except KeyError as e:
              print(e)
          print(f'total_balance: ${total_balance} USD')
          await channel.send("Setting bot information now...")
          try:
            await client.user.edit(username=f"Portfolio ${total_balance}")
          except e:
            await channel.send(f"{e} - please try changing username later.")
          
          
    


load_dotenv()
client = MainClient()
client.run(os.getenv("BOT_PASSWORD"))
