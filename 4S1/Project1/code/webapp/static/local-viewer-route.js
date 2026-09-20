// Preserve old localhost bookmarks while the original static server stays running.
// The archive needs the saved-result APIs supplied by portal_server.py on 8767.
if (['127.0.0.1', 'localhost'].includes(location.hostname) && location.port === '8766') {
  const viewer = new URL(location.href);
  viewer.port = '8767';
  location.replace(viewer.href);
}
