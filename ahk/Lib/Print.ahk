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
