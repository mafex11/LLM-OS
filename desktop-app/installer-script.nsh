; Custom NSIS installer script for Windows-Use AI
; Creates data directories in C:\ProgramData for shared app data

!macro customInstall
  ; Get ProgramData path from registry (more reliable than $PROGRAMDATA)
  ReadRegStr $0 HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" "Common AppData"
  StrCpy $1 "$APPDATA"
  
  ; Create app data directory in ProgramData
  CreateDirectory "$0\WindowsUse"
  CreateDirectory "$0\WindowsUse\logs"
  CreateDirectory "$0\WindowsUse\config"
  CreateDirectory "$0\WindowsUse\cache"
  CreateDirectory "$0\WindowsUse\data"
  
  ; Note: AccessControl plugin not available in electron-builder NSIS
  ; Permissions will be set by the application at runtime if needed
  DetailPrint "Created directories with default permissions"
  
  ; Also create user-specific data directory in AppData
  CreateDirectory "$1\WindowsUse"
  CreateDirectory "$1\WindowsUse\logs"
  CreateDirectory "$1\WindowsUse\config"
  
  ; Create .env file template if it doesn't exist
  IfFileExists "$0\WindowsUse\config\.env" skip_env_creation
    FileOpen $2 "$0\WindowsUse\config\.env" w
    FileWrite $2 "# Windows-Use AI Configuration$\r$\n"
    FileWrite $2 "# Add your API keys here$\r$\n$\r$\n"
    FileWrite $2 "GOOGLE_API_KEY=$\r$\n"
    FileWrite $2 "ELEVENLABS_API_KEY=$\r$\n"
    FileWrite $2 "DEEPGRAM_API_KEY=$\r$\n$\r$\n"
    FileWrite $2 "# TTS Settings$\r$\n"
    FileWrite $2 "ENABLE_TTS=true$\r$\n"
    FileWrite $2 "TTS_VOICE_ID=21m00Tcm4TlvDq8ikWAM$\r$\n"
    FileClose $2
  skip_env_creation:
  
  ; Write data directory paths to registry for the app to find them
  WriteRegStr HKLM "Software\WindowsUse" "DataPath" "$0\WindowsUse"
  WriteRegStr HKCU "Software\WindowsUse" "UserDataPath" "$1\WindowsUse"
  
  ; Display info message
  DetailPrint "Created data directories:"
  DetailPrint "  - $0\WindowsUse"
  DetailPrint "  - $1\WindowsUse"
!macroend

!macro customUnInstall
  ; Ask user if they want to keep their data
  MessageBox MB_YESNO|MB_ICONQUESTION "Do you want to remove all Windows-Use AI data including logs and configuration? This cannot be undone." IDYES remove_data IDNO keep_data
  
  remove_data:
    ; Get ProgramData path from registry (same as install)
    ReadRegStr $0 HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" "Common AppData"
    StrCpy $1 "$APPDATA"
    RMDir /r "$0\WindowsUse"
    RMDir /r "$1\WindowsUse"
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

