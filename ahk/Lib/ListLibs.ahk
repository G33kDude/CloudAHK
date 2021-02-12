ListLibs() {
	print(StrSplit(Trim(stdouttovar("cmd /c dir /b Z:\ahk\lib"), "`r`n"), "`n", "`r"))
}
