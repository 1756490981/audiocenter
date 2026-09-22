using System.Runtime.InteropServices;

namespace AudioHelper;

[ComImport]
[Guid("2A07407E-6497-4A18-9787-32F79BD0D98F")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
internal interface IDeviceTopology
{
	int GetConnectorCount(out uint count);

	int GetConnector(uint index, out nint connector);

	int GetSubunitCount(out uint count);

	int GetSubunit(uint index, out nint subunit);

	int GetPartById(uint id, out nint part);

	int GetDeviceId(out nint id);

	int GetSignalPath([In] nint from, [In] nint to, [MarshalAs(UnmanagedType.Bool)] bool rejectMixedPaths, out nint parts);
}
