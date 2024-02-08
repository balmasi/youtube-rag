import os
from typing import List

from googleapiclient.discovery import build
from langchain_community.document_loaders import YoutubeLoader
from langchain_core.documents import Document
from dagster import AssetExecutionContext, asset

from youtube_persona.indexing.embed import embed_openai
from youtube_persona.indexing.utils import _split_text
from youtube_persona.indexing.resources import PineconeResource

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
OPENAI_KEY = os.getenv('OPENAI_KEY')
USER_HANDLE = '@show-me-the-data'

@asset
def video_ids(context: AssetExecutionContext) -> List[str]:
    """
    Retrieves the video IDs from a specified YouTube channel using the YouTube Data API.
    
    Args:
        context (AssetExecutionContext): The context for the asset execution.

    Returns:
        dict: A dictionary containing the retrieved video IDs.
    """
    youtube_api = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    # Get the Uploads playlist ID
    channel_response = youtube_api.channels().list(forHandle=USER_HANDLE, part='id').execute()
    context.log.info(channel_response)
    
    if not channel_response['items']:
        context.log.error(f"No channel found for user handle: {USER_HANDLE}")
        return {"video_ids": []}
    
    context.log.info(f"Channel Response: {channel_response}")

    channel_id = channel_response['items'][0]['id']
    playlist_id = youtube_api.channels().list(id=channel_id, part='contentDetails').execute()['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    videos = []
    next_page_token = None

    context.log.info(f'Fetching video IDs for user {USER_HANDLE}')
    
    # Retrieve all videos from the playlist
    while True:
        res = youtube_api.playlistItems().list(playlistId=playlist_id,
                                           part='snippet',
                                           maxResults=50,
                                           pageToken=next_page_token).execute()
        videos += res['items']
        next_page_token = res.get('nextPageToken')

        if next_page_token is None:
            break

    # Extract the video IDs
    return [video['snippet']['resourceId']['videoId'] for video in videos]

def _get_index_id_from_video_id(video_id: str, chunk_index=0):
  return f'{video_id}#chunk{chunk_index}'

@asset
def transcripts(
    context: AssetExecutionContext,
    pinecone_resource: PineconeResource,
    video_ids: List[str]) -> List[Document]:
    """
    Fetches transcripts for a list of YouTube video IDs.
    
    Args:
        context (AssetExecutionContext): The execution context.
        pinecone_resource (PineconeResource): The Pinecone resource for vector indexing.
        video_ids (List[str]): A list of YouTube video IDs.
    """
    video_transcripts = []
    
    for video_id in video_ids: 
        pinecone_id = _get_index_id_from_video_id(video_id)
        if not pinecone_resource.is_document_already_indexed(
            pinecone_id,
            namespace=USER_HANDLE
        ):
            context.log.info(f'Document with id {pinecone_id} not yet indexed. Fetching transcript for video {video_id}')
            loader = YoutubeLoader.from_youtube_url(
                f"https://www.youtube.com/watch?v={video_id}",
                add_video_info=True,
                language=["en"]
            )
            docs = loader.load()
            video_transcripts.append(docs[0])
        else:
            context.log.info(f'Video {video_id} already indexed as document with id {pinecone_id}')

    # Track which videos were newly indexed
    context.add_output_metadata({
        "newly_indexed_videos": list(map(lambda video: video.metadata['source'], video_transcripts))
    })

    return video_transcripts


@asset
def index_transcripts(
    context: AssetExecutionContext,
    pinecone_resource: PineconeResource,
    transcripts: List[Document]
):
    """Index the transcripts.

    Args:
        context (AssetExecutionContext): The execution context.
        pinecone_resource (PineconeResource): The Pinecone resource for vector indexing.
        transcripts (List[Document]): The list of transcripts to be indexed.
    """
    context.log.info('There are {} transcripts to index'.format(len(transcripts)))
    
    for transcript in transcripts:
        context.log.info(f'Splitting video {transcript.metadata["source"]}')
        # Split the transcript into chunks
        doc_chunks = _split_text(transcript)
        
        context.log.info(f'There are {len(doc_chunks)} document chunks for video {transcript.metadata["source"]}')
        
        # Create vectors to insert into the Pinecone index
        vectors_to_insert = [{
            "id": _get_index_id_from_video_id(c.metadata['source'], chunk_index=i),
            "values": embed_openai(c.page_content),
            "metadata": {
                **c.metadata,
                'text': c.page_content
            }
        } for i, c in enumerate(doc_chunks)]
        
        # Upsert the vectors into the Pinecone index
        pinecone_resource.upsert(vectors=vectors_to_insert, namespace=USER_HANDLE)


    
   

    