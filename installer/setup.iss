; ============================================
; UceAsistan Windows Installer
; Inno Setup Script
; ============================================

#define MyAppName "UceAsistan"
#define MyAppVersion "2.2.0"
#define MyAppPublisher "UceAsistan SaaS"
#define MyAppURL "https://uceasistan.com"
#define MyAppExeName "Start UceAsistan.bat"

[Setup]
AppId={{B8C4F2E3-9A1D-4B5C-8E7F-2A3D4E5F6A7B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/support
AppUpdatesURL={#MyAppURL}/updates
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\LICENSE.txt
OutputDir=output
OutputBaseFilename=UceAsistan_Setup_{#MyAppVersion}
SetupIconFile=..\assets\jaguar_logo.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Backend files
Source: "..\backend\*"; DestDir: "{app}\backend"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "__pycache__,*.pyc,.env,logs"
; Frontend files
Source: "..\index.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\*.js"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\*.css"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs
; Launcher
Source: "launcher.bat"; DestDir: "{app}"; DestName: "Start UceAsistan.bat"; Flags: ignoreversion
; README
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\jaguar_logo.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\jaguar_logo.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: shellexec postinstall skipifsilent

[Registry]
Root: HKLM; Subkey: "SOFTWARE\UceAsistan"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\UceAsistan"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"

[Code]
// Check for Python installation
function IsPythonInstalled: Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('python', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

// Check for MT5 installation
function IsMT5Installed: Boolean;
begin
  Result := FileExists(ExpandConstant('{pf}\MetaTrader 5\terminal64.exe')) or 
            FileExists(ExpandConstant('{pf32}\MetaTrader 5\terminal.exe')) or
            DirExists(ExpandConstant('{userappdata}\MetaQuotes\Terminal'));
end;

function InitializeSetup: Boolean;
begin
  Result := True;
  
  // Check Python
  if not IsPythonInstalled then
  begin
    if MsgBox('Python 3.10+ gereklidir. Python kurulu degil gibi gorunuyor.' + #13#10 + 
              'Kuruluma devam etmek istiyor musunuz?', mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
    end;
  end;
  
  // Check MT5
  if not IsMT5Installed then
  begin
    MsgBox('MetaTrader 5 terminal bulunamadi.' + #13#10 + 
           'Tam islevsellik icin MT5 kurulmalidir.', mbInformation, MB_OK);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    // Install Python dependencies
    Exec('python', '-m pip install -r "' + ExpandConstant('{app}') + '\backend\requirements.txt"', 
         '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
         
    // Create .env from example if not exists
    if not FileExists(ExpandConstant('{app}\backend\.env')) then
    begin
      FileCopy(ExpandConstant('{app}\backend\.env.example'), 
               ExpandConstant('{app}\backend\.env'), False);
    end;
  end;
end;
