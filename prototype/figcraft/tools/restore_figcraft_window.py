"""Restore only the existing FigCraft control process window for UI verification."""
import ctypes,json,sys
target_pid=int(sys.argv[1]) if len(sys.argv)>1 else 3464
user32=ctypes.WinDLL('user32',use_last_error=True)
windows=[]
CALLBACK=ctypes.WINFUNCTYPE(ctypes.c_bool,ctypes.c_void_p,ctypes.c_void_p)
def collect(hwnd,unused):
    pid=ctypes.c_ulong()
    user32.GetWindowThreadProcessId(ctypes.c_void_p(hwnd),ctypes.byref(pid))
    if pid.value==target_pid and (user32.IsWindowVisible(ctypes.c_void_p(hwnd)) or user32.IsIconic(ctypes.c_void_p(hwnd))):windows.append(hwnd)
    return True
ok=user32.EnumWindows(CALLBACK(collect),0)
if not ok:raise RuntimeError('Desktop window enumeration unavailable')
results=[]
print(json.dumps({'matchingWindows':len(windows)}),flush=True)
for hwnd in windows:
    user32.ShowWindowAsync(ctypes.c_void_p(hwnd),9)
    flags=0x0001|0x0002|0x0040|0x4000
    raised=bool(user32.SetWindowPos(ctypes.c_void_p(hwnd),ctypes.c_void_p(-1),0,0,0,0,flags))
    user32.SetWindowPos(ctypes.c_void_p(hwnd),ctypes.c_void_p(-2),0,0,0,0,flags)
    results.append({'pid':target_pid,'restoreQueued':True,'raiseQueued':raised})
print(json.dumps({'matchingWindows':len(windows),'results':results}))
