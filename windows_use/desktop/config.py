from typing import Set

BROWSER_NAMES=set([
    'msedge.exe',      # Microsoft Edge
    'chrome.exe',      # Google Chrome
    'firefox.exe',     # Mozilla Firefox
    'opera.exe',       # Opera Browser
    'brave.exe',       # Brave Browser
    'vivaldi.exe',     # Vivaldi Browser
    'iexplore.exe'     # Internet Explorer
])

AVOIDED_APPS:Set[str]=set([
    'Recording toolbar'
])

EXCLUDED_APPS:Set[str]=set([
    'Progman','Shell_TrayWnd',
    'Microsoft.UI.Content.PopupWindowSiteBridge',
    'Windows.UI.Core.CoreWindow',
]).union(AVOIDED_APPS)