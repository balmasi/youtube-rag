import itertools

from langchain.text_splitter import RecursiveCharacterTextSplitter

def _chunker(iterable, batch_size=50):
    """A helper function to break an iterable into chunks of size batch_size."""
    it = iter(iterable)
    chunk = tuple(itertools.islice(it, batch_size))
    while chunk:
        yield chunk
        chunk = tuple(itertools.islice(it, batch_size))


def _split_text(doc):
    # create recursive text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1024,
        chunk_overlap=20,
        add_start_index=True
    )

    doc_chunks = text_splitter.split_documents([doc])
    return doc_chunks