

Print(p*)
{
	static stdout := FileOpen("*", "w", "utf-8")
	for k, v in p
		out .= "`t" (IsObject(v) ? Jxon_Dump(v) : v)
	stdout.Write(SubStr(out, 2) "`n")
	stdout.__Handle ; Flush write buffer
}

LogError(exception) {
  static _ := OnError("LogError")
  print("Exception Occurred: ", exception)
  return true
}

Print_FindImportEntry(forModuleName) {
	imageBase := DllCall("GetModuleHandle", "Ptr", 0, "Ptr")
	PEHeaderOffset := NumGet(imageBase + 0, 0x3C, "UInt")
	pImportTable := imageBase + NumGet(imageBase + PEHeaderOffset + 4 + 0x8C, 0, "UInt")
	while( (lookupTableRVA := NumGet(pImportTable + 0, "UInt"))
		&& (nameRVA := NumGet(pImportTable + 12, "UInt"))
		&& (thunkTableRVA := NumGet(pImportTable + 16, "UInt")) ) {
		if (StrGet(imageBase + nameRVA, "UTF-8") = forModuleName)
			return {"imageBase": imageBase, "lookupTable": imageBase + lookupTableRVA, "thunkTable": imageBase + thunkTableRVA}
		pImportTable += 20
	}
}

Print_OverwriteImport(inModuleName, functionName, pReplacementFunction) {
	static PAGE_READWRITE := 0x4
	if !IsObject(entry := Print_FindImportEntry(inModuleName))
		return
	loop {
		thunkIndex := A_Index - 1
		nextLookupValue := NumGet(entry.lookupTable + thunkIndex * 8, "UInt64")
		if (nextLookupValue < 0)
			continue
		hintNameName := StrGet(entry.imageBase + nextLookupValue + 2, "UTF-8")
	} until (hintNameName = functionName)
	if !ThunkIndex
		return
	pTargetThunk := entry.thunkTable + thunkIndex * 8
	DllCall("VirtualProtect", "Ptr", pTargetThunk, "UInt", 8, "UInt", PAGE_READWRITE, "UInt*", OldProtect)
	NumPut(pReplacementFunction, pTargetThunk + 0, "Ptr")
}

Print_MessageBoxW(HWND, pText, pCaption, Type) {
	static _ := Print_OverwriteImport("User32.dll", "MessageBoxW", RegisterCallback("Print_MessageBoxW"))
	Print(StrGet(pText))
	return 1
}

#Include mcode.ahk

Print_keybd_event()
{
	static pfn, _ := Print_keybd_event()
	SetKeyDelay, -1

	; Written in Relax by @CloakerSmoker
	R := "2,x64:6UYEAAAAAAAAAABAAAAAAAAAAAAAAAAAICAgICAgICAgCSAgICAgICAgICteISAgICAgICAgICAgICAgICAgICAgICAgICAgMDEyMzQ1Njc4OSAgICAgICBhYmNkZWZnaGlqa2xtbm9wcXJzdHV2d3h5egAgICAgICAgICAJICAgICAgICAgK14hICAgICAgICAgICAgICAgICAgICAgICAgICApIUAjJCVeJiooICAgICAgIEFCQ0RFRkdISUpLTE1OT1BRUlNUVVZXWFlaAFtcXScAe3x9IgA7OgA9KwAsPgAtXwAuPAAvPwBgfgBVSIvsSIPsYGaJTfhAiFXwRIlF6EyJTeCLRehBuQIAAABEIciFwA+ECAAAADHASA++wMnDjQXv/v//SIlF2I0FQf///0iJRdBAsFtID77AiUXIjQWJ////SIlFwI0FhP///0iJRbhmuNsASA+/wIlFsGa43gBID7/AiUWoZotF+EG5EAAAAGZEOcgPlMBmRItN+EG6oAAAAGZFOdFBD5TBQQLBQAjAD5XAZkSLTfhBuqEAAABmRTnRQQ+UwUECwUAIwA+EDwAAAECwAUCIBU/+///pXgIAAGaLRfhBuQ0AAABmRDnID4UNAAAAQLcN6EQCAADpNAIAAGaLRfhBuboAAABmRDnID4UfAAAAjT3Z/v//RIodCP7//00PvttCijwf6BECAADpAQIAAGaLRfhBubsAAABmRDnID4UfAAAAjT2p/v//RIod1f3//00PvttCijwf6N4BAADpzgEAAGaLRfhBubwAAABmRDnID4UfAAAAjT15/v//RIodov3//00PvttCijwf6KsBAADpmwEAAGaLRfhBub0AAABmRDnID4UfAAAAjT1J/v//RIodb/3//00PvttCijwf6HgBAADpaAEAAGaLRfhBub4AAABmRDnID4UfAAAAjT0Z/v//RIodPP3//00PvttCijwf6EUBAADpNQEAAGaLRfhBub8AAABmRDnID4UfAAAAjT3p/f//RIodCf3//00PvttCijwf6BIBAADpAgEAAGaLRfhBucAAAABmRDnID4UfAAAAjT25/f//RIod1vz//00PvttCijwf6N8AAADpzwAAAGaLRfhEi03IZkQ5yA+MfAAAAGaLRfhEi1WwZkQ50A+dwGZEi1X4RItdqGZFOdpBD57CZkEPr8JACMAPhEkAAABmi0X4SA+/wESLXbBBK8OJRaBAigVr/P//QITAD4QWAAAASIt9uESLXaBCijwf6GcAAADpEQAAAEiLfcBEi12gQoo8H+hRAAAA6UEAAABAigUv/P//QITAD4QbAAAASIt90GZEi134TQ+/20KKPB/oJgAAAOkWAAAASIt92GZEi134TQ+/20KKPB/oCwAAADHAQIgF7Pv//8nDVUiL7EiD7BBAiH34ugEAAABIjXX4QLcBSA++/7gBAAAADwXJw+mf/P//"

	Print_OverwriteImport("USER32.DLL", "keybd_event", MCode(R))
}

