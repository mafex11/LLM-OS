const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  acceptTerms: () => ipcRenderer.send('accept-terms'),
  declineTerms: () => ipcRenderer.send('decline-terms'),
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  onStatus: (callback) => ipcRenderer.on('status', (event, status) => callback(status))
});

