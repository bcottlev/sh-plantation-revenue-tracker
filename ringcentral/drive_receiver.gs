/**
 * RingCentral archive receiver — paste into a new Google Apps Script project
 * (script.google.com, signed in as the Google account that should own the files)
 * and deploy as a Web app: Execute as "Me", Who has access "Anyone".
 *
 * The nightly GitHub Action posts each day's raw call and text records here;
 * this saves them as JSON files in a private Drive folder called
 * "RingCentral Archive" (calls/YYYY-MM/YYYY-MM-DD.json, texts/...).
 * Re-sending a day overwrites that day's file.
 *
 * Set TOKEN to the same passphrase you store in the DRIVE_WEBHOOK_TOKEN
 * GitHub secret. Requests without it are refused.
 */
const TOKEN = 'PASTE_YOUR_PASSPHRASE_HERE';
const ROOT_FOLDER = 'RingCentral Archive';

function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);
    if (!TOKEN || TOKEN === 'PASTE_YOUR_PASSPHRASE_HERE' || body.token !== TOKEN) {
      return reply_({ ok: false, error: 'unauthorized' });
    }
    const parts = String(body.path || '').split('/').filter(String);
    if (!parts.length || parts.some(p => p === '..')) return reply_({ ok: false, error: 'bad path' });
    const name = parts.pop();
    let folder = folder_(DriveApp.getRootFolder(), ROOT_FOLDER);
    parts.forEach(p => { folder = folder_(folder, p); });
    const existing = folder.getFilesByName(name);
    if (existing.hasNext()) existing.next().setContent(body.content);
    else folder.createFile(name, body.content, 'application/json');
    return reply_({ ok: true });
  } catch (err) {
    return reply_({ ok: false, error: String(err) });
  }
}

function folder_(parent, name) {
  const it = parent.getFoldersByName(name);
  return it.hasNext() ? it.next() : parent.createFolder(name);
}

function reply_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
