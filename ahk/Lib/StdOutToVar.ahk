StdOutToVar( sCmd ) { ;  GAHK32 ; Modified Version : SKAN 05-Jul-2013  http://goo.gl/j8XJXY                             
  Static StrGet := "StrGet"     ; Original Author  : Sean 20-Feb-2007  http://goo.gl/mxCdn  
   
  DllCall( "CreatePipe", UIntP,hPipeRead, UIntP,hPipeWrite, UInt,0, UInt,0 )
  DllCall( "SetHandleInformation", UInt,hPipeWrite, UInt,1, UInt,1 )

  if(a_ptrSize=8){
    VarSetCapacity( STARTUPINFO, 104, 0  )      ; STARTUPINFO          ;  http://goo.gl/fZf24
    NumPut( 68,         STARTUPINFO,  0 )      ; cbSize
    NumPut( 0x100,      STARTUPINFO, 60 )      ; dwFlags    =>  STARTF_USESTDHANDLES = 0x100 
    NumPut( hPipeWrite, STARTUPINFO, 88 )      ; hStdOutput
    NumPut( hPipeWrite, STARTUPINFO, 96 )      ; hStdError
    VarSetCapacity( PROCESS_INFORMATION, 32 )  ; PROCESS_INFORMATION  ;  http://goo.gl/b9BaI      
  }else{
    VarSetCapacity( STARTUPINFO, 68, 0  )      ; STARTUPINFO          ;  http://goo.gl/fZf24
    NumPut( 68,         STARTUPINFO,  0 )      ; cbSize
    NumPut( 0x100,      STARTUPINFO, 44 )      ; dwFlags    =>  STARTF_USESTDHANDLES = 0x100 
    NumPut( hPipeWrite, STARTUPINFO, 60 )      ; hStdOutput
    NumPut( hPipeWrite, STARTUPINFO, 64 )      ; hStdError
    VarSetCapacity( PROCESS_INFORMATION, 16 )  ; PROCESS_INFORMATION  ;  http://goo.gl/b9BaI      
  }
  If ! DllCall( "CreateProcess", UInt,0, UInt,&sCmd, UInt,0, UInt,0 ;  http://goo.gl/USC5a
              , UInt,1, UInt,0x08000000, UInt,0, UInt,0
              , UInt,&STARTUPINFO, UInt,&PROCESS_INFORMATION ) 
   Return "" 
   , DllCall( "CloseHandle", UInt,hPipeWrite ) 
   , DllCall( "CloseHandle", UInt,hPipeRead )
   , DllCall( "SetLastError", Int,-1 )     

  hProcess := NumGet( PROCESS_INFORMATION, 0 )                 
  if(a_is64bitOS)
    hThread  := NumGet( PROCESS_INFORMATION, 8 )                      
  else
    hThread  := NumGet( PROCESS_INFORMATION, 4 ) 

  DllCall( "CloseHandle", UInt,hPipeWrite )

  AIC := ( SubStr( A_AhkVersion, 1, 3 ) = "1.0" )                   ;  A_IsClassic 
  VarSetCapacity( Buffer, 4096, 0 ), nSz := 0 
  
  While DllCall( "ReadFile", UInt,hPipeRead, UInt,&Buffer, UInt,4094, UIntP,nSz, UInt,0 )
   sOutput .= ( AIC && NumPut( 0, Buffer, nSz, "UChar" ) && VarSetCapacity( Buffer,-1 ) ) 
              ? Buffer : %StrGet%( &Buffer, nSz, "CP850" )
 
  DllCall( "GetExitCodeProcess", UInt,hProcess, UIntP,ExitCode )
  DllCall( "CloseHandle", UInt,hProcess  )
  DllCall( "CloseHandle", UInt,hThread   )
  DllCall( "CloseHandle", UInt,hPipeRead )

Return sOutput,  DllCall( "SetLastError", UInt,ExitCode )
}

/* minimized 64-bit
sv(c){
u:="UInt",l:="UIntP",k:="CloseHandle",z:="DllCall",y:="NumGet",x:="NumPut",q:="VarSetCapacity",%z%("CreatePipe",l,p,l,w,u,0,u,0),%z%("SetHandleInformation",u,w,u,1,u,1),%q%(s,104,0),%x%(68,s,0),%x%(0x100,s,60),%x%(w,s,88),%x%(w,s,96),%q%(i,32)
If !%z%("CreateProcess",u,0,u,&c,u,0,u,0,u,1,u,0x08000000,u,0,u,0,u,&s,u,&i)
Return "",%z%(k,u,w),%z%(k,u,p),%z%("SetLastError",Int,-1)
g:=%y%(i,0),h:=%y%(i,8),%z%(k,u,w),a:=(SubStr(A_AhkVersion,1,3)="1.0"),%q%(b,4096,0),n:=0
While %z%("ReadFile",u,p,u,&b,u,4094,l,n,u,0)
o.=(a&&%x%(0,b,n,"UChar")&&%q%(b,-1))?b:StrGet(&b,n,"CP850")
%z%("GetExitCodeProcess",u,g,l,e),%z%(k,u,g),%z%(k,u,h),%z%(k,u,p)
Return o,%z%("SetLastError",u,e)
}
*/