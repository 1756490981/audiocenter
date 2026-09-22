using System.Runtime.InteropServices;

namespace AudioHelper;

[UnmanagedFunctionPointer(CallingConvention.StdCall)]
internal delegate int SetPersistedDefaultAudioEndpointDelegate(nint self, uint processId, EDataFlow flow, ERole role, nint deviceId);
