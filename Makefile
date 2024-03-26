install:
	@poetry install --no-root

dagster-ui:
	@poetry run dagster dev -m src.indexing

index-videos:
	@poetry run dagster job execute -j refresh_videos_job -m src.indexing

serve:
	@poetry run python -m src.serving.serve