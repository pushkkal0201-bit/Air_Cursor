; AirCursor 2.2.0 Windows installer, built after PyInstaller.
#define MyAppName "AirCursor"
#define MyAppVersion "2.2.0"
#define MyAppPublisher "Pushkkal Gupta"
#define MyAppURL "https://github.com/pushkkal0201-bit/Air_Cursor"

[Setup]
AppId=AirCursor.Pushkkal.2
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
DefaultDirName={localappdata}\Programs\AirCursor
DefaultGroupName=AirCursor
DisableProgramGroupPage=yes
OutputDir=..\dist\installer
OutputBaseFilename=AirCursor-2.2.0-Windows-Setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
UninstallDisplayIcon={app}\AirCursor.exe
LicenseFile=..\LICENSE

[Files]
Source: "..\dist\AirCursor\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\AirCursor (This PC only)"; Filename: "{app}\AirCursor.exe"; Parameters: "--local-only"; WorkingDir: "{app}"
Name: "{autoprograms}\AirCursor (Private Wi-Fi)"; Filename: "{app}\AirCursor.exe"; Parameters: "--lan"; WorkingDir: "{app}"; Comment: "Remote control: only on your trusted private network"
Name: "{autodesktop}\AirCursor (This PC only)"; Filename: "{app}\AirCursor.exe"; Parameters: "--local-only"; Tasks: desktopicon; WorkingDir: "{app}"

[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut for local-only mode"; GroupDescription: "Shortcuts:"; Flags: unchecked
