from pytube import Playlist
import discord
from discord.ext import commands
import os
import asyncio
import yt_dlp
from KeepAlive import keep_alive
import traceback
import sys

playlist_lock = asyncio.Lock()
# 設定機器人指令前綴
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# 指定下載音樂的資料夾
DOWNLOAD_FOLDER = "C:/Users/qq671/Music/DCRobot/"
# os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

Queue = []

# with open('/etc/secrets/cookies.txt', 'r') as file:
#     cookies = file.read()

ydl_opts = {
    "format": "bestaudio/best",
    "quiet": True,
    "extract_flat": True,
    "extractaudio": True,
    'audioquality': 1,
    'nocheckcertificate': True,
    #'cookies': r'/etc/secrets/cookies.txt',
}


@bot.event
#當機器人完成啟動時
async def on_ready():
    game = discord.Game('裝忙中')
    #discord.Status.<狀態>，可以是online,offline,idle,dnd,invisible
    await bot.change_presence(status=discord.Status.idle, activity=game)
    print(f"已登入為 {bot.user}")
    
# @bot.event
# #當有訊息時
# async def on_message(message):
#     #排除自己的訊息，避免陷入無限循環
#     if message.author == bot.user:
#         return
#     #如果包含 ping，機器人回傳 pong
#     if message.content == '可憐':
#         await message.channel.send('pong')

@bot.command()
async def join(ctx):
    
    #這裡的指令會讓機器人進入call他的人所在的語音頻道
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if ctx.author.voice == None:
        await ctx.send("請先加入一個語音頻道！")
    elif voice == None:
        voiceChannel = ctx.author.voice.channel
        await voiceChannel.connect()
        await ctx.send(f"成功加入 {ctx.voice_client.channel}")
    else:
        await ctx.send(f"已加入 {ctx.voice_client.channel}")
        
@bot.command()
async def leave(ctx):
    """離開語音頻道"""
    if ctx.voice_client:
        ctx.voice_client.pause()
        game = discord.Game('裝忙中')
        await bot.change_presence(status=discord.Status.idle, activity=game)
        await ctx.voice_client.disconnect()
        await ctx.send("已離開語音頻道")
    else:
        await ctx.send("機器人未在任何語音頻道內")
  

      
@bot.command()
async def play(ctx, ADDurl: str = None):
    #print(len(Queue))
    if ADDurl != None:
        await add_f(ctx, ADDurl)

    if len(Queue) == 0:
        await ctx.send(f"當前音樂佇列為空")
        return
    
    """串流播放 YouTube 音樂"""
    if not ctx.voice_client:
        await ctx.invoke(bot.get_command("join"))  # 自動加入語音頻道

    
    while len(Queue) != 0 and ctx.voice_client is not None:
        print('Running')
        url = Queue[0]
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                audio_url = info['url']
                # 播放音樂
                if ctx.voice_client:
                    ctx.voice_client.stop()
    
                ctx.voice_client.play(discord.FFmpegPCMAudio(audio_url, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"),
                                    after=lambda e: print(f"播放完成: {info['title']}"))
                
                print("正在播放: "+info['title'])
                await ctx.send(f"正在播放♫: {info['title']}")
                game = discord.Game('♫正在唱歌♫')
                await bot.change_presence(status=discord.Status.idle, activity=game)
                # 等待直到音樂播放完成
                while ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                    await asyncio.sleep(1)  # 等待音樂播放完成
                
                # 音樂播放完成後，進入下一輪
                async with playlist_lock:
                    Queue.pop(0)
                    print(f"刪掉: {info['title']}")


                
        except Exception as e:
            print(f"播放失敗：{e}")
            if len(Queue) != 0:
                async with playlist_lock:
                    Queue.pop(0)
                print(f"刪掉: {info['title']}")
                
            if ctx.voice_client:
                await ctx.send(f"播放失敗已跳過：{info['title']}")
                if len(Queue) == 0:
                    await ctx.send(f"當前音樂佇列為空")
                else:
                    await ctx.send("已切換下一首⏭️")
           

@bot.command()
async def add(ctx, playlist_url: str):
    """將音樂加入佇列"""
    async with playlist_lock:
        Queue.extend(Playlist(playlist_url))
        await ctx.send(f"已加入 {len(playlist_url)} 首音樂")
        
@bot.command()
async def add_f(ctx, playlist_url: str):
    """插播音樂"""
    Queue.reverse()
    Temp = list(Playlist(playlist_url))
    Temp.reverse()
    async with playlist_lock:
        Queue.extend(Temp)
    Queue.reverse()
    await ctx.send(f"已插播 {len(playlist_url)} 首音樂")

    
@bot.command()
async def next(ctx):
    """切換下一首"""
    if ctx.voice_client:
        ctx.voice_client.stop() 
        
        if len(Queue) <= 1 :
            await ctx.send(f"當前音樂佇列為空")
        else:
            await ctx.send("已切換下一首⏭️")      
    else:
        await ctx.send("機器人未在播放任何音樂")   
        
@bot.command()
async def pause(ctx):
    """暫停音樂"""
    if ctx.voice_client:
        ctx.voice_client.pause()
        await ctx.send("已暫停播放⏸️")
    else:
        await ctx.send("機器人未在播放任何音樂")
        
@bot.command()       
async def resume(ctx):
    """恢復音樂"""
    if ctx.voice_client:
        ctx.voice_client.resume()
        await ctx.send("已恢復播放▶️")
    else:
        await ctx.send("機器人未在播放任何音樂")


@bot.command()
async def clear(ctx):
    async with playlist_lock:
        if ctx.voice_client.is_playing():
            temp = Queue[0]
            Queue.clear()
            Queue.append(temp)
            print(Queue)
        else:
            Queue.clear()
            print(Queue)

@bot.command()
async def close(ctx):
    """關閉機器人"""
    await leave(ctx)
    await ctx.send("關閉機器人中")
    await bot.close()
    sys.exit()
    

try:
    token = os.getenv("TOKEN") or ""
    if token == "":
        raise Exception("Please add your token to the Secrets pane.")
    keep_alive()
    bot.run(token)
except discord.HTTPException as e:
    if e.status == 429:
        print(
            "The Discord servers denied the connection for making too many requests"
        )
        print(
            "Get help from https://stackoverflow.com/questions/66724687/in-discord-py-how-to-solve-the-error-for-toomanyrequests"
        )
    else:
        raise e