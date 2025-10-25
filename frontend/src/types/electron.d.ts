declare global {
  interface Window {
    electronAPI: {
      acceptTerms: () => void;
      declineTerms: () => void;
      openExternal: (url: string) => Promise<void>;
      getAppVersion: () => Promise<string>;
      getDataPaths: () => Promise<any>;
      openDataFolder: () => Promise<void>;
      openConfigFolder: () => Promise<void>;
      openLogsFolder: () => Promise<void>;
      onStatus: (callback: (status: string) => void) => void;
      
      // Audio device access for voice mode
      requestMicrophonePermission: () => Promise<boolean>;
      getAudioDevices: () => Promise<Array<{
        deviceId: string;
        label: string;
        kind: 'audioinput' | 'audiooutput';
      }>>;
      onMicrophonePermissionChanged: (callback: (granted: boolean) => void) => void;
    };
  }
}

export {};
