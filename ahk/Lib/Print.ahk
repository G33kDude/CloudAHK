Print(p*)
{
	static stdout := FileOpen("*", "w")
	for k, v in p
		out .= "`t" (IsObject(v) ? Jxon_Dump(v) : v)
	stdout.Write(SubStr(out, 2) "`n")
}
