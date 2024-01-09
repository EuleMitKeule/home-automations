from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler: AsyncIOScheduler = AsyncIOScheduler()
scheduler.start()
