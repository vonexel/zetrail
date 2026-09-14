from hashlib import sha256


_SEPARATOR = "\x1f"


def stable_id(*parts: str) -> str:
    payload = _SEPARATOR.join(parts).encode("utf-8")
    return sha256(payload).hexdigest()

def document_version_id(library_id: int, item_key: str, attachment_key: str, file_sha256: str) -> str:
    return stable_id(str(library_id), item_key, attachment_key, file_sha256)

def chunk_id(document_version: str, chunker_name: str, chunker_config_hash: str, chunk_index: int) -> str:
    return stable_id(document_version, chunker_name, chunker_config_hash, str(chunk_index))