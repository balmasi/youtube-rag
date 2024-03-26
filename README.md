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
make dagster-ui
```
Open http://localhost:3000 with your browser to see the Dagster project.

You can materialize the assets to index (only) new videos.

You can define a cron schedule in `src/index/__init__.py`.

If you want to enable Dagster [Schedules](https://docs.dagster.io/concepts/partitions-schedules-sensors/schedules) or [Sensors](https://docs.dagster.io/concepts/partitions-schedules-sensors/sensors) for your jobs, the [Dagster Daemon](https://docs.dagster.io/deployment/dagster-daemon) process must be running. This is done automatically when you run `dagster dev`.

Once your Dagster Daemon is running, you can start turning on schedules and sensors for your jobs.


Alternatively, you can run the job directly using the following command:

```bash
make index-videos
```

If you just want to get this up and running in the cloud for demo purposes, I recommend using the [Render cron service](https://docs.render.com/cronjobs) for free or stand up a free instance if you want the UI.

#### Environment Variables Required
This service requires the following environment variables to be set:

```
YOUTUBE_USER_HANDLE
YOUTUBE_API_KEY
OPENAI_KEY
PINECONE_API_KEY
```

### Serving Endpoint

This project uses LangServe to expose a `/chat/invoke` endpoint on port 8000 (by default).

To run the server, execute the following command
```bash
make serve
```

#### Example 1: Basic Request
##### Request:
```bash
curl --location 'http://127.0.0.1:8000/chat/invoke' \
--header 'Content-Type: application/json' \
--data '{
    "input": {
        "question": "How can I deploy a GPT to my website?"
    }
}'
```

##### Response:
```json
{
    "output": "You can deploy a GPT to your website using a chatbot building platform like Botpress. It allows you to host and integrate GPTs on various platforms, including websites, WhatsApp, and Telegram.",
    "callback_events": [],
    "metadata": {
        "run_id": "67af8e5e-b9cc-4602-8e92-eed89be2ca41"
    }
}
```

#### Example 2: Request with chat history
Chat history is managed by the client to minimize server resources (this is a demo project) This way, the client can choose how much context to provide. To provide history, simply pass in a text representation of the conversation so far into the request in the *optional* `chat_history` key.

##### Request
```bash
curl --location 'https://c6f8-174-95-171-152.ngrok-free.app/chat/invoke' \
--header 'Content-Type: application/json' \
--data '{
    "input": {
        "question": "How can I deploy one to my website?",
        "chat_history": "user: what does GPT stand for?\nbot: GPT stands for Generative Pre-trained Transformer."
    }
}'
```

##### Response
```json
{
    "output": "To deploy a GPT on your website, you can use the Botpress platform. It allows you to create chat experiences and embed a chat widget on a regular HTML page. You can follow the integration steps provided by Botpress and use the preconfigured embed code to add the chat widget to your HTML page.",
    "callback_events": [],
    "metadata": {
        "run_id": "1321f1c5-eb46-4d3e-94b2-ea7306f19998"
    }
}
```

#### Deploying the service
To deploy this to a lightweight hosting environment for testing purposes, you can use Render's free [Web Service](https://docs.render.com/web-services).

Keep in mind that Free instances spin down after periods of inactivity. They do not support SSH access, scaling, one-off jobs, or persistent disks.

For this service, you will need the following Environment Variables:
```
YOUTUBE_USER_HANDLE
OPENAI_KEY
PINECONE_API_KEY
# Optional
LANGCHAIN_API_KEY
LANGCHAIN_TRACING_V2
LANGCHAIN_PROJECT
LANGCHAIN_ENDPOINT
```