from warcio.statusandheaders import StatusAndHeaders
from warcio.statusandheaders import StatusAndHeadersParser
from warcio.statusandheaders import StatusAndHeadersParserException

from warcio.limitreader import LimitReader

from warcio.bufferedreaders import BufferedReader, ChunkedDataReader

from warcio.timeutils import timestamp_to_iso_date

from six.moves import zip

# BEGIN PERMA CUSTOMIZATION
import logging
logger = logging.getLogger(__name__)
# END PERMA CUSTOMIZATION

#=================================================================
class ArcWarcRecord(object):
    def __init__(self, *args):
        (self.format, self.rec_type, self.rec_headers, self.raw_stream,
         self.http_headers, self.content_type, self.length) = args
        self.payload_length = -1

    def content_stream(self):
        if not self.http_headers:
            return self.raw_stream

        encoding = self.http_headers.get_header('content-encoding')

        if encoding:
            encoding = encoding.lower()

            if encoding not in BufferedReader.get_supported_decompressors():
                encoding = None

        if self.http_headers.get_header('transfer-encoding') == 'chunked':
            return ChunkedDataReader(self.raw_stream, decomp_type=encoding)
        elif encoding:
            return BufferedReader(self.raw_stream, decomp_type=encoding)
        else:
            return self.raw_stream


#=================================================================
class ArchiveLoadFailed(Exception):
    def __init__(self, reason):
        self.msg = str(reason)
        super(ArchiveLoadFailed, self).__init__(self.msg)


#=================================================================
class ArcWarcRecordLoader(object):
    WARC_TYPES = ['WARC/1.1', 'WARC/1.0', 'WARC/0.17', 'WARC/0.18']

    HTTP_TYPES = ['HTTP/1.0', 'HTTP/1.1']

    HTTP_VERBS = ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'TRACE',
                  'OPTIONS', 'CONNECT', 'PATCH']

    HTTP_RECORDS = ('response', 'request', 'revisit')

    NON_HTTP_SCHEMES = ('dns:', 'whois:', 'ntp:')
    HTTP_SCHEMES = ('http:', 'https:')

    def __init__(self, verify_http=True, arc2warc=True):
        if arc2warc:
            self.arc_parser = ARC2WARCHeadersParser()
        else:
            self.arc_parser = ARCHeadersParser()

        self.warc_parser = StatusAndHeadersParser(self.WARC_TYPES)
        self.http_parser = StatusAndHeadersParser(self.HTTP_TYPES, verify_http)

        self.http_req_parser = StatusAndHeadersParser(self.HTTP_VERBS, verify_http)

    def parse_record_stream(self, stream,
                            statusline=None,
                            known_format=None,
                            no_record_parse=False,
                            ensure_http_headers=False):
        """ Parse file-like stream and return an ArcWarcRecord
        encapsulating the record headers, http headers (if any),
        and a stream limited to the remainder of the record.

        Pass statusline and known_format to detect_type_loader_headers()
        to faciliate parsing.
        """
        (the_format, rec_headers) = (self.
                                     _detect_type_load_headers(stream,
                                                               statusline,
                                                               known_format))

        if the_format == 'arc':
            uri = rec_headers.get_header('uri')
            length = rec_headers.get_header('length')
            content_type = rec_headers.get_header('content-type')
            sub_len = rec_headers.total_len
            if uri and uri.startswith('filedesc://'):
                rec_type = 'arc_header'
            else:
                rec_type = 'response'

        elif the_format in ('warc', 'arc2warc'):
            rec_type = rec_headers.get_header('WARC-Type')
            uri = self._ensure_target_uri_format(rec_headers)
            length = rec_headers.get_header('Content-Length')
            content_type = rec_headers.get_header('Content-Type')
            if the_format == 'warc':
                sub_len = 0
            else:
                sub_len = rec_headers.total_len
                the_format = 'warc'

        is_err = False

        try:
            if length is not None:
                length = int(length) - sub_len
                if length < 0:
                    is_err = True

        except (ValueError, TypeError):
            is_err = True

        # err condition
        if is_err:
            length = 0

        # limit stream to the length for all valid records
        if length is not None and length >= 0:
            stream = LimitReader.wrap_stream(stream, length)


        http_headers = None

        # load http headers if parsing
        if not no_record_parse:
            http_headers = self.load_http_headers(rec_type, uri, stream, length)

        # generate validate http headers (eg. for replay)
        if not http_headers and ensure_http_headers:
            http_headers = self.default_http_headers(length, content_type)

        return ArcWarcRecord(the_format, rec_type,
                             rec_headers, stream, http_headers,
                             content_type, length)

    def load_http_headers(self, rec_type, uri, stream, length):
        # only if length == 0 don't parse
        # try parsing is length is unknown (length is None) or length > 0
        if length == 0:
            return None

        # only certain record types can have http headers
        if rec_type not in self.HTTP_RECORDS:
            return None

        # only http:/https: uris can have http headers
        if not uri.startswith(self.HTTP_SCHEMES):
            return None

        # request record: parse request
        if rec_type == 'request':
            return self.http_req_parser.parse(stream)

        elif rec_type == 'revisit':
            try:
                return self.http_parser.parse(stream)
            except EOFError:
                # empty revisit with no http headers, is ok!
                return None

        # response record or non-empty revisit: parse HTTP status and headers!
        else:
            return self.http_parser.parse(stream)

    def default_http_headers(self, length, content_type=None):
        headers = []
        if content_type:
            headers.append(('Content-Type', content_type))

        if length is not None and length >= 0:
            headers.append(('Content-Length', str(length)))

        return StatusAndHeaders('200 OK', headers=headers, protocol='HTTP/1.0')

    def _detect_type_load_headers(self, stream,
                                  statusline=None, known_format=None):
        """ If known_format is specified ('warc' or 'arc'),
        parse only as that format.

        Otherwise, try parsing record as WARC, then try parsing as ARC.
        if neither one succeeds, we're out of luck.
        """

        if known_format != 'arc':
            # try as warc first
            try:
                rec_headers = self.warc_parser.parse(stream, statusline)
                return 'warc', rec_headers
            except StatusAndHeadersParserException as se:
                if known_format == 'warc':
                    msg = 'Invalid WARC record, first line: '
                    raise ArchiveLoadFailed(msg + str(se.statusline))

                statusline = se.statusline
                pass

        # now try as arc
        try:
            rec_headers = self.arc_parser.parse(stream, statusline)
            return self.arc_parser.get_rec_type(), rec_headers
        except StatusAndHeadersParserException as se:
            if known_format == 'arc':
                msg = 'Invalid ARC record, first line: '
            else:
                msg = 'Unknown archive format, first line: '
            raise ArchiveLoadFailed(msg + str(se.statusline))

    def _ensure_target_uri_format(self, rec_headers):
        """Checks the value for the WARC-Target-URI header field to see if it starts
        with '<' and ends with '>' (Wget 1.19 bug) and if '<' and '>' are present,
        corrects and updates the field returning the corrected value for the field
        otherwise just returns the fields value.

        :param StatusAndHeaders rec_headers: The parsed WARC headers
        :return: The value for the WARC-Target-URI field
        :rtype: str | None
        """
        uri = rec_headers.get_header('WARC-Target-URI')
        if uri is not None and uri.startswith('<') and uri.endswith('>'):
            uri = uri[1:-1]
            rec_headers.replace_header('WARC-Target-URI', uri)

        # BEGIN PERMA CUSTOMIZATION
        # https://github.com/webrecorder/warcio/blob/c64c4394805e13256695f51af072c95389397ee9/warcio/recordloader.py#L217
        # don't pass WARC-Target-URI with spaces to the cdxline indexers, which don't expect that
        # cause of at least some of the errors in https://github.com/harvard-lil/perma/issues/2605
        if uri is not None and " " in uri:
            logger.warning("Replacing spaces in invalid WARC-Target-URI: {}".format(uri))
            uri = uri.replace(" ", "%20")
            rec_headers.replace_header('WARC-Target-URI', uri)
        # END PERMA CUSTOMIZATION

        return uri


#=================================================================
class ARCHeadersParser(object):
    # ARC 1.0 headers
    ARC_HEADERS = ["uri", "ip-address", "archive-date",
                       "content-type", "length"]

    def __init__(self):
        self.headernames = self.get_header_names()

    def get_rec_type(self):
        return 'arc'

    def parse(self, stream, headerline=None):
        total_read = 0

        if headerline is None:
            headerline = stream.readline()

        headerline = StatusAndHeadersParser.decode_header(headerline)

        header_len = len(headerline)

        if header_len == 0:
            raise EOFError()

        headerline = headerline.rstrip()

        headernames = self.headernames

        # if arc header, consume next two lines
        if headerline.startswith('filedesc://'):
            version = StatusAndHeadersParser.decode_header(stream.readline())  # skip version
            spec = StatusAndHeadersParser.decode_header(stream.readline())  # skip header spec, use preset one
            total_read += len(version)
            total_read += len(spec)

        parts = headerline.split(' ')

        if len(parts) != len(headernames):
            msg = 'Wrong # of headers, expected arc headers {0}, Found {1}'
            msg = msg.format(headernames, parts)
            raise StatusAndHeadersParserException(msg, parts)


        protocol, headers = self._get_protocol_and_headers(headerline, parts)

        return StatusAndHeaders(statusline='',
                                headers=headers,
                                protocol='WARC/1.0',
                                total_len=total_read)

    @classmethod
    def get_header_names(cls):
        return cls.ARC_HEADERS

    def _get_protocol_and_headers(self, headerline, parts):
        headers = []

        for name, value in zip(self.headernames, parts):
            headers.append((name, value))

        return ('ARC/1.0', headers)


#=================================================================
class ARC2WARCHeadersParser(ARCHeadersParser):
    # Headers for converting ARC -> WARC Header
    ARC_TO_WARC_HEADERS = ["WARC-Target-URI",
                           "WARC-IP-Address",
                           "WARC-Date",
                           "Content-Type",
                           "Content-Length"]

    def get_rec_type(self):
        return 'arc2warc'

    @classmethod
    def get_header_names(cls):
        return cls.ARC_TO_WARC_HEADERS

    def _get_protocol_and_headers(self, headerline, parts):
        headers = []

        if headerline.startswith('filedesc://'):
            rec_type = 'warcinfo'
        else:
            rec_type = 'response'
            parts[3] = 'application/http;msgtype=response'

        headers.append(('WARC-Type', rec_type))
        headers.append(('WARC-Record-ID', StatusAndHeadersParser.make_warc_id()))

        for name, value in zip(self.headernames, parts):
            if name == 'WARC-Date':
                value = timestamp_to_iso_date(value)

            if rec_type == 'warcinfo' and name == 'WARC-Target-URI':
                name = 'WARC-Filename'
                value = value[len('filedesc://'):]

            headers.append((name, value))

        return ('WARC/1.0', headers)
