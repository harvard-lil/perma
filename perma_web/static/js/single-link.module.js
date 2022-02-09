var resizeTimeout, wrapper;

export var detailsButton = document.getElementById("details-button");
var detailsTray = document.getElementById("collapse-details");

function init () {
  adjustTopMargin();
  var clicked = false;
  if (detailsButton) {
    detailsButton.onclick = function () {
      clicked = !clicked;
      handleShowDetails(clicked);
    };
  }

  window.onresize = function(){
    if (resizeTimeout != null)
      clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(adjustTopMargin, 200);
  };

  const downloadButton = document.getElementById("download-interstitial");
  if (downloadButton) {
    downloadButton.onclick = async function () {

      // trigger replay in a hidden iframe
      const frame = document.createElement('replay-web-page');
      frame.setAttribute('source', this.dataset.source);
      frame.setAttribute('url', this.dataset.url);
      frame.setAttribute('view', this.dataset.view);
      frame.style = 'display:none';
      this.after(frame);

      // optionally, wait until playback is ready and trigger download in a new tab.
      // useful for forcing download when browser behavior is undesirable,
      // for instance, https://github.com/harvard-lil/perma/issues/2056
      if (this.dataset.wait){

        const waitForPlayback = async () => {
          const maxPauseSeconds = 60
          let tries = maxPauseSeconds * 60;  // we expect a repaint rate of ~60 times a second, per https://developer.mozilla.org/en-US/docs/Web/API/window/requestAnimationFrame
          let elem = null;

          while ( !elem && tries > 0) {
            // sleep efficiently until the next repaint
            const pause = await new Promise(resolve => requestAnimationFrame(resolve));
            cancelAnimationFrame(pause);
            // look for the played-back target
            try {
              elem = frame.shadowRoot.querySelector('iframe').contentDocument.querySelector('replay-app-main').shadowRoot.querySelector('wr-coll').shadowRoot.querySelector('wr-coll-replay').shadowRoot.querySelector('iframe')
            } catch (err) {
              if (! err.message.includes('is null')) {
                throw err;
              }
              tries -= 1
            }
          }

          if (elem) {
            return elem.src;
          }
          throw 'Playback timed out'
        };

        // inject a download link and click it
        const download = document.createElement('a');
        download.href = await waitForPlayback();
        download.target = '_blank'
        download.click()
      }
    }
  }
}

export function handleShowDetails (open) {
  detailsButton.textContent = open ? "Hide record details":"Show record details";
  detailsTray.style.display = open ? "block" : "none";
}

function adjustTopMargin () {
  let wrapper = document.getElementsByClassName("capture-wrapper")[0];
  let header = document.getElementsByTagName('header')[0];
  if (!wrapper) return;
  wrapper.style.marginTop = `${header.offsetHeight}px`;
  wrapper.style.height = `calc(100% - ${header.offsetHeight}px)`;
}

init();
