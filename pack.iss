; 脚本由 Inno Setup 脚本向导生成。
; 有关创建 Inno Setup 脚本文件的详细信息，请参阅帮助文档！
; 仅供非商业使用

#define MyAppName "HeartRateReceiver"
#define MyAppVersion "2.0 Preview"
#define MyAppPublisher "EnderHack"
#define MyAppExeName "HeartRateMonitor.exe"
#define MyAppAssocName "心率导出数据"
#define MyAppAssocExt ".hrof"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
; 注意：AppId 的值唯一标识此应用程序。不要在其他应用程序的安装程序中使用相同的 AppId 值。
; (若要生成新的 GUID，请在 IDE 中单击 "工具|生成 GUID"。)
AppId={{B72E0289-7E59-4353-AE2F-83EA2B21F1D2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
; "ArchitecturesAllowed=x64compatible" 指定
; 安装程序只能在 x64 和 Windows 11 on Arm 上运行。
ArchitecturesAllowed=x64compatible
; "ArchitecturesInstallIn64BitMode=x64compatible" 要求
; 在 X64 或 Windows 11 on Arm 上以 "64-位模式" 进行安装，
; 这意味着它应该使用本地 64 位 Program Files 目录
; 和注册表的 64 位视图。
ArchitecturesInstallIn64BitMode=x64compatible
ChangesAssociations=yes
DisableProgramGroupPage=yes
; 取消注释以下行以在非管理安装模式下运行 (仅为当前用户安装)。
;PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=D:\HeartrateReceiver\dist
OutputBaseFilename=HeartRateReceiver
SetupIconFile=D:\HeartrateReceiver\icon.ico
SolidCompression=yes
WizardStyle=modern dynamic

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Default.isl"
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"
Name: "armenian"; MessagesFile: "compiler:Languages\Armenian.isl"
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "bulgarian"; MessagesFile: "compiler:Languages\Bulgarian.isl"
Name: "catalan"; MessagesFile: "compiler:Languages\Catalan.isl"
Name: "chinesetraditional"; MessagesFile: "compiler:Languages\ChineseTraditional.isl"
Name: "corsican"; MessagesFile: "compiler:Languages\Corsican.isl"
Name: "czech"; MessagesFile: "compiler:Languages\Czech.isl"
Name: "danish"; MessagesFile: "compiler:Languages\Danish.isl"
Name: "dutch"; MessagesFile: "compiler:Languages\Dutch.isl"
Name: "english"; MessagesFile: "compiler:Languages\English.isl"
Name: "finnish"; MessagesFile: "compiler:Languages\Finnish.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "hebrew"; MessagesFile: "compiler:Languages\Hebrew.isl"
Name: "hungarian"; MessagesFile: "compiler:Languages\Hungarian.isl"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"
Name: "norwegian"; MessagesFile: "compiler:Languages\Norwegian.isl"
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "slovak"; MessagesFile: "compiler:Languages\Slovak.isl"
Name: "slovenian"; MessagesFile: "compiler:Languages\Slovenian.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "swedish"; MessagesFile: "compiler:Languages\Swedish.isl"
Name: "tamil"; MessagesFile: "compiler:Languages\Tamil.isl"
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "ukrainian"; MessagesFile: "compiler:Languages\Ukrainian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "D:\HeartrateReceiver\dist\main.dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "D:\HeartrateReceiver\dist\main.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; 注意：不要在任何共享系统文件上使用 "Flags: ignoreversion" 

[Registry]
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocExt}\OpenWithProgids"; ValueType: string; ValueName: "{#MyAppAssocKey}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}"; ValueType: string; ValueName: ""; ValueData: "{#MyAppAssocName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

