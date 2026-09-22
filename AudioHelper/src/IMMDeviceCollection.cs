using System.Runtime.InteropServices;

namespace AudioHelper;

[ComImport]
[Guid("0BD7A1BE-7A1A-44DB-8397-CC5392387B5E")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
internal interface IMMDeviceCollection
{
	int GetCount(out int count);

	int Item(int index, out nint device);
}
