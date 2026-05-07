from app.services.chunk_service import build_page_chunks, split_text_into_chunks


def test_split_text_into_chunks_keeps_chunk_sizes_reasonable() -> None:
    text = "문장 하나입니다. " * 80

    chunks = split_text_into_chunks(text)

    assert chunks
    for chunk in chunks[:-1]:
        assert 600 <= len(chunk) <= 1000
    assert len(chunks[-1]) <= 1000


def test_build_page_chunks_keeps_page_number() -> None:
    pages = [{"page": 2, "text": "문장 하나입니다. " * 80}]

    chunk_rows = build_page_chunks(pages)

    assert chunk_rows
    assert all(row["page_number"] == 2 for row in chunk_rows)
    assert all(row["content"] for row in chunk_rows)
