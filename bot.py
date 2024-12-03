import discord
from discord.ext import commands
import os
import json
from typing import Optional
from main import *
from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

LEADERBOARD_STATE_FILE = "leaderboardreference.json"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="//", intents=intents)

leaderboard_message: Optional[discord.Message] = None

RANK_ICONS = {
    "IRON": "<:iron:1313317785744576572>",
    "BRONZE": "<:bronze:1313317780002705418>",
    "SILVER": "<:silver:1313317784008265769>",
    "GOLD": "<:gold:1313317778450550865>",
    "PLATINUM": "<:platinum:1313317781927886858>",
    "EMERALD": "<:emerald:1313319095004827740>",
    "DIAMOND": "<:diamond:1313317772465406106>",
    "MASTER": "<:master:1313317786919108619>", 
    "GRANDMASTER": "<:grandmaster:1313317776437280790>",
    "CHALLENGER": "<:challenger:1313317774319161375>",
}


def save_leaderboard_state(channel_id: int, message_id: int):
    state = {"channel_id": channel_id, "message_id": message_id}
    with open(LEADERBOARD_STATE_FILE, "w") as file:
        json.dump(state, file)

def sort_leaderboard(players):
    sorted_players = sorted(
        players.items(),
        key=lambda x: (
            RANK_ORDER.get(x[1]["Ranked Data"]["tier"].upper(), 10),  
            RANK_POSITION.get(x[1]["Ranked Data"]["rank"].upper(), 10),  
            -x[1]["Ranked Data"]["leaguePoints"] 
        )
    )
    return dict(sorted_players[:10])  


def load_leaderboard_state():
    if not os.path.exists(LEADERBOARD_STATE_FILE):
        return None

    try:
        with open(LEADERBOARD_STATE_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    
def loadLeaderboardData():
    try:
        with open("saved.json", "r") as file:
            return json.load(file)  
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def create_leaderboard_embed(players):
    embed = discord.Embed(
        title="TFT Ranked Leaderboards",
        description="Clo Will Surpass Neil TRUE OR FALSE?!?!",
        color=discord.Color.gold(),
    )

    for index, (player_name, player_data) in enumerate(players.items(), start=1):
        rank_data = player_data["Ranked Data"]
        tier = rank_data["tier"].capitalize()
        rank = rank_data["rank"].upper()
        lp = rank_data["leaguePoints"]
        wins = rank_data["wins"]
        losses = rank_data["losses"]
        winrate = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0
        hot_streak = "🔥 Yes!" if rank_data["hotStreak"] else "👎 No"

        rank_icon = RANK_ICONS.get(tier.upper(), "")
        favorite_units = player_data.get("Favourite Units", [])
        favorite_units_text = ", ".join(favorite_units) if favorite_units else "No Favourite units listed."

        embed.add_field(
            name=f"{index}. {player_name} #{player_data['Tag']}",
            value=(
                f"{rank_icon} **Tier:** {tier} {rank} ({lp} LP)"
                f"**Wins/Losses:** {wins} W / {losses} L\n"
                f"**Winrate:** {winrate:.2f}%\n"
                f"**WinStreak:** {hot_streak}\n"
                f"**Favorite Units:** {favorite_units_text}\n"
            ),
            inline=False,
        )

    embed.set_footer(text="If Bachi Is Higher Rank Than You, Consider Quitting.")
    return embed


@bot.event
async def on_ready():
    global leaderboard_message

    print(f"Bot is ready! Logged in as {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s) to the server.")

        state = load_leaderboard_state()
        if state:
            channel = bot.get_channel(state["channel_id"])
            if channel:
                try:
                    leaderboard_message = await channel.fetch_message(state["message_id"])
                    print("Leaderboard message successfully loaded from state.")
                except discord.NotFound:
                    print("Leaderboard message not found. Resetting state.")
                    save_leaderboard_state(None, None)  # Reset state
    except Exception as e:
        print(f"Failed to sync commands or load leaderboard state: {e}")



def create_leaderboard_embed(players):
    embed = discord.Embed(
        title="TFT Ranked Leaderboards",
        description="Clo Will Surpass Neil TRUE OR FALSE?!?!",
        color=discord.Color.gold(),
    )

    for index, (player_name, player_data) in enumerate(players.items(), start=1):
        rank_data = player_data["Ranked Data"]
        tier = rank_data["tier"].capitalize()
        rank = rank_data["rank"].upper()
        lp = rank_data["leaguePoints"]
        wins = rank_data["wins"]
        losses = rank_data["losses"]
        winrate = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0
        hot_streak = "🔥 Yes!" if rank_data["hotStreak"] else "👎 No"

        favorite_units = player_data.get("Favourite Units", [])
        favorite_units_text = ", ".join(favorite_units) if favorite_units else "No Favourite units listed."

        embed.add_field(
            name=f"{index}. {player_name} #{player_data['Tag']}\n\n",
            value=(
                f"**Tier:** {tier} {rank} ({lp} LP)\n"
                f"**Wins/Losses:** {wins} W / {losses} L\n"
                f"**Winrate:** {winrate:.2f}%\n"
                f"**WinStreak:** {hot_streak}\n"
                f"**Favorite Units:** {favorite_units_text}\n"
            ),
            inline=False,
        )

    embed.set_footer(text="If Bachi Is Higher Rank Than You, Consider Quitting.")
    return embed


@bot.tree.command(name="refreshleaderboard", description="Refresh the leaderboard with updated data")
async def refresh_leaderboard(interaction: discord.Interaction):
    global leaderboard_message

    await interaction.response.defer(ephemeral=True)

    file_path = "saved.json"
    try:
        success = refreshLeaderboard(file_path)
        if not success:
            await interaction.followup.send("Failed to refresh leaderboard data.", ephemeral=True)
            return
    except Exception as e:
        await interaction.followup.send(f"An error occurred while refreshing data: {e}", ephemeral=True)
        return

    players = loadLeaderboardData()
    if not players:
        await interaction.followup.send("No leaderboard data found after refreshing.", ephemeral=True)
        return

    top_players = sort_leaderboard(players)
    embed = create_leaderboard_embed(top_players)

    try:
        if leaderboard_message is None:
            leaderboard_message = await interaction.channel.send(embed=embed)
            save_leaderboard_state(interaction.channel.id, leaderboard_message.id)
        else:
            await leaderboard_message.edit(embed=embed)

        await interaction.followup.send("Leaderboard refreshed successfully!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Failed to update leaderboard: {e}", ephemeral=True)





@bot.tree.command(name="addtftaccount", description="Add an account to the leaderboard")
async def add_account(
    interaction: discord.Interaction,
    game_name: str,
    tag: str,
):
    puuid = getPUUID(game_name, tag)

    if not puuid:
        await interaction.response.send_message(
            f"Failed to fetch data for **{game_name}#{tag}**. Please double-check your input.",
            ephemeral=True,
        )
        return

    summoner_data = getSummoner(puuid)
    ranked_data = getTFTRankedData(summoner_data)

    if not ranked_data:
        await interaction.response.send_message(
            "Play some ranked games before adding yourself....",
            ephemeral=True,
        )
        return

    try:
        complete = combineDataAndSave("saved.json", puuid, game_name, tag, summoner_data, ranked_data)
        if not complete:
            await interaction.response.send_message(
                f"**{game_name}#{tag} is already added. Use `/RefreshLeaderboard` to update the leaderboard.**",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"Account added!\n"
            f"**Game Name**: {game_name}\n"
            f"**Tag**: {tag}\n"
            "Refresh the leaderboard for updated results.",
            ephemeral=True
        )
    except Exception as exception:
        await interaction.response.send_message(
            f"Failed to save account data for **{game_name}#{tag}**.",
            ephemeral=True,
        )


bot.run(DISCORD_BOT_TOKEN)
