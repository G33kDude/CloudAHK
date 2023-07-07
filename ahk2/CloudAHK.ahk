#Warn VarUnset, StdOut
#Warn Unreachable, StdOut
OnError CloudAHK_Error, -1

MsgBox(Text := "Press OK to continue.", *) {
  try {
    FileAppend(String(Text) "`n", "*", "UTF-8")
  } catch MethodError as e {
    x := Error("", -1)
    e.File := x.File, e.Line := x.Line, e.Stack := x.Stack
    throw e
  }
}

CloudAHK_Error(err, mode) {
  out := ""
  for i, line in _ScriptGetLines(err.File, err.Line, 2)
  {
    if (line.File != err.File)
      continue

    out .= Format("{}{:03}: {}`n",
      line.Number == err.Line ? "> " : "  ",
      line.Number,
      StrReplace(
        StrReplace(
          RegExReplace(line.Text, "s)^.{30}\K.+", "..."),
          "`n"
          "``n"
        ),
        "`r",
        "``r"
      )
    )
  }

MsgBox Format("
    (LTrim
    {}: {}
    
    {}Line: {}
    What: {}
    
    {}
    {}
    )",
    type(err),
    err.Message,
    err.File == "*" ? "" : "File: " err.File "`n",
    err.Line,
    err.What,
    out,
    (mode == "ExitApp" ? "Script" : "Thread") " will " (mode == "Return" ? "continue" : "exit")
  )

  return -1
}
