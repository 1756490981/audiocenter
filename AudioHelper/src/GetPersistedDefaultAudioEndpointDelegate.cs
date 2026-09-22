using System.Runtime.InteropServices;

namespace AudioHelper;

[UnmanagedFunctionPointer(CallingConvention.StdCall)]
internal delegate int GetPersistedDefaultAudioEndpointDelegate(nint self, uint processId, EDataFlow flow, ERole role, out nint deviceId);
