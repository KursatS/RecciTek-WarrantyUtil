[Setup]
AppName=Garanti Takip Sistemi
AppVersion=1.0
AppPublisher=Kursat Sinan
DefaultDirName={localappdata}\Garanti Takip Sistemi
DefaultGroupName=Garanti Takip Sistemi
OutputDir=.
OutputBaseFilename=GarantiSetup
SetupIconFile=logo.ico
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\GarantiV6\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Garanti Takip Sistemi"; Filename: "{app}\GarantiV6.exe"
Name: "{commondesktop}\Garanti Takip Sistemi"; Filename: "{app}\GarantiV6.exe"

[Run]
Filename: "{app}\GarantiV6.exe"; Description: "Garanti Takip Sistemi'ni Başlat"; Flags: nowait postinstall
