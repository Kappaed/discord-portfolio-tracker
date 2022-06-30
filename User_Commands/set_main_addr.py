from discord.ext import commands
import API.zapper
import requests
import discord
import json
import re
import Portfolio


def parse_tokens_res(r_data):
    parsed_arr = [
        json.loads(item.strip())
        for item in re.split(r"event:\s+\w+\s+data:\s+", r_data.text)
        if item.startswith("{") and json.loads(item.strip()) != {}
    ]
    for item in parsed_arr:
        try:
            # print("wallet")
            tokens_categories = {}
            if item["appId"] == "tokens":
                tokens_categories["wallet"] = item["balance"]["wallet"]
                token_type = "wallet"
            else:
                # print("defi") / Not accounted for "NFT" (will just give key error when parsing & skip api "item")
                tokens_categories["claimable"] = item["balance"]["claimable"]
                tokens_categories["debt"] = item["balance"]["debt"]
                tokens_categories["supplied"] = {
                    i: item["app"]["data"][i] for i in range(len(item["app"]["data"]))
                }
                token_type = "defi-app"

            for category in tokens_categories:
                for key in tokens_categories[category]:
                    token_info = extract_token_info(tokens_categories[category][key])
                    symbol, balance, network, appID = (
                        token_info["symbol"],
                        token_info["balance"],
                        token_info["network"],
                        token_info["vault"],
                    )
                    if token_type == "wallet":
                        print(
                            f"network {network}: {symbol} (${balance} USD) to total balance."
                        )
                    else:
                        print(
                            f"network {network}: {appID} ({category}): adding {symbol} (${balance} USD) to total balance."
                        )

                    Portfolio.total_balance += balance
                    if token_type == "defi-app":
                        defi_app_key = f"{appID} ({network})"
                        if defi_app_key not in Portfolio.defi_apps:
                            Portfolio.defi_apps[defi_app_key] = {
                                "network": network,
                                "claimable": {},
                                "debt": {},
                                "supplied": {},
                                "total_balance": 0,
                            }

                        curr_defi_app = Portfolio.defi_apps[defi_app_key]
                        curr_defi_app["total_balance"] += balance
                        curr_defi_app[category][symbol] = balance

                    else:
                        Portfolio.wallet["total_balance"] += balance
                        Portfolio.wallet["tokens"][f"{symbol} ({network})"] = {
                            "network": network,
                            "balance": balance,
                        }

        except KeyError as e:
            # print(item)
            # print(category)
            # print(token_info)
            print("Key error: ", e)


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
                ans = dfs(key, currObj[key], chain + [key])
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


def extract_token_info(token_dict):
    try:
        token_network = token_dict["network"]
        token_symbol = token_dict["displayProps"]["label"]
        token_balance = round(float(token_dict["balanceUSD"]), 2)
        token_appID = token_dict["appId"]
    except KeyError as e:
        msg = f'{e.args[0]} not found in {token_dict}: Real key hierarchy in {",".join(find_key_hierarchy(token_dict, e.args[0])) if find_key_hierarchy(token_dict, e.args[0]) != None else "unable to be found."}'
        raise KeyError(msg) from e
    output = {
        "network": token_network,
        "symbol": token_symbol,
        "balance": token_balance,
        "vault": token_appID,
    }
    return output


@commands.command()
async def set_main_addr(ctx, main_addr=None):
    if main_addr == None:
        ctx.send("Invalid arguments. Please try again.")
        return
    Portfolio.main_addr = main_addr
    get_req = API.zapper.BASE_URL + "balances"
    payload = {
        "addresses[]": [main_addr],
        "networks[]": API.zapper.EVM_NETWORKS,
        "useNewBalancesFormat": "true",
        "bundled": "false",
    }
    r = await get_tokens(get_req, payload, ctx)
    parse_tokens_res(r)
    total_balance = Portfolio.total_balance
    print(f"total_balance: ${total_balance} USD")
    print(Portfolio.defi_apps)
    print(Portfolio.wallet)
    await ctx.send("Setting bot information now...")
    try:
        await ctx.author.edit(username=f"Total Portfolio ${total_balance}")
    except discord.errors.HTTPException as e:
        print(e)
        await ctx.send(e)
