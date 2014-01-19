# monkeypatch to stop stuff getting added to our urls
# this will be unnecessary if pywb adds a way to specify a custom ArchivalUrl class
from pywb import wbarchivalurl
_real_archivalurl_to_str = wbarchivalurl.ArchivalUrl.to_str
def archivalurl_to_str(atype, mod, timestamp, url):
    return _real_archivalurl_to_str(atype, '', '', url)
wbarchivalurl.ArchivalUrl.to_str = staticmethod(archivalurl_to_str)

# imports
from pywb import replay, archiveloader, indexreader, query, archivalrouter
import perma.settings

# include guid in CDX requests
class MatchRegex(archivalrouter.MatchRegex):
    def _addFilters(self, wbrequest, matcher):
        wbrequest.customParams['guid'] = matcher.group(2)

# prevent bare URLs getting forwarded to timestamp version
class RewritingReplayHandler(replay.RewritingReplayHandler):
    def _checkRedir(self, wbrequest, cdx):
        return None


def createDefaultWB(headinsert):
    """
        Configure server.
        This is imported by pywb.wbapp
    """
    query_handler = query.QueryHandler(indexreader.RemoteCDXServer(perma.settings.CDX_SERVER_URL))

    resolvers = [replay.PrefixResolver('file://', '')]  # where to look for WARCs -- this assumes absolute file paths returned by CDX server

    replay_handler = RewritingReplayHandler(
        resolvers = resolvers,
        archiveloader = archiveloader.ArchiveLoader(),
        headInsert = ""
    )

    return archivalrouter.ArchivalRequestRouter({
            MatchRegex(r'(warc)/([a-zA-Z0-9\-]+)', replay.WBHandler(query_handler, replay_handler))
        })