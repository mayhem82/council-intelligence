# Checking Your PowerShell Version

If you have this repository checked out on Windows and want to read this file from a PowerShell session, open it with a command such as `notepad .\docs\powershell-version.md` or `Get-Content .\docs\powershell-version.md`. Entering the file path by itself tries to run it as a command, which results in a “not recognized” error.

To confirm you are running PowerShell rather than Command Prompt, check that the shell prompt begins with `PS`. Once you have a PowerShell session, run the following command to view the current version information:

```powershell
$PSVersionTable.PSVersion
```

The output lists the Major, Minor, Build, and Revision numbers. If you see an error indicating the command is not recognized, you are likely in Command Prompt (`cmd.exe`) instead of PowerShell. Open PowerShell through the Start menu, Run dialog (`Win + R`), or Windows Terminal, then rerun the command.

For tasks that require administrative privileges—such as registering scheduled tasks—launch PowerShell as an administrator by right-clicking its shortcut and choosing **Run as administrator**.
