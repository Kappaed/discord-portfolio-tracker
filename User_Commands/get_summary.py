import Portfolio
import API.zapper
import discord
from discord.ext import commands


@commands.command()
async def get_summary(ctx):
    if Portfolio.main_addr == None:
        await ctx.send("Main address has not been set. Please try again.")
        return
    if Portfolio.total_balance == 0:
        await ctx.send("Wallet balance is current zero. Please try again.")
        return

    group_bal_by_network = {network: 0 for network in API.zapper.EVM_NETWORKS}
    discord_purple = discord.colour.Color.purple()

    for defi_app_info in Portfolio.defi_apps.values():
        network = defi_app_info["network"]
        defi_app_bal = defi_app_info["total_balance"]
        group_bal_by_network[network] += defi_app_bal
    for token_info in Portfolio.wallet["tokens"].values():
        network = token_info["network"]
        token_bal = token_info["balance"]
        group_bal_by_network[network] += token_bal

    network_embed = discord.Embed(
        title="Network Summary",
        description="Group Wallet Balances by Network",
        color=discord_purple,
    )

    network_embed.set_author(
        name=Portfolio.main_addr, url=f"https://zapper.fi/account/{Portfolio.main_addr}"
    )
    for network in sorted(
        group_bal_by_network, reverse=True, key=group_bal_by_network.get
    ):
        network_embed.add_field(
            name=network,
            value=f"${group_bal_by_network[network]:.2f}",
        )

    await ctx.send(embed=network_embed)

    wallet_summary = discord.Embed(
        title=f"Wallet Summary ${Portfolio.total_balance:.2f}",
        description="\u200b",
        color=discord_purple,
    )

    wallet_summary.set_author(
        name=Portfolio.main_addr, url=f"https://zapper.fi/account/{Portfolio.main_addr}"
    )

    add_wallet_token_field(wallet_summary, Portfolio.wallet["tokens"])
    add_defi_app_fields(wallet_summary, Portfolio.defi_apps)

    await ctx.send(embed=wallet_summary)


def create_defi_cat_str(dict_of_dicts):
    output = ""
    for token in dict_of_dicts:
        balance = dict_of_dicts[token]
        output += f"{token} ${balance:.2f}\n"
    return output if output != "" else "\u200b"


def add_wallet_token_field(embed, wallet_token_dict):
    token_wallet_summary_str = ""
    total_balance = 0
    for token in wallet_token_dict:
        token_info = wallet_token_dict[token]
        total_balance += token_info["balance"]
        token_wallet_summary_str += f'{token}\t${token_info["balance"]:.2f}\n'

    embed.add_field(
        name=f"Wallet Tokens (${total_balance:.2f})",
        value=token_wallet_summary_str,
    )


def add_defi_app_fields(embed, defi_apps_dict):
    for defi_app in defi_apps_dict:
        defi_app_info = defi_apps_dict[defi_app]
        embed.add_field(
            name=f'{defi_app} (${defi_app_info["total_balance"]:.2f})',
            value=f'network: {defi_app_info["network"]}',
            inline=False,
        )

        for category in defi_app_info:
            if category in ["supplied", "debt", "claimable"]:
                field_name = category
                field_val = create_defi_cat_str(defi_app_info[category])
                embed.add_field(name=field_name, value=field_val, inline=True)
