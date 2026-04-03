import asyncio 
from telethon import TelegramClient 
from telethon .sessions import StringSession 

API_ID =input ("API_ID: ").strip ()
API_HASH =input ("API_HASH: ").strip ()
PHONE =input ("Phone (+9665xxxxxxxx): ").strip ()

async def main ():
    client =TelegramClient (StringSession (),int (API_ID ),API_HASH )
    await client .start (phone =PHONE )
    session_string =client .session .save ()
    print ("\n"+"="*60 )
    print ("SESSION_STRING (انسخ هذا كاملاً):")
    print ("="*60 )
    print (session_string )
    print ("="*60 )
    await client .disconnect ()

asyncio .run (main ())
