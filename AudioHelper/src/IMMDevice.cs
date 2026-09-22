using System;
using System.Runtime.InteropServices;

namespace AudioHelper;

[ComImport]
[Guid("D666063F-1587-4E43-81F1-B948E807363F")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
internal interface IMMDevice
{
	int Activate(ref Guid iid, int clsCtx, nint activationParams, out nint pInterface);

	int OpenPropertyStore(int stgmAccess, out nint properties);

	int GetId(out nint id);

	int GetState(out int state);
}
