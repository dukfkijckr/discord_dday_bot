import discord
from discord import app_commands
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# 봇 토큰 설정
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

# 데이터 파일
DATA_FILE = 'dday.json'

# --- 데이터 관리 함수 ---

# JSON 파일에서 디데이 데이터를 불러오는 함수 (서버별로 분리)
def load_data(guild_id: str):
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
            return all_data.get(guild_id, {})
    except json.JSONDecodeError:
        return {}

# 디데이 데이터를 JSON 파일에 저장하는 함수 (서버별로 분리)
def save_data(guild_id: str, guild_data: dict):
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
        except json.JSONDecodeError:
            all_data = {}
    else:
        all_data = {}

    all_data[guild_id] = guild_data

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)

# --- 봇 클라이언트 설정 ---

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

intents = discord.Intents.default()
client = MyClient(intents=intents)

# --- 이벤트 ---

@client.event
async def on_ready():
    print(f'{client.user} (ID: {client.user.id}) 봇이 성공적으로 로그인했습니다.')
    print('------')

# --- 명령어 ---

@client.tree.command(name="디데이-추가", description="새로운 디데이를 추가합니다.")
@app_commands.describe(
    title="기억할 디데이 제목",
    date_str="날짜 (YYYYMMDD)"
)
async def add_dday(interaction: discord.Interaction, title: str, date_str: str):
    try:
        target_date = datetime.strptime(date_str, '%Y%m%d')
        formatted_date = target_date.strftime('%Y-%m-%d')
    except ValueError:
        await interaction.response.send_message("❌ 날짜 형식이 올바르지 않아요. `YYYYMMDD` 형식으로 입력해주세요.", ephemeral=True)
        return

    guild_id = str(interaction.guild_id)
    data = load_data(guild_id)

    if title in data:
        await interaction.response.send_message(f"❌ 이미 '{title}' 제목의 디데이가 존재해요. 다른 제목을 사용해주세요.", ephemeral=True)
        return

    data[title] = formatted_date
    save_data(guild_id, data)

    await interaction.response.send_message(f"✅ 디데이 '{title}' ({formatted_date})가 성공적으로 추가되었어요!")

@client.tree.command(name="디데이-삭제", description="등록된 디데이를 삭제합니다.")
@app_commands.describe(title="삭제할 디데이의 제목")
async def delete_dday(interaction: discord.Interaction, title: str):
    guild_id = str(interaction.guild_id)
    data = load_data(guild_id)

    if title not in data:
        await interaction.response.send_message(f"❌ '{title}' 제목의 디데이를 찾을 수 없어요.", ephemeral=True)
        return

    del data[title]
    save_data(guild_id, data)

    await interaction.response.send_message(f"🗑️ 디데이 '{title}'가 삭제되었어요.")

@client.tree.command(name="디데이-확인", description="모든 디데이를 확인합니다.")
async def check_dday(interaction: discord.Interaction):
    guild_id = str(interaction.guild_id)
    data = load_data(guild_id)

    if not data:
        await interaction.response.send_message("등록된 디데이가 하나도 없어요.", ephemeral=True)
        return

    embed = discord.Embed(
        title="📅 등록된 디데이 목록",
        color=discord.Color.blue()
    )

    today = datetime.now()
    sorted_ddays = sorted(data.items(), key=lambda item: datetime.strptime(item[1], '%Y-%m-%d'))

    for title, date_str in sorted_ddays:
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
        days_left = (target_date - today).days

        if days_left + 1 == 0:
            dday_string = "**D-Day!** 🎉"
        elif days_left + 1 > 0:
            dday_string = f"**D-{days_left + 1}**"
        else:
            dday_string = f"**D+{-days_left - 1}**"

        formatted_date = target_date.strftime('%Y. %m. %d.')
        embed.add_field(name=f"📌 {title}", value=f"{dday_string} | {formatted_date}", inline=False)

    await interaction.response.send_message(embed=embed)

# --- 봇 실행 ---

if TOKEN == '여기에_디스코드_봇_토큰을_붙여넣으세요':
    print("오류: 봇 토큰이 설정되지 않았습니다.")
else:
    client.run(TOKEN)
