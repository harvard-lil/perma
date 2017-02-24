package cc.perma.plugin;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.lang.Integer;
import java.net.URL;
import java.util.ArrayList;
import java.util.Collection;

import org.lockss.config.Configuration;
import org.lockss.crawler.BaseCrawlSeed;
import org.lockss.daemon.ConfigParamDescr;
import org.lockss.daemon.Crawler.CrawlerFacade;
import org.lockss.daemon.PluginException;
import org.lockss.plugin.ArchivalUnit;
import org.lockss.plugin.ArchivalUnit.ConfigurationException;
import org.lockss.plugin.AuUtil;


public class PermaCrawlSeed extends BaseCrawlSeed {

  protected Collection<String> urls;
  protected String baseUrl;
  protected Integer year;
  protected Integer month;

  public PermaCrawlSeed(CrawlerFacade cf) {
    super(cf);
  }

  @Override
  protected void initialize()
          throws PluginException, ConfigurationException, IOException {
    super.initialize();

    // get configuration
    Configuration config = au.getConfiguration();
    this.baseUrl = config.get(ConfigParamDescr.BASE_URL.getKey());
    try{
      this.year = config.getInt(ConfigParamDescr.YEAR.getKey());
    } catch (Configuration.InvalidParam e) {
      throw new ConfigurationException("Year must be an integer", e);
    }
    try{
      this.month = config.getInt("month");
    } catch (Configuration.InvalidParam e) {
      throw new ConfigurationException("Month must be an integer", e);
    }
  }
  
  @Override
  public Collection<String> doGetStartUrls() 
      throws ConfigurationException, PluginException, IOException{

    if(urls == null){
      urls = new ArrayList<String>();
      Integer offset = 0;
      long startDate = AuUtil.getAuState(au).getLastCrawlTime();
      if(startDate>0)
        startDate = startDate/1000 - 24*60*60; // convert to seconds from milliseconds, and subtract one day

      while(true){
        URL url = new URL(String.format("%slockss/search/?offset=%s&creation_month=%s&creation_year=%s&updates_since=%s", baseUrl, offset, month, year, startDate));
        InputStream is = url.openStream();
        BufferedReader reader = new BufferedReader(new InputStreamReader(is));
        String targetUrl;

        final ArrayList<String> partial = new ArrayList<String>();
        try {
          while ((targetUrl = reader.readLine()) != null) {
            partial.add(String.format("%slockss/fetch/%s", baseUrl, targetUrl));
          }
        } finally {
          is.close();
        }
        if(partial.size()>0){
          urls.addAll(partial);
          offset += 1000;
        }else{
          break;
        }
      }
    }

    return urls;
  }


  /**
   * All URLs are start urls so don't fail on error
   * @return false
   */
  @Override
  public boolean isFailOnStartUrlError() {
    return false;
  }


}
