using System.Runtime.InteropServices;

namespace AudioHelper;

[UnmanagedFunctionPointer(CallingConvention.StdCall)]
internal delegate int ClearAllPersistedApplicationDefaultEndpointsDelegate(nint self);
