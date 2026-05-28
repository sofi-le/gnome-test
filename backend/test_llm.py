import asyncio, os, openai
from dotenv import load_dotenv
load_dotenv()
async def run():
    client = openai.AsyncOpenAI(api_key=os.environ["NEBIUS_API_KEY"], base_url=os.environ["NEBIUS_BASE_URL"])
    models = await client.models.list()
    print([m.id for m in models.data])
asyncio.run(run())
