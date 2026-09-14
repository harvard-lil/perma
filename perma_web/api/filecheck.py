"""Upload scanning with compatibility for legacy Filecheck responses."""
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
    if 'verdict' in result:
        verdict = result['verdict']
        if verdict in ('clean', 'unsafe', 'rejected', 'unavailable'):
            return verdict, reason
        return 'unavailable', 'Unknown Filecheck verdict'

    # Older development images and service versions only return safe/reason.
    if result.get('safe') is True:
        return 'clean', reason
    if result.get('safe') is False and isinstance(result.get('reason'), str):
        if reason in ('clamav not running', 'clamav out of date') or reason.startswith('Communication with filecheck API failed'):
            return 'unavailable', reason
        return 'unsafe', reason
    return 'unavailable', 'Invalid Filecheck response'
