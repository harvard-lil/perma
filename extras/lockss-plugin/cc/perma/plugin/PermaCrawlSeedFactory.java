package cc.perma.plugin;

import org.lockss.crawler.CrawlSeed;
import org.lockss.crawler.CrawlSeedFactory;
import org.lockss.daemon.Crawler;

public class PermaCrawlSeedFactory implements CrawlSeedFactory {
	@Override
	public CrawlSeed createCrawlSeed(Crawler.CrawlerFacade crawlFacade) {
		return new PermaCrawlSeed(crawlFacade);
	}

}
