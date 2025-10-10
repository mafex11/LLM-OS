; Custom NSIS installer script for Windows-Use AI
; Creates data directories in C:\ProgramData for shared app data

!macro customInstall
  ; Create app data directory in C:\ProgramData
  CreateDirectory "$PROGRAMDATA\WindowsUse"
  CreateDirectory "$PROGRAMDATA\WindowsUse\logs"
  CreateDirectory "$PROGRAMDATA\WindowsUse\config"
  CreateDirectory "$PROGRAMDATA\WindowsUse\cache"
  CreateDirectory "$PROGRAMDATA\WindowsUse\data"
  
  ; Set permissions so all users can write to these folders
  AccessControl::GrantOnFile "$PROGRAMDATA\WindowsUse" "(S-1-5-32-545)" "FullAccess"
  AccessControl::GrantOnFile "$PROGRAMDATA\WindowsUse\logs" "(S-1-5-32-545)" "FullAccess"
  AccessControl::GrantOnFile "$PROGRAMDATA\WindowsUse\config" "(S-1-5-32-545)" "FullAccess"
  AccessControl::GrantOnFile "$PROGRAMDATA\WindowsUse\cache" "(S-1-5-32-545)" "FullAccess"
  AccessControl::GrantOnFile "$PROGRAMDATA\WindowsUse\data" "(S-1-5-32-545)" "FullAccess"
  
  ; Also create user-specific data directory in AppData
  CreateDirectory "$APPDATA\WindowsUse"
  CreateDirectory "$APPDATA\WindowsUse\logs"
  CreateDirectory "$APPDATA\WindowsUse\config"
  
  ; Create .env file template if it doesn't exist
  IfFileExists "$PROGRAMDATA\WindowsUse\config\.env" skip_env_creation
    FileOpen $0 "$PROGRAMDATA\WindowsUse\config\.env" w
    FileWrite $0 "# Windows-Use AI Configuration$\r$\n"
    FileWrite $0 "# Add your API keys here$\r$\n$\r$\n"
    FileWrite $0 "GOOGLE_API_KEY=$\r$\n"
    FileWrite $0 "ELEVENLABS_API_KEY=$\r$\n"
    FileWrite $0 "DEEPGRAM_API_KEY=$\r$\n$\r$\n"
    FileWrite $0 "# TTS Settings$\r$\n"
    FileWrite $0 "ENABLE_TTS=true$\r$\n"
    FileWrite $0 "TTS_VOICE_ID=21m00Tcm4TlvDq8ikWAM$\r$\n"
    FileClose $0
  skip_env_creation:
  
  ; Write data directory paths to registry for the app to find them
  WriteRegStr HKLM "Software\WindowsUse" "DataPath" "$PROGRAMDATA\WindowsUse"
  WriteRegStr HKCU "Software\WindowsUse" "UserDataPath" "$APPDATA\WindowsUse"
  
  ; Display info message
  DetailPrint "Created data directories:"
  DetailPrint "  - C:\ProgramData\WindowsUse"
  DetailPrint "  - $APPDATA\WindowsUse"
!macroend

!macro customUnInstall
  ; Ask user if they want to keep their data
  MessageBox MB_YESNO|MB_ICONQUESTION "Do you want to remove all Windows-Use AI data including logs and configuration? This cannot be undone." IDYES remove_data IDNO keep_data
  
  remove_data:
    RMDir /r "$PROGRAMDATA\WindowsUse"
    RMDir /r "$APPDATA\WindowsUse"
    DeleteRegKey HKLM "Software\WindowsUse"
    DeleteRegKey HKCU "Software\WindowsUse"
    DetailPrint "All application data removed"
    Goto done
  
  keep_data:
    DetailPrint "Application data preserved at:"
    DetailPrint "  - C:\ProgramData\WindowsUse"
    DetailPrint "  - $APPDATA\WindowsUse"
  
  done:
!macroend

