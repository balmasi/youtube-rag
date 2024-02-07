import os
from dagster import ConfigurableResource, InitResourceContext
from pinecone import Pinecone
from pydantic import PrivateAttr

class PineconeResource(ConfigurableResource):
    api_key: str
    index_name: str

    _index: Pinecone.Index = PrivateAttr()

    def setup_for_execution(self, context) -> None:
        client = Pinecone(api_key=self.api_key)
        self._index= client.Index(self.index_name)
    
    def is_document_already_indexed(self, id: str, namespace=None):
        results = self._index.fetch(
            ids=[id],
            namespace=namespace
        )
        return len(results['vectors']) > 0

    def upsert(self, vectors, namespace=None):
        return self._index.upsert(vectors=vectors, namespace=namespace)