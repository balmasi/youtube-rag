from dagster import (
    AssetSelection,
    Definitions,
    define_asset_job,
    load_assets_from_modules,
    ScheduleDefinition,
    EnvVar
)

from youtube_persona.indexing import assets
from youtube_persona.indexing.resources import PineconeResource
import os


all_assets = load_assets_from_modules([assets])


refresh_videos_job = define_asset_job("refresh_videos_job", selection=AssetSelection.all())

# Addition: a ScheduleDefinition the job it should run and a cron schedule of how frequently to run it
refresh_videos_schedule = ScheduleDefinition(
    job=refresh_videos_job,
    cron_schedule="0 * * * *",  # every hour
)

defs = Definitions(
    assets=all_assets,
    schedules=[refresh_videos_schedule],
    jobs=[refresh_videos_job],
    resources={
        'pinecone_resource': PineconeResource(
            api_key=EnvVar('PINECONE_API_KEY'),
            index_name='youtube-videos'
        )
    }
)
