'use strict';

// Modal functionality
// Variables for modal elements
const modal = document.querySelector('[data-modal]');
const modalCloseBtn = document.querySelector('[data-modal-close]');
const modalCloseOverlay = document.querySelector('[data-modal-overlay]');

// Close modal function
if (modal && modalCloseBtn && modalCloseOverlay) {
  const modalCloseFunc = function () {
    modal.classList.add('closed'); // Add 'closed' class to hide modal
  };

  // Event listeners to close the modal
  modalCloseOverlay.addEventListener('click', modalCloseFunc);
  modalCloseBtn.addEventListener('click', modalCloseFunc);
}

// Notification toast functionality
// Variables for notification toast elements
const notificationToast = document.querySelector('[data-toast]');
const toastCloseBtn = document.querySelector('[data-toast-close]');

// Close notification toast
if (notificationToast && toastCloseBtn) {
  toastCloseBtn.addEventListener('click', function () {
    notificationToast.classList.add('closed'); // Add 'closed' class to hide toast
  });
}

// Mobile menu functionality
// Variables for mobile menu elements
const mobileMenuOpenBtn = document.querySelectorAll('[data-mobile-menu-open-btn]');
const mobileMenu = document.querySelectorAll('[data-mobile-menu]');
const mobileMenuCloseBtn = document.querySelectorAll('[data-mobile-menu-close-btn]');
const overlay = document.querySelector('[data-overlay]');

// Handle multiple mobile menus
if (mobileMenuOpenBtn && mobileMenu && mobileMenuCloseBtn && overlay) {
  for (let i = 0; i < mobileMenuOpenBtn.length; i++) {
    // Function to close mobile menu and overlay
    const mobileMenuCloseFunc = function () {
      mobileMenu[i].classList.remove('active'); // Remove 'active' class from menu
      overlay.classList.remove('active'); // Remove 'active' class from overlay
    };

    // Open mobile menu and activate overlay
    mobileMenuOpenBtn[i].addEventListener('click', function () {
      mobileMenu[i].classList.add('active'); // Add 'active' class to menu
      overlay.classList.add('active'); // Add 'active' class to overlay
    });

    // Close mobile menu and deactivate overlay
    mobileMenuCloseBtn[i].addEventListener('click', mobileMenuCloseFunc);
    overlay.addEventListener('click', mobileMenuCloseFunc);
  }
}

const mobileMenuOpenBtnAi = document.querySelectorAll('[data-mobile-menu-open-btn-Ai]');
const mobileMenuAi = document.querySelectorAll('[data-mobile-menu-Ai]');
const mobileMenuCloseBtnAi = document.querySelectorAll('[data-mobile-menu-close-btn-Ai]');
const overlayAi = document.querySelector('[data-overlay]');

// Handle multiple mobile menus
if (mobileMenuOpenBtnAi && mobileMenuAi && mobileMenuCloseBtnAi && overlayAi) {
  for (let i = 0; i < mobileMenuOpenBtnAi.length; i++) {
    // Function to close mobile menu and overlay
    const mobileMenuCloseFunc = function () {
      mobileMenuAi[i].classList.remove('active'); // Remove 'active' class from menu
      overlayAi.classList.remove('active'); // Remove 'active' class from overlay
    };

    // Open mobile menu and activate overlay
    mobileMenuOpenBtnAi[i].addEventListener('click', function () {
      mobileMenuAi[i].classList.add('active'); // Add 'active' class to menu
      overlayAi.classList.add('active'); // Add 'active' class to overlay
    });

    // Close mobile menu and deactivate overlay
    mobileMenuCloseBtnAi[i].addEventListener('click', mobileMenuCloseFunc);
    overlayAi.addEventListener('click', mobileMenuCloseFunc);
  }
}

const laptopMenuOpenBtnAi = document.querySelectorAll('[data-laptop-menu-open-btn-Ai]');
const laptopMenuAi = document.querySelectorAll('[data-mobile-menu-Ai]');
const laptopMenuCloseBtnAi = document.querySelectorAll('[data-mobile-menu-close-btn-Ai]');
const laptopOverlayAi = document.querySelector('[data-overlay]');

// Handle multiple mobile menus
if (laptopMenuOpenBtnAi && laptopMenuAi && laptopMenuCloseBtnAi && laptopOverlayAi) {
  for (let i = 0; i < laptopMenuOpenBtnAi.length; i++) {
    // Function to close mobile menu and overlay
    const mobileMenuCloseFunc = function () {
      laptopMenuAi[i].classList.remove('active'); // Remove 'active' class from menu
      laptopOverlayAi.classList.remove('active'); // Remove 'active' class from overlay
    };

    // Open mobile menu and activate overlay
    laptopMenuOpenBtnAi[i].addEventListener('click', function () {
      laptopMenuAi[i].classList.add('active'); // Add 'active' class to menu
      laptopOverlayAi.classList.add('active'); // Add 'active' class to overlay
    });

    // Close mobile menu and deactivate overlay
    laptopMenuCloseBtnAi[i].addEventListener('click', mobileMenuCloseFunc);
    laptopOverlayAi.addEventListener('click', mobileMenuCloseFunc);
  }
}
// Accordion functionality
// Variables for accordion elements
const accordionBtn = document.querySelectorAll('[data-accordion-btn]');
const accordion = document.querySelectorAll('[data-accordion]');

// Handle accordion toggle
if (accordionBtn && accordion) {
  for (let i = 0; i < accordionBtn.length; i++) {
    accordionBtn[i].addEventListener('click', function () {
      const clickedBtn = this.nextElementSibling.classList.contains('active'); // Check if clicked accordion is active

      // Close all accordions if another is clicked
      for (let i = 0; i < accordion.length; i++) {
        if (clickedBtn) break;
        if (accordion[i].classList.contains('active')) {
          accordion[i].classList.remove('active'); // Remove 'active' class from accordion content
          accordionBtn[i].classList.remove('active'); // Remove 'active' class from accordion button
        }
      }

      // Toggle the 'active' class for the clicked accordion
      this.nextElementSibling.classList.toggle('active');
      this.classList.toggle('active');
    });
  }
}

// Remove default 'title' attribute from all ion-icons
document.querySelectorAll('ion-icon').forEach((icon) => {
  icon.removeAttribute('title'); // Remove default title attribute to prevent browser tooltips
});

const mainFeatureForm = document.getElementById('main-feature-form');
const mainFeatureStatus = document.getElementById('main-feature-status');
const mainFeatureResult = document.getElementById('main-feature-result');

if (mainFeatureForm && mainFeatureStatus && mainFeatureResult) {
  const storageKey = 'smart_outfit_saved_looks_v1';
  let latestRecommendation = null;

  const featureMeta = document.getElementById('feature-meta');
  const weatherList = document.getElementById('feature-weather-list');
  const styleList = document.getElementById('feature-style-list');
  const pairingList = document.getElementById('feature-pairing-list');
  const galleryGrid = document.getElementById('feature-gallery-grid');
  const inspirationSection = document.getElementById('feature-inspiration-section');
  const inspirationGrid = document.getElementById('feature-inspiration-grid');
  const tryOnNote = document.getElementById('feature-tryon-note');
  const mannequinImage = document.getElementById('feature-mannequin-image');
  const overlayWrap = document.getElementById('feature-overlay-wrap');
  const overlayImage = document.getElementById('feature-overlay-image');
  const submitBtn = document.getElementById('feature-submit-btn');
  const saveBtn = document.getElementById('feature-save-btn');
  const exportBtn = document.getElementById('feature-export-btn');
  const presentationBtn = document.getElementById('feature-presentation-btn');
  const savedList = document.getElementById('feature-saved-list');

  const renderList = function (element, items) {
    element.innerHTML = '';
    (items || []).forEach((item) => {
      const listItem = document.createElement('li');
      listItem.textContent = item;
      element.appendChild(listItem);
    });
  };

  const formatCurrency = function (usd, ngn) {
    const usdValue = typeof usd === 'number' ? usd.toFixed(2) : '0.00';
    const ngnValue = typeof ngn === 'number' ? ngn.toLocaleString() : '0';
    return `$${usdValue} / NGN ${ngnValue}`;
  };

  const renderGalleryCards = function (cards) {
    if (!galleryGrid) return;
    galleryGrid.innerHTML = '';
    (cards || []).forEach((item) => {
      const card = document.createElement('article');
      card.className = 'smart-piece-card';
      card.innerHTML = `
        <div class="smart-piece-image-wrap">
          <img src="${item.image}" alt="${item.title}" class="smart-piece-image">
          <div class="smart-piece-overlay"></div>
        </div>
        <div class="smart-piece-body">
          <p class="smart-piece-tag">${item.tag || 'Style Pick'}</p>
          <h5>${item.title}</h5>
          <p class="smart-piece-price">${formatCurrency(item.price_usd, item.price_ngn)}</p>
        </div>
      `;
      galleryGrid.appendChild(card);
    });
  };

  const renderInspirationCards = function (photos) {
    if (!inspirationGrid || !inspirationSection) return;
    inspirationGrid.innerHTML = '';

    if (!photos || photos.length === 0) {
      inspirationSection.style.display = 'none';
      return;
    }

    inspirationSection.style.display = 'block';
    photos.forEach((photo) => {
      const card = document.createElement('article');
      card.className = 'smart-inspiration-card';
      card.innerHTML = `
        <img src="${photo.image}" alt="${photo.title}">
        <p>${photo.title || 'Outfit inspiration'}</p>
      `;
      inspirationGrid.appendChild(card);
    });
  };

  const drawWrappedText = function (ctx, text, x, y, maxWidth, lineHeight) {
    const words = String(text || '').split(' ');
    let line = '';
    let currentY = y;

    words.forEach((word) => {
      const testLine = line ? `${line} ${word}` : word;
      if (ctx.measureText(testLine).width > maxWidth && line) {
        ctx.fillText(line, x, currentY);
        currentY += lineHeight;
        line = word;
      } else {
        line = testLine;
      }
    });

    if (line) {
      ctx.fillText(line, x, currentY);
      currentY += lineHeight;
    }

    return currentY;
  };

  const exportPresentationCard = function (payload) {
    const canvas = document.createElement('canvas');
    canvas.width = 1600;
    canvas.height = 900;
    const ctx = canvas.getContext('2d');

    const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
    gradient.addColorStop(0, '#0f172a');
    gradient.addColorStop(0.45, '#1f2937');
    gradient.addColorStop(1, '#0f766e');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = '#f8fafc';
    ctx.font = '700 56px Trebuchet MS';
    ctx.fillText('Smart Outfit Recommendation', 70, 90);

    ctx.font = '500 27px Trebuchet MS';
    ctx.fillStyle = '#cbd5e1';
    ctx.fillText(`Occasion: ${payload.occasion}  |  Weather: ${payload.weather}  |  City: ${payload.city || 'Not provided'}`, 70, 140);

    ctx.fillStyle = '#f8fafc';
    ctx.fillRect(70, 180, 700, 650);
    ctx.fillRect(820, 180, 710, 315);
    ctx.fillRect(820, 515, 710, 315);

    ctx.fillStyle = '#0f172a';
    ctx.font = '700 34px Trebuchet MS';
    ctx.fillText('Recommendation Summary', 100, 235);
    ctx.fillText('Top Recommended Pieces', 850, 235);
    ctx.fillText('Style & Pairing Notes', 850, 570);

    ctx.fillStyle = '#334155';
    ctx.font = '500 24px Trebuchet MS';
    let y = 285;
    y = drawWrappedText(ctx, `Weather Suggestions: ${(payload.weather_suggestions || []).slice(0, 2).join(' | ')}`, 100, y, 640, 40);
    y = drawWrappedText(ctx, `Style Tips: ${(payload.style_recommendations || []).slice(0, 2).join(' | ')}`, 100, y + 8, 640, 40);
    y = drawWrappedText(ctx, `Outfit Pairings: ${(payload.pairings || []).slice(0, 3).join(' | ')}`, 100, y + 8, 640, 40);

    const topCards = (payload.gallery_items || []).slice(0, 4);
    let pieceY = 285;
    ctx.font = '600 22px Trebuchet MS';
    topCards.forEach((item) => {
      const line = `${item.title} - $${Number(item.price_usd || 0).toFixed(2)} / NGN ${Number(item.price_ngn || 0).toLocaleString()}`;
      ctx.fillText(line, 850, pieceY);
      pieceY += 52;
    });

    let notesY = 620;
    ctx.font = '500 22px Trebuchet MS';
    (payload.style_recommendations || []).slice(0, 3).forEach((note) => {
      notesY = drawWrappedText(ctx, `• ${note}`, 850, notesY, 650, 34);
    });

    ctx.fillStyle = '#fef3c7';
    ctx.font = '600 20px Trebuchet MS';
    ctx.fillText(`Generated on ${new Date().toLocaleString()}`, 70, 870);

    const pngUrl = canvas.toDataURL('image/png');
    const link = document.createElement('a');
    link.href = pngUrl;
    link.download = `smart-outfit-presentation-${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  const readSavedLooks = function () {
    try {
      const raw = localStorage.getItem(storageKey);
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      return [];
    }
  };

  const writeSavedLooks = function (items) {
    localStorage.setItem(storageKey, JSON.stringify(items));
  };

  const renderSavedLooks = function () {
    if (!savedList) return;
    const items = readSavedLooks();
    savedList.innerHTML = '';

    if (items.length === 0) {
      savedList.innerHTML = '<p class="smart-empty-state">No looks saved yet. Generate and save your first recommendation.</p>';
      return;
    }

    items.forEach((item, index) => {
      const card = document.createElement('article');
      card.className = 'smart-saved-card';
      card.innerHTML = `
        <div>
          <h6>${item.occasion} - ${item.weather}</h6>
          <p>${item.city || 'City not provided'} - ${item.createdAt}</p>
        </div>
        <div class="smart-saved-card-actions">
          <button type="button" data-apply-index="${index}">Use</button>
          <button type="button" data-delete-index="${index}">Delete</button>
        </div>
      `;
      savedList.appendChild(card);
    });
  };

  const applySavedLook = function (savedLook) {
    if (!savedLook) return;
    renderList(weatherList, savedLook.weather_suggestions);
    renderList(styleList, savedLook.style_recommendations);
    renderList(pairingList, savedLook.pairings);
    renderGalleryCards(savedLook.gallery_items);
    renderInspirationCards(savedLook.inspiration_photos);

    featureMeta.textContent = `Occasion: ${savedLook.occasion} | Weather: ${savedLook.weather} (${savedLook.weather_source || 'saved'}) | City: ${savedLook.city || 'Not provided'}`;

    const scannerPanel = document.getElementById('feature-scanner-panel');
    const tryOnResultPanel = document.getElementById('feature-tryon-result-panel');
    if (scannerPanel) scannerPanel.style.display = 'none';
    tryOnNote.textContent = `${savedLook.virtual_try_on.simple_mode.note} ${savedLook.virtual_try_on.advanced_mode.note}`;

    if (savedLook.virtual_try_on.simple_mode.image) {
      mannequinImage.src = savedLook.virtual_try_on.simple_mode.image;
      mannequinImage.style.display = 'block';
      const dirCard = document.getElementById('feature-tryon-direction');
      if (dirCard) dirCard.style.display = 'none';
    } else {
      mannequinImage.style.display = 'none';
      const dirCard = document.getElementById('feature-tryon-direction');
      if (dirCard) {
        dirCard.style.display = 'flex';
        dirCard.innerHTML = `<h5>Outfit Direction</h5><div class="smart-tryon-direction-item">${savedLook.virtual_try_on.simple_mode.note}</div><div class="smart-tryon-direction-item">${savedLook.virtual_try_on.advanced_mode.note}</div>`;
      }
    }

    if (savedLook.virtual_try_on.advanced_mode.enabled && savedLook.virtual_try_on.advanced_mode.overlay_preview) {
      overlayImage.src = savedLook.virtual_try_on.advanced_mode.overlay_preview;
      overlayWrap.style.display = 'block';
    } else {
      overlayWrap.style.display = 'none';
    }

    if (tryOnResultPanel) tryOnResultPanel.style.display = 'block';

    mainFeatureResult.querySelectorAll('.smart-reveal').forEach(function (el) {
      el.classList.add('is-visible');
    });

    mainFeatureResult.style.display = 'block';
    mainFeatureStatus.style.display = 'block';
    mainFeatureStatus.className = 'smart-status';
    mainFeatureStatus.textContent = 'Loaded saved recommendation.';
  };

  if (savedList) {
    savedList.addEventListener('click', function (event) {
      const applyBtn = event.target.closest('[data-apply-index]');
      const deleteBtn = event.target.closest('[data-delete-index]');
      const items = readSavedLooks();

      if (applyBtn) {
        const idx = Number(applyBtn.getAttribute('data-apply-index'));
        applySavedLook(items[idx]);
      }

      if (deleteBtn) {
        const idx = Number(deleteBtn.getAttribute('data-delete-index'));
        const nextItems = items.filter(function (_, i) { return i !== idx; });
        writeSavedLooks(nextItems);
        renderSavedLooks();
        mainFeatureStatus.style.display = 'block';
        mainFeatureStatus.textContent = 'Saved look removed.';
      }
    });
  }

  if (saveBtn) {
    saveBtn.addEventListener('click', function () {
      if (!latestRecommendation) {
        mainFeatureStatus.style.display = 'block';
        mainFeatureStatus.textContent = 'Generate a recommendation first before saving.';
        return;
      }

      const items = readSavedLooks();
      const entry = {
        ...latestRecommendation,
        createdAt: new Date().toLocaleString()
      };

      const nextItems = [entry].concat(items).slice(0, 12);
      writeSavedLooks(nextItems);
      renderSavedLooks();
      mainFeatureStatus.style.display = 'block';
      mainFeatureStatus.textContent = 'Look saved successfully.';
    });
  }

  if (exportBtn) {
    exportBtn.addEventListener('click', function () {
      if (!latestRecommendation) {
        mainFeatureStatus.style.display = 'block';
        mainFeatureStatus.textContent = 'Generate a recommendation first before export.';
        return;
      }

      const dataBlob = new Blob([JSON.stringify(latestRecommendation, null, 2)], { type: 'application/json' });
      const objectUrl = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = objectUrl;
      link.download = `smart-outfit-${Date.now()}.json`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(objectUrl);

      mainFeatureStatus.style.display = 'block';
      mainFeatureStatus.textContent = 'Recommendation exported as JSON.';
    });
  }

  if (presentationBtn) {
    presentationBtn.addEventListener('click', function () {
      if (!latestRecommendation) {
        mainFeatureStatus.style.display = 'block';
        mainFeatureStatus.textContent = 'Generate a recommendation first before downloading a presentation card.';
        return;
      }

      try {
        exportPresentationCard(latestRecommendation);
        mainFeatureStatus.style.display = 'block';
        mainFeatureStatus.textContent = 'Presentation card downloaded as PNG.';
      } catch (error) {
        mainFeatureStatus.style.display = 'block';
        mainFeatureStatus.textContent = 'Unable to export presentation card.';
      }
    });
  }

  renderSavedLooks();

  mainFeatureForm.addEventListener('submit', async function (event) {
    event.preventDefault();

    // ── Dramatic loading helpers ──────────────────────────────
    const LOADING_STEPS = [
      'Reading occasion & weather data',
      'Building your style profile',
      'Curating outfit pieces',
      'Scanning trending inspirations',
      'Finalizing your personalized look',
    ];
    const STEP_MS = 650;
    const MIN_MS = LOADING_STEPS.length * STEP_MS + 400;

    mainFeatureResult.style.display = 'none';
    mainFeatureResult.querySelectorAll('.smart-reveal').forEach(function (el) {
      el.classList.remove('is-visible');
    });

    mainFeatureStatus.style.display = 'block';
    mainFeatureStatus.className = 'smart-status';
    mainFeatureStatus.innerHTML =
      '<div class="smart-loading-header"><div class="smart-loading-spinner"></div><span>AI Stylist is building your look\u2026</span></div>' +
      '<ul class="smart-loading-steps">' +
      LOADING_STEPS.map(function (s, i) { return '<li class="smart-loading-step" id="drm-step-' + i + '">' + s + '</li>'; }).join('') +
      '</ul>';

    LOADING_STEPS.forEach(function (_, i) {
      setTimeout(function () {
        var el = document.getElementById('drm-step-' + i);
        if (el) el.classList.add('active');
        if (i > 0) {
          var prev = document.getElementById('drm-step-' + (i - 1));
          if (prev) { prev.classList.remove('active'); prev.classList.add('done'); }
        }
      }, i * STEP_MS + 100);
    });

    if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = '\u2736 Generating\u2026'; }

    var minWait = new Promise(function (resolve) { setTimeout(resolve, MIN_MS); });

    var result = null;
    var apiError = null;
    try {
      var formData = new FormData(mainFeatureForm);
      var response = await fetch('/main-feature-recommendation', { method: 'POST', body: formData });
      var ct = response.headers.get('content-type') || '';
      if (ct.includes('application/json')) {
        result = await response.json();
      } else {
        var fallbackText = await response.text();
        throw new Error(fallbackText.slice(0, 120) || 'Server returned an invalid response.');
      }
      if (!response.ok) throw new Error(result.error || 'Unable to generate recommendations.');
    } catch (err) {
      apiError = err;
    }

    await minWait;

    if (apiError) {
      mainFeatureStatus.innerHTML = '';
      mainFeatureStatus.textContent = apiError.message || 'Something went wrong.';
    } else {
      latestRecommendation = result;

      featureMeta.textContent = 'Occasion: ' + result.occasion + ' | Weather: ' + result.weather + ' (' + result.weather_source + ') | City: ' + (result.city || 'Not set');
      renderList(weatherList, result.weather_suggestions);
      renderList(styleList, result.style_recommendations);
      renderList(pairingList, result.pairings);
      renderGalleryCards(result.gallery_items);
      renderInspirationCards(result.inspiration_photos);

      mainFeatureResult.style.display = 'block';

      var revealEls = Array.from(mainFeatureResult.querySelectorAll('.smart-reveal'));
      revealEls.forEach(function (el, idx) {
        setTimeout(function () {
          el.classList.add('is-visible');
          if (el.id === 'smart-tryon-section') {
            // ── Try-on scanner animation ──────────────────────
            var scannerPanel = document.getElementById('feature-scanner-panel');
            var tryOnResultPanel = document.getElementById('feature-tryon-result-panel');
            if (scannerPanel && tryOnResultPanel) {
              scannerPanel.style.display = 'block';
              scannerPanel.style.opacity = '1';
              tryOnResultPanel.style.display = 'none';
              var scanStepIds = ['scan-step-1', 'scan-step-2', 'scan-step-3', 'scan-step-4'];
              scanStepIds.forEach(function (sid) {
                var se = document.getElementById(sid);
                if (se) { se.classList.remove('active', 'done'); }
              });
              scanStepIds.forEach(function (sid, si) {
                setTimeout(function () {
                  var se = document.getElementById(sid);
                  if (se) se.classList.add('active');
                  if (si > 0) {
                    var prevSe = document.getElementById(scanStepIds[si - 1]);
                    if (prevSe) { prevSe.classList.remove('active'); prevSe.classList.add('done'); }
                  }
                }, si * 750 + 200);
              });
              var totalScan = scanStepIds.length * 750 + 200 + 500;
              setTimeout(function () {
                var lastSe = document.getElementById(scanStepIds[scanStepIds.length - 1]);
                if (lastSe) { lastSe.classList.remove('active'); lastSe.classList.add('done'); }
                setTimeout(function () {
                  scannerPanel.style.transition = 'opacity 0.5s ease';
                  scannerPanel.style.opacity = '0';
                  setTimeout(function () {
                    scannerPanel.style.display = 'none';
                    scannerPanel.style.opacity = '1';
                    scannerPanel.style.transition = '';
                    var td = result.virtual_try_on;
                    tryOnNote.textContent = td.simple_mode.note + ' ' + td.advanced_mode.note;
                    if (td.simple_mode.image) {
                      mannequinImage.src = td.simple_mode.image;
                      mannequinImage.style.display = 'block';
                      var dc = document.getElementById('feature-tryon-direction');
                      if (dc) dc.style.display = 'none';
                    } else {
                      mannequinImage.style.display = 'none';
                      var dc = document.getElementById('feature-tryon-direction');
                      if (dc) {
                        dc.style.display = 'flex';
                        dc.innerHTML = '<h5>Outfit Direction</h5><div class="smart-tryon-direction-item">' + td.simple_mode.note + '</div><div class="smart-tryon-direction-item">' + td.advanced_mode.note + '</div>';
                      }
                    }
                    if (td.advanced_mode.enabled && td.advanced_mode.overlay_preview) {
                      overlayImage.src = td.advanced_mode.overlay_preview;
                      overlayWrap.style.display = 'block';
                    } else {
                      overlayWrap.style.display = 'none';
                    }
                    tryOnResultPanel.style.display = 'block';
                    tryOnResultPanel.classList.remove('smart-tryon-fade-in');
                    void tryOnResultPanel.offsetWidth;
                    tryOnResultPanel.classList.add('smart-tryon-fade-in');
                  }, 500);
                }, 300);
              }, totalScan);
            }
          }
        }, idx * 280);
      });

      setTimeout(function () {
        mainFeatureStatus.innerHTML = '';
        mainFeatureStatus.textContent = '\u2736 Your look is ready.';
      }, revealEls.length * 280 + 200);
    }

    if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = '\u2736 Generate My Look'; }
  });
}