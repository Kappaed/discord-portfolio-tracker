from re import L
from turtle import color
from discord.ext import commands
import API.zapper
import Portfolio
import discord
from User_Commands.get_summary import add_wallet_token_field, add_defi_app_fields


dc_dict = discord.colour.Color

EVM_NETWORKS_COLOURS = {
    "ethereum": dc_dict.blurple(),
    "polygon": dc_dict.purple(),
    "optimism": dc_dict.red(),
    "gnosis": dc_dict.dark_blue(),
    "binance-smart-chain": dc_dict.dark_magenta(),
    "fantom": dc_dict.blue(),
    "avalanche": dc_dict.dark_red(),
    "arbitrum": dc_dict.dark_blue,
    "celo": dc_dict.green(),
    "harmony": dc_dict.green(),
    "moonriver": dc_dict.dark_purple(),
    "bitcoin": dc_dict.orange(),
    "cronos": dc_dict.dark_grey(),
    "aurora": dc_dict.dark_green(),
    "evmos": dc_dict.dark_theme(),
}


@commands.command()
async def get_by_network(ctx, input_network=None):
    available_networks = API.zapper.EVM_NETWORKS
    if input_network not in available_networks:
        await ctx.send(f"{input_network} is not an available EVM network to query.")
    wallet_tokens = {}
    defi_apps = {}
    for token in Portfolio.wallet["tokens"]:
        token_info = Portfolio.wallet["tokens"][token]
        t_network = token_info["network"]
        t_balance = token_info["balance"]
        if t_network == input_network:
            wallet_tokens[token] = {"balance": t_balance}

    for defi_app in Portfolio.defi_apps:
        defi_app_info = Portfolio.defi_apps[defi_app]
        dapp_network = defi_app_info["network"]
        if input_network == dapp_network:
            defi_apps[defi_app] = defi_app_info

    if len(wallet_tokens) + len(defi_apps) == 0:
        await ctx.send(
            "No wallet tokens or defi-apps for this network were found in this wallet."
        )
        return

    network_balance = sum([x["balance"] for x in wallet_tokens.values()]) + sum(
        [x["total_balance"] for x in defi_apps.values()]
    )

    network_embed = discord.Embed(
        title=f"{input_network} (${network_balance:.2f})",
        color=EVM_NETWORKS_COLOURS[input_network],
    )

    add_wallet_token_field(network_embed, wallet_tokens)
    add_defi_app_fields(network_embed, defi_apps)

    await ctx.send(embed=network_embed)
