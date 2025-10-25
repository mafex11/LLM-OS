const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  acceptTerms: () => ipcRenderer.send('accept-terms'),
  declineTerms: () => ipcRenderer.send('decline-terms'),
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  getDataPaths: () => ipcRenderer.invoke('get-data-paths'),
  openDataFolder: () => ipcRenderer.invoke('open-data-folder'),
  openConfigFolder: () => ipcRenderer.invoke('open-config-folder'),
  openLogsFolder: () => ipcRenderer.invoke('open-logs-folder'),
  onStatus: (callback) => ipcRenderer.on('status', (event, status) => callback(status)),
  
  // Audio device access for voice mode
  requestMicrophonePermission: () => ipcRenderer.invoke('request-microphone-permission'),
  getAudioDevices: () => ipcRenderer.invoke('get-audio-devices'),
  onMicrophonePermissionChanged: (callback) => ipcRenderer.on('microphone-permission-changed', (event, granted) => callback(granted))
});

