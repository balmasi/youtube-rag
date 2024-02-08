# Youtube Persona RAG example

This project shows how you can create a chatbot that understands all the contents of a given youtube creator's channel.

It consists of 2 modules:
1.  **Indexing:** The transcripts for the Youtube videos for the channel are indexed into a Pinecone (serverless) vector database
2. **Serving:** Langchain is used to serve a basic chat endpoint where the history is handled by the client rather than the server.

## Getting started

You will need [poetry](https://python-poetry.org/docs/) to install the requirements.

```bash
poetry install
```

You will also need to set the following Environment Variables, which you can provide in a .env file at the root of the project

```bash
# Youtube user handle you're interested in (only @ style supported)
YOUTUBE_USER_HANDLE='@show-me-the-data'

# Youtube Data API key
YOUTUBE_API_KEY='...'
OPENAI_KEY='sk-...'
PINECONE_API_KEY='...'

# Optional LangSmith API key for observability
LANGCHAIN_API_KEY='...'
LANGCHAIN_TRACING_V2='true'
LANGCHAIN_PROJECT='Youtube Persona - Show Me The Data'
LANGCHAIN_ENDPOINT='https://api.smith.langchain.com'
```



### Indexing jobs
[Dagster](https://dagster.io/) is used as the orchestration framework for the indexing job. 

To start the dagster web server and trigger the jobs using the UI, run the following command

```bash
poetry run dagster dev -m src.youtube_persona.indexing
```
Open http://localhost:3000 with your browser to see the Dagster project.

You can materialize the assets to index (only) new videos.

You can define a cron schedule in `src/youtube_persona/indexing/__init__.py`.

If you want to enable Dagster [Schedules](https://docs.dagster.io/concepts/partitions-schedules-sensors/schedules) or [Sensors](https://docs.dagster.io/concepts/partitions-schedules-sensors/sensors) for your jobs, the [Dagster Daemon](https://docs.dagster.io/deployment/dagster-daemon) process must be running. This is done automatically when you run `dagster dev`.

Once your Dagster Daemon is running, you can start turning on schedules and sensors for your jobs.

Alternatively, you can run the job directly using the following command:

```bash
poetry run dagster job execute -j refresh_videos_job -f src/youtube_persona/indexing/__init__.py
```

If you just want to get this up and running in the cloud for demo purposes, I recommend using the [Render cron service](https://docs.render.com/cronjobs) for about $1 per month or stand up a free instance if you want the UI.

### Serving Endpoint

This project uses LangServe to expose a `/chat` endpoint.