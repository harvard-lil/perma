from pywb import replay, archiveloader, indexreader, query, archivalrouter, wbarchivalurl
import perma.settings


# include guid in CDX requests
class Route(archivalrouter.Route):
    def _addFilters(self, wbrequest, matcher):
        wbrequest.customParams['guid'] = matcher.group(1)


# prevent bare URLs getting forwarded to timestamp version
class RewritingReplayHandler(replay.RewritingReplayHandler):
    def _checkRedir(self, wbrequest, cdx):
        return None


# prevent timestamp and mod getting added to rewritten urls
class ArchivalUrl(wbarchivalurl.ArchivalUrl):
    def to_str(self, **overrides):
        overrides['mod'] = ''
        overrides['timestamp'] = ''
        return wbarchivalurl.ArchivalUrl.to_str(self, **overrides)

    def _init_replay(self, url):
        self.url = url
        self.type = self.LATEST_REPLAY
        return True


def createDefaultWB(headinsert):
    """
        Configure server.
        This is imported by pywb.wbapp
    """
    query_handler = query.QueryHandler(indexreader.RemoteCDXServer(perma.settings.CDX_SERVER_URL))

    resolvers = [replay.PrefixResolver('file://', '')]  # where to look for WARCs -- this assumes absolute file paths returned by CDX server

    replay_handler = RewritingReplayHandler(
        resolvers = resolvers,
        archiveloader = archiveloader.ArchiveLoader()
    )

    return archivalrouter.ArchivalRequestRouter({
        Route(r'([a-zA-Z0-9\-]+)', replay.WBHandler(query_handler, replay_handler))
    }, archivalurl_class=ArchivalUrl)
