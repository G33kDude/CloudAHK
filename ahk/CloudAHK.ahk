#NoTrayIcon

;LogError(exception) {
;  static _ := OnError("LogError")
;  print("Exception Occurred: ", exception)
;  return true
;}

CloudAHK_FindImportEntry(forModuleName) {
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

CloudAHK_OverwriteImport(inModuleName, functionName, pReplacementFunction) {
	static PAGE_READWRITE := 0x4
	if !IsObject(entry := CloudAHK_FindImportEntry(inModuleName))
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

CloudAHK_MessageBoxW(HWND, pText, pCaption, Type) {
	static _ := CloudAHK_OverwriteImport("User32.dll", "MessageBoxW", RegisterCallback("CloudAHK_MessageBoxW"))
	Print(StrGet(pText))
	return 1
}

/*
#include <mcl.h>
#include <stdint.h>
#include <stdbool.h>
MCL_IMPORT(bool, Kernel32, WriteFile, (uintptr_t, void*, uint32_t, uint32_t*, void*));
uintptr_t hStdOut = 0;
MCL_EXPORT_GLOBAL(hStdOut);
bool shifted = 0;

MCL_EXPORT(keybd_event);
void keybd_event(uint8_t bVk, uint8_t bScan, uint32_t dwFlags, uintptr_t dwExtraInfo) {
  char* lower = "  1234567890-= \tqwertyuiop[]\n asdfghjkl;'` \\zxcvbnm,./    ";
  char* upper = "  !@#$%^&*()_+ \tQWERTYUIOP{}\n ASDFGHJKL:\"~ |ZXCVBNM<>?    ";
  if (bVk == 0xA0) { // VK_LSHIFT
    shifted = true;
  } else if (dwFlags == 2) { // Up
    shifted = false;
  } else if (dwFlags == 0) { // Down
    WriteFile(hStdOut, bScan <= 58 ? (shifted ? &upper[bScan] : &lower[bScan]) : &lower[0], 1, 0, 0);
  }
}
*/

CloudAHK_keybd_event_MCL() {
	static CodeBase64 := ""
. "bzEAAAAAAAAAAAAAAAAAAAAAVUiJ5UiD7ECJ0ESJRSBMiU0oicqIVRCIRRhIjQW/AAAASIlF+EiNBfQAAABIiUXwgH0QoHUJxgWTAAAAAettg30g"
. "AnUJxgWEAAAAAOteg30gAHVYTIsVZQAAAIB9GDp3JQ+2BWgAAACEwHQND7ZVGEiLRfBIAdDrEQ+2VRhIi0X4SAHQ6wRIi0X4SIsNX////0jHRCQg"
. "AAAAAEG5AAAAAEG4AQAAAEiJwkH/0pBIg8RAXcOQkJCQkJCQkJCQkJCQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgIDEyMzQ1Njc4"
. "OTAtPSAJcXdlcnR5dWlvcFtdCiBhc2RmZ2hqa2w7J2AgXHp4Y3Zibm0sLi8gICAgAAAAAAAAICAhQCMkJV4mKigpXysgCVFXRVJUWVVJT1B7fQog"
. "QVNERkdISktMOiJ+IHxaWENWQk5NPD4/ICAgIAAAAAAAAA=="
	static Code := false
	if ((A_PtrSize * 8) != 64) {
		Throw Exception("MyC does not support " (A_PtrSize * 8) " bit AHK, please run using 64 bit AHK")
	}
	; MCL standalone loader https://github.com/G33kDude/MCLib.ahk
	; Copyright (c) 2021 G33kDude, CloakerSmoker (CC-BY-4.0)
	; https://creativecommons.org/licenses/by/4.0/
	if (!Code) {
		CompressedSize := VarSetCapacity(DecompressionBuffer, 370, 0)
		if !DllCall("Crypt32\CryptStringToBinary", "Str", CodeBase64, "UInt", 0, "UInt", 1, "Ptr", &DecompressionBuffer, "UInt*", CompressedSize, "Ptr", 0, "Ptr", 0, "UInt")
			throw Exception("Failed to convert MCLib b64 to binary")
		if !(pCode := DllCall("GlobalAlloc", "UInt", 0, "Ptr", 368, "Ptr"))
			throw Exception("Failed to reserve MCLib memory")
		DecompressedSize := 0
		if (DllCall("ntdll\RtlDecompressBuffer", "UShort", 0x102, "Ptr", pCode, "UInt", 368, "Ptr", &DecompressionBuffer, "UInt", CompressedSize, "UInt*", DecompressedSize, "UInt"))
			throw Exception("Error calling RtlDecompressBuffer",, Format("0x{:08x}", r))
		for ImportName, ImportOffset in {"Kernel32$WriteFile": 208} {
			Import := StrSplit(ImportName, "$")
			hDll := DllCall("GetModuleHandle", "Str", Import[1], "Ptr")
			if (ErrorLevel || A_LastError)
				Throw "Could not load dll " Import[1] ", ErrorLevel " ErrorLevel ", LastError " Format("{:0x}", A_LastError)
			pFunction := DllCall("GetProcAddress", "Ptr", hDll, "AStr", Import[2], "Ptr")
			if (ErrorLevel || A_LastError)
				Throw "Could not find function " Import[2] " from " Import[1] ".dll, ErrorLevel " ErrorLevel ", LastError " Format("{:0x}", A_LastError)
			NumPut(pFunction, pCode + 0, ImportOffset, "Ptr")
		}
		OldProtect := 0
		if !DllCall("VirtualProtect", "Ptr", pCode, "Ptr", 368, "UInt", 0x40, "UInt*", OldProtect, "UInt")
			Throw Exception("Failed to mark MCLib memory as executable")
		Exports := {}
		for ExportName, ExportOffset in {"hStdOut": 0, "keybd_event": 16} {
			Exports[ExportName] := pCode + ExportOffset
		}
		Code := Exports
	}
	return Code
}

CloudAHK_keybd_event()
{
	static stdout, _ := CloudAHK_keybd_event()
	SetKeyDelay, -1

	stdout := FileOpen("*", "w")
	lib := CloudAHK_keybd_event_MCL()
	
	NumPut(stdOut.__Handle, lib.hStdOut, "UPtr")
	CloudAHK_OverwriteImport("USER32.DLL", "keybd_event", lib.keybd_event)
}

