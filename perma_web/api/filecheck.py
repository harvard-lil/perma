"""Upload scanning using Filecheck verdicts."""
import requests


def scan_upload(uploaded_file, url, timeout):
    """Return (verdict, reason); unavailable scans intentionally fail open."""
    uploaded_file.file.seek(0)
    try:
        response = requests.post(
            url,
            files={'file': (uploaded_file.name, uploaded_file.file)},
            timeout=timeout,
        )
        response.raise_for_status()
        result = response.json()
    except requests.RequestException as error:
        return 'unavailable', f'Communication with filecheck API failed: {error}'
    finally:
        uploaded_file.file.seek(0)

    if not isinstance(result, dict):
        return 'unavailable', 'Invalid Filecheck response'
    reason = result.get('reason')
    if not isinstance(reason, str):
        reason = 'No reason provided'
    verdict = result.get('verdict')
    if verdict in ('clean', 'unsafe', 'rejected', 'unavailable'):
        return verdict, reason
    return 'unavailable', 'Missing or unknown Filecheck verdict'
