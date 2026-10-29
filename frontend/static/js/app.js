document.addEventListener('DOMContentLoaded', () => {
  // State
  let page = 1;
  let activeTab = 'active'; // 'active' | 'archived'
  let searchQuery = '';
  let copiedId = null;
  let currentCreatedLink = null;

  // DOM Elements - ShortenCard
  const shortenForm = document.getElementById('shortenForm');
  const urlInput = document.getElementById('urlInput');
  const customSlugInput = document.getElementById('customSlugInput');
  const toggleSlugBtn = document.getElementById('toggleSlugBtn');
  const slugDrawer = document.getElementById('slugDrawer');
  const submitShortenBtn = document.getElementById('submitShortenBtn');
  const cyberErrorBox = document.getElementById('cyberErrorBox');
  const cyberErrorMsg = document.getElementById('cyberErrorMsg');
  const resultBanner = document.getElementById('resultBanner');
  const resultLinkText = document.getElementById('resultLinkText');
  const resultTargetPreview = document.getElementById('resultTargetPreview');
  const resultQrPreviewImg = document.getElementById('resultQrPreviewImg');
  const resultCopyBtn = document.getElementById('resultCopyBtn');
  const resultCopyLabel = document.getElementById('resultCopyLabel');
  const resultQrBtn = document.getElementById('resultQrBtn');
  const resultOpenBtn = document.getElementById('resultOpenBtn');
  const slugPrefixHost = document.getElementById('slugPrefixHost');

  // DOM Elements - Modal
  const modalBackdrop = document.getElementById('modalBackdrop');
  const closeModalBtn = document.getElementById('closeModalBtn');
  const doneModalBtn = document.getElementById('doneModalBtn');
  const modalQrImage = document.getElementById('modalQrImage');
  const modalShortCodeText = document.getElementById('modalShortCodeText');

  // DOM Elements - Telemetry Cards
  const telemetryActiveLinks = document.getElementById('telemetryActiveLinks');
  const telemetryTotalClicks = document.getElementById('telemetryTotalClicks');
  const telemetryUniqueClicks = document.getElementById('telemetryUniqueClicks');
  const telemetryConversionRate = document.getElementById('telemetryConversionRate');

  // DOM Elements - MetricsTable
  const tabActiveBtn = document.getElementById('tabActiveBtn');
  const tabArchivedBtn = document.getElementById('tabArchivedBtn');
  const searchInput = document.getElementById('searchInput');
  const linksTableBody = document.getElementById('linksTableBody');
  const mainLinksTable = document.getElementById('mainLinksTable');
  const tableEmptyState = document.getElementById('tableEmptyState');
  const tableEmptyMessage = document.getElementById('tableEmptyMessage');
  const paginationContainer = document.getElementById('paginationContainer');
  const paginationInfo = document.getElementById('paginationInfo');
  const prevPageBtn = document.getElementById('prevPageBtn');
  const nextPageBtn = document.getElementById('nextPageBtn');

  // Set host prefix in slug drawer
  if (slugPrefixHost) {
    slugPrefixHost.textContent = `${window.location.host}/`;
  }

  // CSRF Token Helper
  function getCsrfToken() {
    const input = document.querySelector('[name=csrfmiddlewaretoken]');
    if (input) return input.value;
    const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
  }

  // QR Code generator helper
  function getQrCodeUrl(shortUrl) {
    if (!shortUrl) return '';
    return `https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(shortUrl)}`;
  }

  // Modal Control
  function setShowQrModal(show) {
    if (!modalBackdrop) return;
    if (show && currentCreatedLink) {
      const fullUrl = `${window.location.origin}/${currentCreatedLink.short_code}`;
      modalQrImage.src = `https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(fullUrl)}`;
      modalShortCodeText.textContent = `/${currentCreatedLink.short_code}`;
      modalBackdrop.style.display = 'flex';
    } else {
      modalBackdrop.style.display = 'none';
    }
  }

  if (closeModalBtn) closeModalBtn.addEventListener('click', () => setShowQrModal(false));
  if (doneModalBtn) doneModalBtn.addEventListener('click', () => setShowQrModal(false));
  if (modalBackdrop) {
    modalBackdrop.addEventListener('click', () => setShowQrModal(false));
  }

  // Toggle Custom Slug Drawer
  if (toggleSlugBtn && slugDrawer) {
    toggleSlugBtn.addEventListener('click', () => {
      const isVisible = slugDrawer.style.display !== 'none';
      slugDrawer.style.display = isVisible ? 'none' : 'block';
      toggleSlugBtn.classList.toggle('active', !isVisible);
    });
  }

  // Fetch Telemetry Global Stats
  async function fetchGlobalStats() {
    try {
      const res = await fetch('/links/stats');
      if (!res.ok) return;
      const stats = await res.json();

      if (telemetryActiveLinks) {
        telemetryActiveLinks.textContent = (stats.totalLinks === undefined || stats.totalLinks === null)
          ? '—'
          : stats.totalLinks;
      }
      if (telemetryTotalClicks) {
        telemetryTotalClicks.textContent = (stats.totalClicks ?? 0).toLocaleString();
      }
      if (telemetryUniqueClicks) {
        telemetryUniqueClicks.textContent = (stats.totalUniqueClicks ?? 0).toLocaleString();
      }
      if (telemetryConversionRate) {
        telemetryConversionRate.textContent = `${stats.averageConversionRate ?? 0}%`;
      }
    } catch (e) {
      console.error('Failed to fetch stats:', e);
    }
  }

  // Helper Domain Extractor
  function getDomain(url) {
    try {
      return new URL(url).hostname;
    } catch {
      return 'link';
    }
  }

  // Helper Relative Time Formatter
  function formatRelativeTime(isoString) {
    if (!isoString) return 'just now';
    try {
      const now = new Date();
      const past = new Date(isoString);
      const diffSecs = Math.floor((now.getTime() - past.getTime()) / 1000);
      if (diffSecs < 60) return 'just now';
      const diffMins = Math.floor(diffSecs / 60);
      if (diffMins < 60) return `${diffMins}m ago`;
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `${diffHours}h ago`;
      const diffDays = Math.floor(diffHours / 24);
      return `${diffDays}d ago`;
    } catch {
      return 'recently';
    }
  }

  // Load Directory Links Table
  async function fetchLinks() {
    const isArchived = activeTab === 'archived';

    try {
      const res = await fetch(`/links?page=${page}&limit=10&includeDeleted=${isArchived}`);
      if (!res.ok) throw new Error('Registry query error');
      const data = await res.json();

      renderTable(data.data || [], isArchived);
      renderPagination(data.pagination);
    } catch (err) {
      console.error(err);
      if (tableEmptyState) {
        tableEmptyState.style.display = 'block';
        tableEmptyMessage.textContent = 'Registry query error: Network error';
        mainLinksTable.style.display = 'none';
      }
    }
  }

  // Render Table Rows
  function renderTable(links, isArchived) {
    const filteredLinks = searchQuery
      ? links.filter(link => link.short_code === searchQuery)
      : links;

    if (filteredLinks.length === 0) {
      tableEmptyState.style.display = 'block';
      mainLinksTable.style.display = 'none';
      tableEmptyMessage.textContent = searchQuery
        ? 'No shortened links match your search query.'
        : isArchived
        ? 'No archived links in your workspace.'
        : 'No active links available for this page view.';
      return;
    }

    tableEmptyState.style.display = 'none';
    mainLinksTable.style.display = 'table';
    linksTableBody.innerHTML = '';

    filteredLinks.forEach(link => {
      const shortUrl = `${window.location.origin}/${link.short_code}`;
      const isCopied = copiedId === link.id;
      const domain = getDomain(link.original_url);

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>
          <div class="link-identity">
            <img
              src="https://www.google.com/s2/favicons?domain=${domain}&sz=32"
              alt=""
              class="favicon-icon"
              onerror="this.style.display='none'"
            />
            <div style="display: flex; align-items: center; gap: 0.4rem;">
              <a
                href="${shortUrl}"
                target="_blank"
                rel="noreferrer"
                class="slug-text"
              >
                /${link.short_code}
              </a>
              <button
                type="button"
                class="btn-ghost copy-row-btn"
                style="padding: 0.2rem 0.35rem;"
                title="Copy link"
                data-id="${link.id}"
                data-code="${link.short_code}"
              >
                ${isCopied
                  ? `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--neon-green)" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>`
                  : `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`
                }
              </button>
            </div>
          </div>
        </td>

        <td>
          <span class="target-url-text" title="${link.original_url}">
            ${link.original_url}
          </span>
        </td>

        <td style="text-align: center;">
          <span class="badge-pill badge-clicks">
            ${link.clicks.toLocaleString()}
          </span>
        </td>

        <td>
          <div class="badge-referrer">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"></polygon></svg>
            <span>${link.top_referrer || 'direct'}</span>
          </div>
        </td>

        <td style="text-align: center;">
          <span class="badge-pill badge-rate">
            ${link.conversion_rate}%
          </span>
        </td>

        <td style="color: var(--text-muted); font-size: 0.8rem; white-space: nowrap; font-family: var(--font-mono);">
          ${formatRelativeTime(link.created_at)}
        </td>

        <td style="text-align: right;">
          <div style="display: inline-flex; gap: 0.35rem; align-items: center;">
            <a
              href="${shortUrl}"
              target="_blank"
              rel="noreferrer"
              class="btn-ghost"
              style="padding: 0.35rem;"
              title="Open URL"
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
            </a>

            ${isArchived
              ? `
                <button
                  type="button"
                  class="btn-secondary restore-link-btn"
                  style="padding: 0.3rem 0.65rem; font-size: 0.75rem; color: #86efac;"
                  data-id="${link.id}"
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg>
                  <span>Restore</span>
                </button>
              `
              : `
                <button
                  type="button"
                  class="btn-danger-ghost archive-link-btn"
                  title="Archive link"
                  data-id="${link.id}"
                >
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="21 8 21 21 3 21 3 8"></polyline><rect x="1" y="3" width="22" height="5"></rect><line x1="10" y1="12" x2="14" y2="12"></line></svg>
                </button>
              `
            }
          </div>
        </td>
      `;

      linksTableBody.appendChild(tr);
    });
  }

  // Render Pagination
  function renderPagination(pagination) {
    if (!pagination || pagination.totalPages <= 1) {
      paginationContainer.style.display = 'none';
      return;
    }
    paginationContainer.style.display = 'flex';
    paginationInfo.textContent = `Page ${pagination.page} of ${pagination.totalPages} · (${pagination.total} total links)`;
    prevPageBtn.disabled = pagination.page <= 1;
    nextPageBtn.disabled = pagination.page >= pagination.totalPages;
  }

  // Handle Shorten Form Submit
  if (shortenForm) {
    shortenForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      cyberErrorBox.style.display = 'none';

      const urlVal = urlInput.value.trim();
      const slugVal = customSlugInput.value.trim();

      if (!urlVal) {
        cyberErrorBox.style.display = 'flex';
        cyberErrorMsg.textContent = 'Target URL is required';
        return;
      }

      submitShortenBtn.disabled = true;
      submitShortenBtn.textContent = 'PROCESSING...';

      try {
        const payload = { originalUrl: urlVal };
        if (slugVal) payload.customSlug = slugVal;

        const res = await fetch('/links', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
          },
          body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (!res.ok) {
          const err = data.error || (data.details && data.details.originalUrl && data.details.originalUrl[0]) || 'Failed to shorten URL';
          cyberErrorBox.style.display = 'flex';
          cyberErrorMsg.textContent = err;
          return;
        }

        // Success: display result banner
        currentCreatedLink = data;
        const fullShortUrl = `${window.location.origin}/${data.short_code}`;

        resultLinkText.textContent = fullShortUrl;
        resultLinkText.href = fullShortUrl;
        resultTargetPreview.textContent = `Target: ${data.original_url}`;
        resultOpenBtn.href = fullShortUrl;

        resultQrPreviewImg.src = getQrCodeUrl(fullShortUrl);

        resultBanner.style.display = 'flex';

        // Clear inputs
        urlInput.value = '';
        customSlugInput.value = '';
        if (slugDrawer) slugDrawer.style.display = 'none';
        if (toggleSlugBtn) toggleSlugBtn.classList.remove('active');

        // Refresh stats & table
        fetchGlobalStats();
        fetchLinks();

      } catch (err) {
        cyberErrorBox.style.display = 'flex';
        cyberErrorMsg.textContent = err.message || 'Failed to shorten URL';
      } finally {
        submitShortenBtn.disabled = false;
        submitShortenBtn.textContent = '► SHORTEN LINK';
      }
    });
  }

  // Result Copy Button
  if (resultCopyBtn) {
    resultCopyBtn.addEventListener('click', () => {
      if (!currentCreatedLink) return;
      const fullShortUrl = `${window.location.origin}/${currentCreatedLink.short_code}`;
      navigator.clipboard.writeText(fullShortUrl);
      resultCopyLabel.textContent = 'Copied';
      resultCopyLabel.style.color = 'var(--neon-green)';
      setTimeout(() => {
        resultCopyLabel.textContent = 'Copy';
        resultCopyLabel.style.color = '';
      }, 2000);
    });
  }

  if (resultQrBtn) {
    resultQrBtn.addEventListener('click', () => {
      setShowQrModal(false);
    });
  }

  // Table Event Delegation (Copy, Archive, Restore)
  if (linksTableBody) {
    linksTableBody.addEventListener('click', async (e) => {
      // Copy
      const copyBtn = e.target.closest('.copy-row-btn');
      if (copyBtn) {
        const id = parseInt(copyBtn.getAttribute('data-id'), 10);
        const code = copyBtn.getAttribute('data-code');
        const fullUrl = `${window.location.origin}/${code}`;
        navigator.clipboard.writeText(fullUrl);
        copiedId = id;
        fetchLinks();
        setTimeout(() => {
          copiedId = null;
          fetchLinks();
        }, 2000);
        return;
      }

      // Archive Link
      const archiveBtn = e.target.closest('.archive-link-btn');
      if (archiveBtn) {
        const id = archiveBtn.getAttribute('data-id');
        try {
          const res = await fetch(`/links/${id}`, {
            method: 'DELETE',
            headers: { 'X-CSRFToken': getCsrfToken() }
          });
          if (res.ok) {
            fetchLinks();
            fetchGlobalStats();
          } else {
            const data = await res.json();
            alert(data.error || 'Failed to archive link');
          }
        } catch (err) {
          alert(err.message || 'Failed to archive link');
        }
        return;
      }

      // Restore Link
      const restoreBtn = e.target.closest('.restore-link-btn');
      if (restoreBtn) {
        const id = restoreBtn.getAttribute('data-id');
        try {
          const res = await fetch(`/links/${id}/restore`, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCsrfToken() }
          });
          if (res.ok) {
            fetchLinks();
            fetchGlobalStats();
          } else {
            const data = await res.json();
            alert(data.error || 'Failed to restore link');
          }
        } catch (err) {
          alert(err.message || 'Failed to restore link');
        }
        return;
      }
    });
  }

  // Tab switching
  if (tabActiveBtn && tabArchivedBtn) {
    tabActiveBtn.addEventListener('click', () => {
      if (activeTab === 'active') return;
      activeTab = 'active';
      tabActiveBtn.classList.add('active');
      tabArchivedBtn.classList.remove('active');
      page = 1;
      fetchLinks();
    });

    tabArchivedBtn.addEventListener('click', () => {
      if (activeTab === 'archived') return;
      activeTab = 'archived';
      tabArchivedBtn.classList.add('active');
      tabActiveBtn.classList.remove('active');
      page = 1;
      fetchLinks();
    });
  }

  // Search Input Filter
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      searchQuery = e.target.value.trim();
      fetchLinks();
    });
  }

  // Pagination Buttons
  if (prevPageBtn) {
    prevPageBtn.addEventListener('click', () => {
      if (page > 1) {
        page -= 1;
        fetchLinks();
      }
    });
  }
  if (nextPageBtn) {
    nextPageBtn.addEventListener('click', () => {
      page += 1;
      fetchLinks();
    });
  }

  // Initial load
  fetchGlobalStats();
  fetchLinks();
});
