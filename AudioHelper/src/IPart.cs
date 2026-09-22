using System;
using System.Runtime.InteropServices;

namespace AudioHelper;

[ComImport]
[Guid("AE2DE0E4-5BCA-4F2D-AA46-5D13F8FDB3A9")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
internal interface IPart
{
	int GetName(out nint name);

	int GetLocalId(out uint id);

	int GetGlobalId(out nint id);

	int GetPartType(out Guid type);

	int GetSubType(out Guid type);

	int GetControlInterfaceCount(out uint count);

	int GetControlInterface(uint index, out nint ctrl);

	int EnumPartsIncoming(out nint parts);

	int EnumPartsOutgoing(out nint parts);

	int GetTopologyObject(out nint topology);

	int Activate(int clsCtx, ref Guid iid, out nint obj);

	int RegisterControlChangeCallback(ref Guid iid, nint cb);

	int UnregisterControlChangeCallback(nint cb);
}
