from discord.ext import commands
import API.zapper
import requests
import discord
import json
import re

def parse_tokens_res(r_data):
  parsed_arr = [json.loads(item.strip()) for item in re.split(r"event:\s+\w+\s+data:\s+", r_data.text) if item.startswith("{")]
  total_balance = 0
  parsed_info = {"total_balance": 0, "networks": {network: {"nw_balance":0 , "defi-apps":{}} for network in API.zapper.EVM_NETWORKS}}
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
        print(f'token price : {token_info["balance"]}')
        parsed_info["total_balance"] += token_info["balance"]
        parsed_info["networks"][token_info["network"]]["nw_balance"] += token_info["balance"]
        if token_type == "defi-app":
          parsed_info["networks"][token_info["network"]]["defi-apps"][token_info["vault"]] = {"balance": token_info["balance"]}
    except KeyError as e:
      print(e)
  return parsed_info

async def get_tokens(req_url, payload, ctx):
  try:
    r = requests.get(req_url, auth=API.zapper.AUTH, params=payload)
    if r.status_code == 200:
      msg = f"Setting bot to track {payload['addresses[]'][0]}..."
      print(msg)
      await ctx.send(msg)
    else:
      msg = f"Invalid status code: {r.status_code}"
      print(msg)
      await ctx.send(msg)
  except requests.exceptions.RequestException as e:
    msg = f"request exception: {e}"
    print(msg)
    await ctx.send(msg)
  return r

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
      token_balance = round(float(token_dict["balanceUSD"]),2)
    except KeyError as e:
      msg = f'{e.args[0]} not found in {token_dict}: Real key hierarchy in {",".join(find_key_hierarchy(token_dict, e.args[0])) if find_key_hierarchy(token_dict, e.args[0]) != None else "unable to be found."}'
      raise KeyError(msg) from e
    output = {"network": token_network, "symbol": token_symbol, "supply": token_supply, "balance": token_balance}
    if storedIn != "wallet":
      output["vault"] = token_dict["appId"]
    return output
  
@commands.command()
async def set_main_addr(ctx, main_addr = None):
  if main_addr == None:
    ctx.send("Invalid arguments. Please try again.")
    return
  get_req = API.zapper.BASE_URL + "balances"
  payload = {"addresses[]":[main_addr], "networks[]": API.zapper.EVM_NETWORKS, "useNewBalancesFormat": "true", "bundled": "false"}
  r = await get_tokens(get_req, payload, ctx)
  tokens_info = parse_tokens_res(r)
  total_balance = tokens_info["total_balance"]
  sorted_network_balances = [x for x in sorted(tokens_info["networks"], key= lambda x: tokens_info["networks"][x]["nw_balance"], reverse=True)]
  for network in sorted_network_balances:
    print(f'{network}:{tokens_info["networks"][network]["nw_balance"]}')
  
  print(tokens_info)
  print(f'total_balance: ${total_balance} USD')
  await ctx.send("Setting bot information now...")
  try:
    await ctx.author.edit(username=f"Total Portfolio ${total_balance}")
  except discord.errors.HTTPException as e:
    print(e)
    await ctx.send(e)
  
  


