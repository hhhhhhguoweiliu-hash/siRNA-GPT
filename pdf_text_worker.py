"""Bounded text-layer extraction in a subprocess; never OCR or PDF authoring."""
import io
import json
import sys


def extract(raw):
    from pypdf import PdfReader, __version__
    import pypdf.filters
    # Bound decoded streams while accommodating normal publisher figure/font streams.
    pypdf.filters.ZLIB_MAX_OUTPUT_LENGTH = 16_000_000
    reader = PdfReader(io.BytesIO(raw), strict=True)
    if reader.is_encrypted:
        raise ValueError('暂不接收加密PDF，请提供未加密的文字版。')
    if not 1 <= len(reader.pages) <= 100:
        raise ValueError('PDF须为1至100页。')
    pages = []
    for i, page in enumerate(reader.pages, 1):
        # Inspect decoded streams without serializing/reparsing all drawing operators.
        content = page.get('/Contents')
        content = content.get_object() if content is not None else None
        streams = [s.get_object() for s in content] if isinstance(content,list) else [content] if content is not None else []
        if sum(len(s.get_data()) for s in streams) > 8_000_000:
            raise ValueError(f'第{i}页内容过大，未导入。')
        value = (page.extract_text() or '').replace('\x00', '').strip()
        if len(value) > 120_000:
            raise ValueError(f'第{i}页文字过多，未导入。')
        pages.append({'page': i, 'text': value})
    if sum(len(p['text']) for p in pages) < 60:
        raise ValueError('未提取到足够文字：可能是扫描版或图片PDF。本版不识别图片文字，请提供文字版PDF或文本。')
    if sum(len(p['text']) for p in pages) > 2_000_000:
        raise ValueError('PDF提取文字超过本版上限，未导入。')
    return {'pages': pages, 'extractor': 'pypdf-' + __version__,
            'scope': 'TEXT_LAYER_ONLY_NO_OCR_NO_FIGURE_READING',
            'pages_without_text': [p['page'] for p in pages if not p['text']]}


if __name__ == '__main__':
    try:
        if sys.platform != 'win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS, (256*1024*1024, 256*1024*1024))
            resource.setrlimit(resource.RLIMIT_CPU, (18, 18))
        raw = sys.stdin.buffer.read(8_000_001)
        if len(raw) > 8_000_000:
            raise ValueError('PDF不能超过8MB。')
        result = extract(raw)
        sys.stdout.buffer.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
    except Exception as e:
        sys.stdout.buffer.write(json.dumps({'error': str(e) or type(e).__name__}, ensure_ascii=False).encode('utf-8'))
        sys.exit(1)
